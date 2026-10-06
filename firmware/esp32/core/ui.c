/* SPDX-License-Identifier: MIT */
#include "ui.h"
#include <stdio.h>
#include <string.h>
#include "font5x7.h"

/* How a test value is shown. */
enum { F_NONE, F_YESNO, F_RAW, F_MS, F_S, F_MA, F_DC, F_MV, F_ML10, F_MLPS, F_RATE, F_COUNT, F_GRIND };

typedef struct {
    const char *label;
    uint8_t fmt;
} val_fmt;

typedef struct {
    const char *name;
    const char *desc[5];
    const char *param_label; /* NULL: no parameter */
    const char *param_unit;
    uint16_t def, min, max, step;
    val_fmt v[OSC_TEST_VALUES];
} test_info;

static const test_info tests[OSC_TEST_COUNT] = {
    {"", {0}, 0, 0, 0, 0, 0, 0, {{0, F_NONE}}},
    {"Entradas y sensores",
     {"Lee puerta, micros, agua,", "caldera y 24 V 3 s.", "Abra y cierre la puerta", "para probar el contacto.", "(SW-02/03, WL-01)"},
     0, 0, 0, 0, 0, 0,
     {{"Puerta cerrada", F_YESNO}, {"Grupo presente", F_YESNO}, {"Grupo en trabajo", F_YESNO},
      {"Agua (ADC)", F_RAW}, {"Caldera", F_DC}, {"24 V", F_MV}}},
    {"Grupo: ciclo",
     {"Lleva el grupo a trabajo", "y lo devuelve. Mide I0,", "pico de arranque y tiempo.", "Puerta cerrada y grupo.", "(BU-03/04/06)"},
     0, 0, 0, 0, 0, 0,
     {{"Hasta trabajo", F_MS}, {"I0", F_MA}, {"Pico arranque", F_MA}, {"I en el tope", F_MA},
      {"Vuelta", F_MS}, {"Fallos driver", F_COUNT}}},
    {"Electrovalvula",
     {"Activa la valvula 2 s.", "Mida la corriente con la", "pinza en JP3. La placa", "mide la caida del rail.",
      "(VA-02)"},
     0, 0, 0, 0, 0, 0,
     {{"24 V antes", F_MV}, {"24 V activa", F_MV}, {"Tiempo", F_MS}, {0, F_NONE}, {0, F_NONE}, {0, F_NONE}}},
    {"Rele general",
     {"Cierra K701 1 s sin carga.", "Debe oirse el rele.", 0, 0, 0},
     0, 0, 0, 0, 0, 0,
     {{"24 V antes", F_MV}, {"24 V activa", F_MV}, {"Tiempo", F_MS}, {0, F_NONE}, {0, F_NONE}, {0, F_NONE}}},
    {"Bomba y caudal",
     {"Bombea el volumen por", "pulsos, 30 s como mucho.", "Deposito lleno, recipiente", "bajo la salida. Pese agua.", "(PU-04, FL-01)"},
     "Volumen", "ml", 100, 10, 500, 10,
     {{"Tiempo", F_MS}, {"Pulsos", F_COUNT}, {"Volumen nominal", F_ML10}, {"Caudal", F_MLPS},
      {"Caldera inicio", F_DC}, {"Caldera fin", F_DC}}},
    {"Calentador",
     {"Calienta a la consigna,", "60 s como mucho, y mide", "15 s la sobreoscilacion.", "SOLO con la caldera llena:", "cebe antes con la bomba."},
     "Consigna", FONT_DEGREE "C", 90, 40, 105, 5,
     {{"Inicio", F_DC}, {"Fin calentar", F_DC}, {"Tiempo", F_S}, {"Ritmo", F_RATE}, {"Pico", F_DC},
      {"Sobreoscilacion", F_DC}}},
    {"Molinillo",
     {"Muele el tiempo indicado", "y mide la corriente: para", "si falta grano o se atasca", "Tolva con grano.", "(GR-02/03/04/08)"},
     "Tiempo", "ms", 3000, 500, 10000, 500,
     {{"Tiempo", F_MS}, {"Pico arranque", F_MA}, {"I moliendo", F_MA}, {"I final", F_MA},
      {"Cero sensor", F_MA}, {"24 V", F_MV}}},
    {"Dosis: moler y prensar",
     {"Muele y prensa la dosis", "con el grupo; avisa si no", "llega cafe a la camara.", "Sin agua. Tolva con grano.", "(BU-05)"},
     "Molido", "ms", 6000, 500, 10000, 500,
     {{"Molido", F_MS}, {"I molinillo", F_MA}, {"Molinillo", F_GRIND}, {"I0 grupo", F_MA},
      {"Subida al prensar", F_MA}, {"Dosis", F_YESNO}}},
};

/* Shown after "Motivo: " on one 26-character line: 18 characters at most. */
static const char *const reasons[] = {
    "", "puerta abierta", "control ocupado", "tiempo agotado", "fallo del driver", "parada",
    "enlace perdido", "NTC abierto/corto", "limite temperatura", "grupo ausente", "sin caudal",
    "parametro", "prueba desconocida", "sin cafe en tolva", "molino atascado", "camara sin cafe"};

static const char *const menu_items[] = {"Preparar cafe", "Puesta a punto", "Informacion", "Borrar fallo",
                                        "Volver"};
#define MENU_N 5u
#define SETUP_N ((unsigned)OSC_TEST_COUNT) /* tests 1..N-1, then Volver */

const char *ui_test_name(uint8_t id) { return id < OSC_TEST_COUNT ? tests[id].name : "?"; }

void ui_init(osc_ui *u) {
    memset(u, 0, sizeof *u);
    u->page = UI_HOME;
}

static void ask(ui_request *req, uint8_t type, const uint8_t *p, uint8_t len) {
    req->type = type;
    req->len = len;
    if (len) memcpy(req->payload, p, len);
}

static bool fault(const ui_ctx *c) { return c->have_status && c->status->state == OSC_CORE_FAULT; }

static void move(uint8_t *sel, unsigned n, uint8_t presses) {
    if (presses & UI_KEY_UP) *sel = (uint8_t)((*sel + n - 1u) % n);
    if (presses & UI_KEY_DOWN) *sel = (uint8_t)((*sel + 1u) % n);
}

bool ui_keys(osc_ui *u, uint8_t k, const ui_ctx *c, ui_request *req) {
    static const uint8_t recipe = 1;
    uint8_t p[3];
    req->type = 0;
    if (!k) return false;
    if (u->standby) {
        /* Any key wakes the screen without doing anything else. */
        u->standby = false;
        return false;
    }
    if (k & UI_KEY_STBY) {
        u->standby = true;
        return false;
    }
    if (!c->link_ok) return false;
    if (k & UI_KEY_STOP) {
        ask(req, OSC_MSG_STOP, 0, 0);
        return true;
    }
    switch ((ui_page)u->page) {
    case UI_HOME:
        if (k & UI_KEY_MENU) {
            u->page = UI_MENU;
            u->sel = 0;
        } else if (k & UI_KEY_OK) {
            if (fault(c)) ask(req, OSC_MSG_CLEAR_FAULT, 0, 0);
            else ask(req, OSC_MSG_START_RECIPE, &recipe, 1);
        }
        break;
    case UI_MENU:
        move(&u->sel, MENU_N, k);
        if (k & (UI_KEY_BACK | UI_KEY_MENU)) u->page = UI_HOME;
        else if (k & UI_KEY_OK) {
            switch (u->sel) {
            case 0: ask(req, OSC_MSG_START_RECIPE, &recipe, 1); u->page = UI_HOME; break;
            case 1: u->page = UI_SETUP; u->sel = 0; break;
            case 2: u->page = UI_INFO; break;
            case 3: ask(req, OSC_MSG_CLEAR_FAULT, 0, 0); u->page = UI_HOME; break;
            default: u->page = UI_HOME; break;
            }
        }
        break;
    case UI_SETUP:
        move(&u->sel, SETUP_N, k);
        if (k & UI_KEY_BACK) {
            u->page = UI_MENU;
            u->sel = 1;
        } else if (k & UI_KEY_OK) {
            if (u->sel + 1u >= SETUP_N) {
                u->page = UI_MENU;
                u->sel = 1;
            } else {
                u->test = (uint8_t)(u->sel + 1u);
                u->param = tests[u->test].def;
                u->page = UI_CONFIRM;
            }
        }
        break;
    case UI_CONFIRM: {
        const test_info *t = &tests[u->test];
        if (t->param_label) {
            if ((k & UI_KEY_UP) && u->param + t->step <= t->max) u->param = (uint16_t)(u->param + t->step);
            if ((k & UI_KEY_DOWN) && u->param >= t->min + t->step) u->param = (uint16_t)(u->param - t->step);
        }
        if (k & UI_KEY_BACK) u->page = UI_SETUP;
        else if (k & UI_KEY_OK) {
            p[0] = u->test;
            p[1] = (uint8_t)(u->param & 0xFFu);
            p[2] = (uint8_t)(u->param >> 8);
            ask(req, OSC_MSG_TEST, p, 3);
            u->page = UI_TEST;
        }
        break;
    }
    case UI_TEST: {
        const bool mine = c->have_report && c->report->id == u->test;
        const bool running = mine && c->report->phase == OSC_TEST_RUNNING;
        if (k & UI_KEY_BACK) {
            if (running) {
                ask(req, OSC_MSG_STOP, 0, 0);
            } else {
                p[0] = OSC_TEST_NONE;
                ask(req, OSC_MSG_TEST, p, 1);
                u->page = UI_SETUP;
            }
        } else if ((k & UI_KEY_OK) && mine && c->report->phase == OSC_TEST_DONE && u->test == OSC_TEST_PUMP) {
            u->entry_ml = (uint16_t)((c->report->value[2] + 5) / 10);
            u->page = UI_ENTRY;
        }
        break;
    }
    case UI_ENTRY:
        if ((k & UI_KEY_UP) && u->entry_ml < 1000u) u->entry_ml++;
        if ((k & UI_KEY_DOWN) && u->entry_ml > 1u) u->entry_ml--;
        if ((k & UI_KEY_OK) && c->have_report && u->entry_ml)
            u->flow_ppl = (int32_t)((int64_t)c->report->value[1] * 1000 / u->entry_ml);
        if (k & UI_KEY_BACK) u->page = UI_TEST;
        break;
    case UI_INFO:
        if (k & (UI_KEY_BACK | UI_KEY_OK)) {
            u->page = UI_MENU;
            u->sel = 2;
        }
        break;
    }
    return req->type != 0;
}

static void fmt_value(char *out, size_t n, uint8_t fmt, int32_t v) {
    switch (fmt) {
    case F_YESNO: snprintf(out, n, "%s", v ? "si" : "no"); break;
    case F_GRIND: snprintf(out, n, "%s", v == 2 ? "atasco" : v == 1 ? "sin grano" : "ok"); break;
    case F_MS: snprintf(out, n, "%ld ms", (long)v); break;
    case F_S: snprintf(out, n, "%ld.%01ld s", (long)(v / 1000), (long)((v % 1000) / 100)); break;
    case F_MA: snprintf(out, n, "%ld mA", (long)v); break;
    case F_DC:
        if (v == -32768) snprintf(out, n, "---");
        else snprintf(out, n, "%s%ld.%01ld " FONT_DEGREE "C", v < 0 ? "-" : "", (long)(v < 0 ? -v : v) / 10,
                      (long)(v < 0 ? -v : v) % 10);
        break;
    case F_MV: snprintf(out, n, "%ld.%02ld V", (long)(v / 1000), (long)((v % 1000) / 10)); break;
    case F_ML10: snprintf(out, n, "%ld.%01ld ml", (long)(v / 10), (long)(v % 10)); break;
    case F_MLPS: snprintf(out, n, "%ld.%02ld ml/s", (long)(v / 100), (long)(v % 100)); break;
    case F_RATE: snprintf(out, n, "%ld.%02ld " FONT_DEGREE "C/s", (long)(v / 100), (long)((v < 0 ? -v : v) % 100)); break;
    default: snprintf(out, n, "%ld", (long)v); break;
    }
}

static void pair(char *line, const char *label, const char *value) {
    /* Label left, value right-aligned in TXT_COLS columns. */
    const size_t ll = strlen(label), lv = strlen(value);
    size_t i;
    memset(line, ' ', TXT_COLS);
    line[TXT_COLS] = '\0';
    for (i = 0; i < ll && i < TXT_COLS; ++i) line[i] = label[i];
    for (i = 0; i < lv && i < TXT_COLS; ++i) line[TXT_COLS - lv + i] = value[i];
}

static uint16_t title_colour(const ui_ctx *c) {
    if (!c->link_ok) return DISP_GREY;
    switch (c->status->state) {
    case OSC_CORE_SAFE_IDLE: return DISP_GREEN;
    case OSC_CORE_FAULT: return DISP_RED;
    case OSC_CORE_SERVICE: return DISP_AMBER;
    default: return DISP_BLUE;
    }
}

static const char *state_name(uint8_t s) {
    switch (s) {
    case OSC_CORE_BOOT: return "arrancando";
    case OSC_CORE_SAFE_IDLE: return "en reposo";
    case OSC_CORE_FAULT: return "FALLO";
    case OSC_CORE_SERVICE: return "prueba";
    default: return "?";
    }
}

static void render_test(const osc_ui *u, const ui_ctx *c, osc_text_screen *s) {
    const test_info *t = &tests[u->test];
    const osc_test_report *r = c->report;
    const bool mine = c->have_report && r->id == u->test;
    char a[TXT_COLS + 1], b[TXT_COLS + 1], line[TXT_COLS + 1];
    unsigned i, row = 2;
    if (!mine) {
        txt_line(s, 0, TXT_DIM, "Esperando al control...");
    } else {
        switch (r->phase) {
        case OSC_TEST_RUNNING: snprintf(a, sizeof a, "En curso, paso %u", (unsigned)r->step); break;
        case OSC_TEST_DONE: snprintf(a, sizeof a, "Terminada"); break;
        case OSC_TEST_ABORTED: snprintf(a, sizeof a, "Abortada"); break;
        case OSC_TEST_REFUSED: snprintf(a, sizeof a, "Rechazada"); break;
        default: snprintf(a, sizeof a, "-"); break;
        }
        txt_line(s, 0, r->phase == OSC_TEST_DONE ? TXT_OK : r->phase == OSC_TEST_RUNNING ? TXT_WARN : TXT_BAD, a);
        if (r->reason && r->reason < sizeof reasons / sizeof reasons[0]) {
            snprintf(a, sizeof a, "Motivo: %s", reasons[r->reason]);
            txt_line(s, 1, TXT_BAD, a);
        } else {
            fmt_value(b, sizeof b, F_S, (int32_t)r->elapsed_ms);
            pair(line, "Transcurrido", b);
            txt_line(s, 1, TXT_DIM, line);
        }
        for (i = 0; i < OSC_TEST_VALUES && r->phase != OSC_TEST_REFUSED; ++i) {
            if (!t->v[i].label) continue;
            fmt_value(b, sizeof b, t->v[i].fmt, r->value[i]);
            pair(line, t->v[i].label, b);
            txt_line(s, row++, TXT_NORMAL, line);
        }
        if (u->flow_ppl && u->test == OSC_TEST_PUMP) {
            snprintf(b, sizeof b, "%ld p/l", (long)u->flow_ppl);
            pair(line, "Calibracion", b);
            txt_line(s, row++, TXT_OK, line);
        }
    }
    if (mine && r->phase == OSC_TEST_RUNNING) txt_foot(s, "STOP/" FONT_LEFT ": parar");
    else if (u->test == OSC_TEST_PUMP && mine && r->phase == OSC_TEST_DONE)
        txt_foot(s, "OK: pesar  " FONT_LEFT ": volver");
    else txt_foot(s, FONT_LEFT ": volver");
}

void ui_render(const osc_ui *u, const ui_ctx *c, osc_text_screen *s) {
    char a[TXT_COLS + 1], b[TXT_COLS + 1], line[TXT_COLS + 1];
    unsigned i;
    if (!c->have_status) {
        txt_clear(s, "OPEN SAECO", DISP_BLUE);
        txt_line(s, 1, TXT_DIM, "Arrancando...");
        return;
    }
    if (!c->link_ok) {
        txt_clear(s, "SIN ENLACE", DISP_GREY);
        txt_line(s, 1, TXT_WARN, "Sin enlace con el control.");
        txt_line(s, 2, TXT_DIM, "Los datos no son actuales.");
        return;
    }
    switch ((ui_page)u->page) {
    case UI_HOME:
        txt_clear(s, "OPEN SAECO", title_colour(c));
        snprintf(a, sizeof a, "%s", state_name(c->status->state));
        pair(line, "Estado", a);
        txt_line(s, 0, fault(c) ? TXT_BAD : TXT_NORMAL, line);
        fmt_value(a, sizeof a, F_DC, c->status->boiler_dc);
        pair(line, "Caldera", a);
        txt_line(s, 1, TXT_NORMAL, line);
        pair(line, "Puerta", (c->status->inputs & OSC_IN_DOOR_CLOSED) ? "cerrada" : "abierta");
        txt_line(s, 2, (c->status->inputs & OSC_IN_DOOR_CLOSED) ? TXT_NORMAL : TXT_WARN, line);
        pair(line, "Grupo", (c->status->inputs & OSC_IN_BU_PRESENT) ? "presente" : "ausente");
        txt_line(s, 3, (c->status->inputs & OSC_IN_BU_PRESENT) ? TXT_NORMAL : TXT_WARN, line);
        fmt_value(a, sizeof a, F_MV, c->status->rail_12v_mv);
        fmt_value(b, sizeof b, F_MV, c->status->rail_24v_mv);
        snprintf(line, sizeof line, "%.12s  %.12s", a, b);
        txt_line(s, 4, TXT_DIM, line);
        if (c->last_reply_type == OSC_MSG_ERROR && c->last_reply_for == OSC_MSG_START_RECIPE)
            txt_line(s, 6, TXT_WARN, "Cafe: aun no disponible");
        if (!c->keypad_valid) txt_line(s, 7, TXT_BAD, "Teclado sin respuesta");
        txt_foot(s, fault(c) ? "OK: borrar  MENU: menu" : "OK: cafe  MENU: menu");
        break;
    case UI_MENU:
        txt_clear(s, "MENU", title_colour(c));
        for (i = 0; i < MENU_N; ++i) txt_line(s, i, i == u->sel ? TXT_SELECTED : TXT_NORMAL, menu_items[i]);
        txt_foot(s, FONT_UP FONT_DOWN " OK  " FONT_LEFT ": volver");
        break;
    case UI_SETUP:
        txt_clear(s, "PUESTA A PUNTO", title_colour(c));
        for (i = 1; i < OSC_TEST_COUNT; ++i)
            txt_line(s, i - 1u, i - 1u == u->sel ? TXT_SELECTED : TXT_NORMAL, tests[i].name);
        txt_line(s, OSC_TEST_COUNT - 1u, OSC_TEST_COUNT - 1u == u->sel ? TXT_SELECTED : TXT_NORMAL, "Volver");
        txt_foot(s, FONT_UP FONT_DOWN " OK  " FONT_LEFT ": volver");
        break;
    case UI_CONFIRM: {
        const test_info *t = &tests[u->test];
        txt_clear(s, t->name, title_colour(c));
        for (i = 0; i < 5u; ++i)
            if (t->desc[i]) txt_line(s, i, TXT_NORMAL, t->desc[i]);
        if (t->param_label) {
            snprintf(a, sizeof a, "%u %s", (unsigned)u->param, t->param_unit);
            pair(line, t->param_label, a);
            txt_line(s, 6, TXT_SELECTED, line);
        }
        txt_foot(s, t->param_label ? FONT_UP FONT_DOWN " valor  OK: empezar" : "OK: empezar  " FONT_LEFT ": volver");
        break;
    }
    case UI_TEST:
        txt_clear(s, tests[u->test].name, title_colour(c));
        render_test(u, c, s);
        break;
    case UI_ENTRY:
        txt_clear(s, "CALIBRAR CAUDAL", title_colour(c));
        txt_line(s, 0, TXT_NORMAL, "Pese el agua dispensada");
        txt_line(s, 1, TXT_NORMAL, "e indique el volumen.");
        snprintf(a, sizeof a, "%u ml", (unsigned)u->entry_ml);
        pair(line, "Medido", a);
        txt_line(s, 3, TXT_SELECTED, line);
        if (c->have_report) {
            snprintf(a, sizeof a, "%ld", (long)c->report->value[1]);
            pair(line, "Pulsos", a);
            txt_line(s, 4, TXT_DIM, line);
        }
        if (u->flow_ppl) {
            snprintf(a, sizeof a, "%ld p/l", (long)u->flow_ppl);
            pair(line, "Resultado", a);
            txt_line(s, 6, TXT_OK, line);
            txt_line(s, 7, TXT_DIM, "Nominal: 1925 p/l");
        }
        txt_foot(s, FONT_UP FONT_DOWN " ml  OK  " FONT_LEFT ": volver");
        break;
    case UI_INFO:
        txt_clear(s, "INFORMACION", title_colour(c));
        snprintf(a, sizeof a, "v0");
        pair(line, "Protocolo", a);
        txt_line(s, 0, TXT_NORMAL, line);
        snprintf(a, sizeof a, "%lu s", (unsigned long)(c->status->uptime_ms / 1000u));
        pair(line, "Control activo", a);
        txt_line(s, 1, TXT_NORMAL, line);
        snprintf(a, sizeof a, "%lu/%lu", (unsigned long)c->requests, (unsigned long)c->replies);
        pair(line, "Peticiones/resp.", a);
        txt_line(s, 2, TXT_NORMAL, line);
        snprintf(a, sizeof a, "%lu", (unsigned long)c->recoveries);
        pair(line, "Rearranques frontal", a);
        txt_line(s, 3, TXT_NORMAL, line);
        snprintf(a, sizeof a, "%u", (unsigned)c->status->ntc_raw);
        pair(line, "NTC (ADC)", a);
        txt_line(s, 4, TXT_NORMAL, line);
        fmt_value(a, sizeof a, F_MA, c->status->brew_ma);
        pair(line, "Grupo", a);
        txt_line(s, 5, TXT_NORMAL, line);
        txt_foot(s, FONT_LEFT ": volver");
        break;
    }
}
