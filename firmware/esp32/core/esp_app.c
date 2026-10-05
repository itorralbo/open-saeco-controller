/* SPDX-License-Identifier: MIT */
#include "esp_app.h"
#include <string.h>
#include "board_pins.h"
#include "esp_hal.h"

static osc_esp_view v;
static osc_parser parser;
static uint8_t seq;
static uint32_t last_status, last_keepalive, front_t, valid_at;

static void send(uint8_t type, const uint8_t *payload, uint8_t len) {
    osc_frame f;
    uint8_t buf[OSC_PROTO_MAX_FRAME];
    f.type = type;
    f.seq = seq++;
    f.len = len;
    if (len) memcpy(f.payload, payload, len);
    esp_hal_uart_write(buf, osc_proto_encode(&f, buf));
    if (type != OSC_MSG_KEEPALIVE) v.requests++;
}

/* Every front-panel line back to high impedance: with 3V3_UI off a driven
 * high would feed the panel through its pull-ups and protection diodes. */
static void front_release(void) {
    esp_hal_i2c_deinit();
    esp_hal_spi_deinit();
    esp_hal_gpio_mode(BOARD_LCD_BL_GPIO, ESP_GPIO_OFF);
    esp_hal_gpio_mode(BOARD_LCD_DC_GPIO, ESP_GPIO_OFF);
    esp_hal_gpio_mode(BOARD_LCD_RST_N_GPIO, ESP_GPIO_OFF);
    disp_stop(&v.display);
    v.keypad.valid = false;
}

static void front_bring_up(uint32_t now) {
    esp_hal_i2c_init(BOARD_KEY_SDA_GPIO, BOARD_KEY_SCL_GPIO, 100000u);
    esp_hal_spi_init(BOARD_LCD_SCLK_GPIO, BOARD_LCD_MOSI_GPIO, BOARD_LCD_CS_N_GPIO, DISP_SPI_HZ);
    fp_init(&v.keypad, now);
    disp_start(&v.display, now);
    v.front = ESP_FRONT_ON;
    valid_at = now;
}

static void handle(const osc_frame *f, uint32_t now) {
    if (f->type == OSC_MSG_STATUS) {
        if (osc_status_unpack(f->payload, f->len, &v.status)) {
            v.have_status = true;
            last_status = now;
        }
    } else if ((f->type == OSC_MSG_ACK || f->type == OSC_MSG_ERROR) && f->len >= 1) {
        v.replies++;
        v.last_reply_type = f->type;
        v.last_reply_for = f->payload[0];
        v.last_reply_code = f->type == OSC_MSG_ERROR && f->len >= 2 ? f->payload[1] : 0u;
    }
}

static void keys(uint8_t presses) {
    static const uint8_t recipe = 1;
    if (presses & ESP_KEY_STANDBY) {
        v.standby = !v.standby;
        fp_set_led(&v.keypad, v.standby);
    }
    if (!v.link_ok) return; /* nothing to ask without a link */
    if (presses & ESP_KEY_STOP) send(OSC_MSG_STOP, 0, 0);
    if (presses & ESP_KEY_START) send(OSC_MSG_START_RECIPE, &recipe, 1);
    if (presses & ESP_KEY_CLEAR_FAULT) send(OSC_MSG_CLEAR_FAULT, 0, 0);
}

static void front(uint32_t now) {
    const bool ui_power = (v.status.inputs & OSC_IN_UI_POWER) != 0;
    static const uint8_t off = 0, on = 1;
    switch (v.front) {
    case ESP_FRONT_WAIT:
        if (v.link_ok && ui_power) front_bring_up(now);
        break;
    case ESP_FRONT_ON:
        if (v.link_ok && !ui_power) {
            front_release();
            v.front = ESP_FRONT_WAIT;
            break;
        }
        fp_poll(&v.keypad, now, !esp_hal_gpio_read(BOARD_KEY_INT_N_GPIO));
        if (v.keypad.valid) {
            valid_at = now;
        } else if (v.link_ok && now - valid_at >= ESP_FRONT_RECOVERY_MS) {
            /* A keypad that will not answer gets a clean power cycle. */
            front_release();
            send(OSC_MSG_UI_POWER, &off, 1);
            v.front = ESP_FRONT_POWER_OFF;
            v.recoveries++;
            front_t = now;
            break;
        }
        keys(fp_take_presses(&v.keypad));
        disp_poll(&v.display, now);
        break;
    case ESP_FRONT_POWER_OFF:
        if (v.link_ok && !ui_power && now - front_t >= ESP_FRONT_OFF_MS) {
            send(OSC_MSG_UI_POWER, &on, 1);
            v.front = ESP_FRONT_POWER_ON;
            front_t = now;
        } else if (now - front_t >= 1000u) {
            send(OSC_MSG_UI_POWER, &off, 1);
            front_t = now;
        }
        break;
    case ESP_FRONT_POWER_ON:
        if (v.link_ok && ui_power) front_bring_up(now);
        else if (now - front_t >= 1000u) {
            send(OSC_MSG_UI_POWER, &on, 1);
            front_t = now;
        }
        break;
    }
}

static void screen(void) {
    static const uint16_t bg[] = {DISP_BLACK, DISP_GREY, DISP_BLUE, DISP_GREEN, DISP_RED, DISP_BLACK};
    uint16_t bar = DISP_BLACK;
    if (!v.have_status) v.screen = ESP_SCREEN_BOOT;
    else if (!v.link_ok) v.screen = ESP_SCREEN_LINK_LOST;
    else if (v.standby) v.screen = ESP_SCREEN_STANDBY;
    else if (v.status.state == OSC_CORE_FAULT) v.screen = ESP_SCREEN_FAULT;
    else if (v.status.state == OSC_CORE_SAFE_IDLE) v.screen = ESP_SCREEN_IDLE;
    else v.screen = ESP_SCREEN_STARTING;
    /* A refused START is a normal answer, shown in amber, not a link error. */
    if (v.last_reply_type == OSC_MSG_ACK) bar = DISP_GREEN;
    else if (v.last_reply_type == OSC_MSG_ERROR) bar = DISP_AMBER;
    disp_show(&v.display, bg[v.screen], bar);
    disp_backlight(&v.display, v.screen != ESP_SCREEN_STANDBY);
}

void esp_app_init(void) {
    static const uint8_t hello[2] = {OSC_PROTO_VERSION, 1u /* role: interface */};
    const uint32_t now = esp_hal_millis();
    memset(&v, 0, sizeof v);
    osc_parser_init(&parser);
    seq = 0;
    last_status = last_keepalive = front_t = valid_at = now;
    esp_hal_uart_init(BOARD_UART_TX_GPIO, BOARD_UART_RX_GPIO, OSC_PROTO_BAUD);
    esp_hal_gpio_mode(BOARD_KEY_INT_N_GPIO, ESP_GPIO_INPUT);
    v.front = ESP_FRONT_WAIT;
    send(OSC_MSG_HELLO, hello, 2);
}

void esp_app_poll(void) {
    const uint32_t now = esp_hal_millis();
    uint8_t byte;
    osc_frame f;
    while (esp_hal_uart_read(&byte))
        if (osc_parser_feed(&parser, byte, &f)) handle(&f, now);
    v.link_ok = v.have_status && now - last_status < OSC_PROTO_LINK_TIMEOUT_MS;
    if (now - last_keepalive >= OSC_PROTO_KEEPALIVE_PERIOD_MS) {
        last_keepalive = now;
        send(OSC_MSG_KEEPALIVE, 0, 0);
    }
    front(now);
    screen();
}

const osc_esp_view *esp_app_view(void) { return &v; }
