/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2017 Nick Moore
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */


#include <stdio.h>

#include "esp_log.h"

#include "driver/gpio.h"
#include "driver/touch_pad.h"

#include "py/runtime.h"
#include "py/mphal.h"
#include "modmachine.h"

typedef struct _mtp_obj_t {
    mp_obj_base_t base;
    gpio_num_t gpio_id;
    touch_pad_t touchpad_id;
    mp_obj_t callback;
} mtp_obj_t;

mtp_obj_t touchpad_obj[] = {
    {{&machine_touchpad_type}, GPIO_NUM_4, TOUCH_PAD_NUM0, mp_const_none},
    {{&machine_touchpad_type}, GPIO_NUM_0, TOUCH_PAD_NUM1, mp_const_none},
    {{&machine_touchpad_type}, GPIO_NUM_2, TOUCH_PAD_NUM2, mp_const_none},
    {{&machine_touchpad_type}, GPIO_NUM_15, TOUCH_PAD_NUM3, mp_const_none},
    {{&machine_touchpad_type}, GPIO_NUM_13, TOUCH_PAD_NUM4, mp_const_none},
    {{&machine_touchpad_type}, GPIO_NUM_12, TOUCH_PAD_NUM5, mp_const_none},
    {{&machine_touchpad_type}, GPIO_NUM_14, TOUCH_PAD_NUM6, mp_const_none},
    {{&machine_touchpad_type}, GPIO_NUM_27, TOUCH_PAD_NUM7, mp_const_none},
    {{&machine_touchpad_type}, GPIO_NUM_33, TOUCH_PAD_NUM8, mp_const_none},
    {{&machine_touchpad_type}, GPIO_NUM_32, TOUCH_PAD_NUM9, mp_const_none},
};

#define TOUCHPAD_FILTER_TOUCH_PERIOD (10)

static void mtp_intr(void * arg)
{
    uint32_t pad_intr = touch_pad_get_status();
    touch_pad_clear_status();
    for (int i = 0; i < MP_ARRAY_SIZE(touchpad_obj); i++) {
        if ((pad_intr >> i) & 0x01) {
            if (touchpad_obj[i].callback != mp_const_none) {
                mp_sched_schedule(touchpad_obj[i].callback, mp_const_none);
            }
        }
    }
}

STATIC mp_obj_t mtp_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw,
        const mp_obj_t *args) {

    mp_arg_check_num(n_args, n_kw, 1, 1, true);
    gpio_num_t pin_id = machine_pin_get_id(args[0]);
    const mtp_obj_t *self = NULL;
    for (int i = 0; i < MP_ARRAY_SIZE(touchpad_obj); i++) {
        if (pin_id == touchpad_obj[i].gpio_id) { self = &touchpad_obj[i]; break; }
    }
    if (!self) mp_raise_ValueError("invalid pin for touchpad");

    static int initialized = 0;
    if (!initialized) {
        touch_pad_init();
        touch_pad_set_fsm_mode(TOUCH_FSM_MODE_TIMER);
        touch_pad_set_voltage(TOUCH_HVOLT_2V7, TOUCH_LVOLT_0V5, TOUCH_HVOLT_ATTEN_1V);
        touch_pad_filter_start(TOUCHPAD_FILTER_TOUCH_PERIOD);
        touch_pad_isr_register(mtp_intr, NULL);
        esp_sleep_enable_touchpad_wakeup();
        initialized = 1;
    }
    esp_err_t err = touch_pad_config(self->touchpad_id, 0);
    if (err == ESP_OK) return MP_OBJ_FROM_PTR(self);
    mp_raise_ValueError("Touch pad error");
}

STATIC mp_obj_t mtp_config(mp_obj_t self_in, mp_obj_t value_in) {
    mtp_obj_t *self = self_in;
    uint16_t value = mp_obj_get_int(value_in);
    esp_err_t err = touch_pad_set_thresh(self->touchpad_id, value);
    if (err == ESP_OK) return mp_const_none;
    mp_raise_ValueError("Touch pad error");
}
MP_DEFINE_CONST_FUN_OBJ_2(mtp_config_obj, mtp_config);

STATIC mp_obj_t mtp_read(mp_obj_t self_in) {
    mtp_obj_t *self = self_in;
    uint16_t value;
    esp_err_t err = touch_pad_read(self->touchpad_id, &value);
    if (err == ESP_OK) return MP_OBJ_NEW_SMALL_INT(value);
    mp_raise_ValueError("Touch pad error");
}
MP_DEFINE_CONST_FUN_OBJ_1(mtp_read_obj, mtp_read);

STATIC mp_obj_t mtp_callback(mp_obj_t self_in, mp_obj_t callback) {
    mtp_obj_t *self = self_in;
    self->callback = callback;
    if (callback == mp_const_none) {
        touch_pad_intr_disable();
        touch_pad_clear_status();
    }
    else {
        touch_pad_intr_enable();
    }
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_2(mtp_callback_obj, mtp_callback);

STATIC const mp_rom_map_elem_t mtp_locals_dict_table[] = {
    // instance methods
    { MP_ROM_QSTR(MP_QSTR_config), MP_ROM_PTR(&mtp_config_obj) },
    { MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&mtp_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_callback), MP_ROM_PTR(&mtp_callback_obj) },
};

STATIC MP_DEFINE_CONST_DICT(mtp_locals_dict, mtp_locals_dict_table);

const mp_obj_type_t machine_touchpad_type = {
    { &mp_type_type },
    .name = MP_QSTR_TouchPad,
    .make_new = mtp_make_new,
    .locals_dict = (mp_obj_t)&mtp_locals_dict,
};
