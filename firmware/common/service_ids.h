/* SPDX-License-Identifier: MIT */
/* Set-up tests shared by both firmwares: identifiers, phases and reasons.
 * The STM32 runs them (firmware/stm32/src/service.c); the ESP32 lists and
 * labels them. Each maps to tests of docs/HD8911/characterization-plan.md;
 * values are the six int32 of osc_test_report, in the units listed. */
#ifndef OSC_SERVICE_IDS_H
#define OSC_SERVICE_IDS_H

typedef enum {
    OSC_TEST_NONE = 0,
    /* Inputs and sensors, no load (SW-02/03, WL-01, NT): door 0/1,
     * unit present 0/1, unit at work 0/1, water ADC code, boiler 0.1 degC,
     * 24 V rail mV. Allowed in FAULT, so the door switch can be checked. */
    OSC_TEST_INPUTS = 1,
    /* Brew unit to the work switch and back (BU-03/04/06): time to work ms,
     * running current I0 mA, start peak mA, current at the stop mA, return
     * time ms, DRV8876 faults. */
    OSC_TEST_BREW_UNIT = 2,
    /* Valve 2 s (VA-02 with a clamp): 24 V before mV, 24 V during mV,
     * on time ms. */
    OSC_TEST_VALVE = 3,
    /* Mains relay K701 1 s, alone: 24 V before, during mV, on time ms. */
    OSC_TEST_RELAY = 4,
    /* Pump until the parameter in ml (nominal pulses) or 30 s (PU-04, FL-01):
     * on time ms, flow pulses, nominal ml x10, ml/s x100, boiler 0.1 degC at
     * start and at the end. */
    OSC_TEST_PUMP = 5,
    /* Heater to the parameter in degC (default 90) or 60 s, then 15 s coast
     * (NT-02/03): start 0.1 degC, end of heating 0.1 degC, heating time ms,
     * rate 0.01 degC/s, peak 0.1 degC, overshoot 0.1 degC. */
    OSC_TEST_HEATER = 6,
    /* Grinder for the parameter in ms, at most OSC_GRINDER_MAX_ON_MS
     * (GR-02/03/04 with a clamp): on time ms, 12 V and 24 V during mV. */
    OSC_TEST_GRINDER = 7,
    OSC_TEST_COUNT
} osc_test_id;

typedef enum {
    OSC_TEST_IDLE = 0,
    OSC_TEST_RUNNING = 1,
    OSC_TEST_DONE = 2,
    OSC_TEST_ABORTED = 3,
    OSC_TEST_REFUSED = 4
} osc_test_phase;

typedef enum {
    OSC_REASON_OK = 0,
    OSC_REASON_DOOR = 1,       /* door or drawer open */
    OSC_REASON_STATE = 2,      /* core not idle (or busy with another test) */
    OSC_REASON_TIMEOUT = 3,
    OSC_REASON_DRIVER = 4,     /* DRV8876 nFAULT */
    OSC_REASON_STOP = 5,       /* STOP from the interface */
    OSC_REASON_LINK = 6,       /* link to the ESP32 lost */
    OSC_REASON_SENSOR = 7,     /* NTC open or short */
    OSC_REASON_LIMIT = 8,      /* temperature limit */
    OSC_REASON_UNIT = 9,       /* brew unit missing */
    OSC_REASON_NO_FLOW = 10,   /* pump without flow pulses: dry or blocked */
    OSC_REASON_PARAM = 11,     /* parameter out of range */
    OSC_REASON_UNKNOWN = 12    /* no such test */
} osc_test_reason;
#endif
