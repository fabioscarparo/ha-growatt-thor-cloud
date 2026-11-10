import assert from "node:assert/strict";
import { describe, test } from "node:test";
import {
  type BookingForm,
  bookingError,
  bookingSummary,
  clockIn,
  initialForm,
  limitText,
  reservationDefaults,
  serviceData,
} from "./booking";
import type { HomeAssistant } from "./types";

// The booking dialog's logic (booking.ts): where the form starts from, what makes it
// valid, the start_charging data and the sentence that sums it up. Times are on Home
// Assistant's clock, Europe/Rome here, which is UTC+1 in November.

const ROME = "Europe/Rome";

function hass(language: string): HomeAssistant {
  return {
    states: {},
    entities: {},
    devices: {},
    language,
    locale: { language, number_format: "language" },
    callService: async () => undefined,
    formatEntityState: (obj) => obj.state,
  };
}

function form(fields: Partial<BookingForm>): BookingForm {
  return { start: "now", time: "", limit: "none", energy: "", cost: "", hours: "", minutes: "", ...fields };
}

describe("initial form", () => {
  test("follows the scheduled start, on Home Assistant's clock", () => {
    // 21:00 UTC is 22:00 in Rome.
    const defaults = reservationDefaults(
      "2026-11-10T21:00:00+00:00",
      { every_day: true, limit: "energy", limit_value: 20 },
      ROME,
    );
    assert.deepEqual(defaults, {
      start: "every_day",
      time: "22:00",
      limit: "energy",
      energy: 20,
      cost: undefined,
      duration: undefined,
    });
    assert.deepEqual(initialForm(defaults!, false), form({ start: "every_day", time: "22:00", limit: "energy", energy: "20" }));
  });

  test("splits a duration limit into hours and minutes", () => {
    const defaults = reservationDefaults("2026-11-10T05:30:00+01:00", { limit: "duration", limit_value: 150 }, ROME);
    assert.deepEqual(initialForm(defaults!, false), form({ start: "at_time", time: "05:30", limit: "duration", hours: "2", minutes: "30" }));
  });

  test("has no scheduled start to follow without a start time", () => {
    assert.equal(reservationDefaults("unknown", {}, ROME), undefined);
  });

  test("falls back to empty values and a start now", () => {
    assert.deepEqual(initialForm({ start: "later", time: "7:00", limit: "speed" }, false), form({}));
  });

  test("starts at a time in RFID mode, where charging now needs the card", () => {
    assert.equal(initialForm({ start: "now" }, true).start, "at_time");
    assert.equal(initialForm({ start: "every_day" }, true).start, "every_day");
  });
});

describe("validation", () => {
  test("needs a start time unless starting now", () => {
    assert.equal(bookingError(form({ start: "at_time" })), "error_time");
    assert.equal(bookingError(form({ start: "every_day", time: "24:00" })), "error_time");
    assert.equal(bookingError(form({ start: "at_time", time: "22:00" })), undefined);
    assert.equal(bookingError(form({ start: "now" })), undefined);
  });

  test("needs energy and cost above 0, with a point or a comma", () => {
    assert.equal(bookingError(form({ limit: "energy" })), "error_energy");
    assert.equal(bookingError(form({ limit: "energy", energy: "0" })), "error_energy");
    assert.equal(bookingError(form({ limit: "energy", energy: "7,5" })), undefined);
    assert.equal(bookingError(form({ limit: "cost", cost: "abc" })), "error_cost");
    assert.equal(bookingError(form({ limit: "cost", cost: "2.50" })), undefined);
  });

  test("needs a duration from 1 minute to 23 h 59 min, in whole hours and minutes", () => {
    assert.equal(bookingError(form({ limit: "duration" })), "error_duration");
    assert.equal(bookingError(form({ limit: "duration", minutes: "1" })), undefined);
    assert.equal(bookingError(form({ limit: "duration", hours: "23", minutes: "59" })), undefined);
    assert.equal(bookingError(form({ limit: "duration", hours: "24" })), "error_duration");
    assert.equal(bookingError(form({ limit: "duration", hours: "1", minutes: "60" })), "error_duration");
    assert.equal(bookingError(form({ limit: "duration", hours: "1.5" })), "error_duration");
  });
});

describe("start_charging data", () => {
  test("starts now without a time", () => {
    assert.deepEqual(serviceData(form({ limit: "cost", cost: "3,5" }), "dev1"), {
      device_id: "dev1",
      limit: "cost",
      value: 3.5,
    });
  });

  test("schedules a start once or every day", () => {
    assert.deepEqual(serviceData(form({ start: "at_time", time: "22:00" }), "dev1"), {
      device_id: "dev1",
      limit: "none",
      start_time: "22:00",
      every_day: false,
    });
    assert.deepEqual(serviceData(form({ start: "every_day", time: "06:30", limit: "energy", energy: "20" }), "dev1"), {
      device_id: "dev1",
      limit: "energy",
      value: 20,
      start_time: "06:30",
      every_day: true,
    });
  });

  test("sends a duration in minutes", () => {
    assert.equal(serviceData(form({ limit: "duration", hours: "2", minutes: "30" }), "dev1").value, 150);
  });
});

describe("summary", () => {
  // 18:00 in Rome.
  const now = new Date("2026-11-10T17:00:00Z");

  test("reads today or tomorrow from Home Assistant's clock", () => {
    assert.equal(clockIn(now, ROME), "18:00");
    const en = hass("en-GB");
    assert.equal(
      bookingSummary(en, form({ start: "at_time", time: "22:00", limit: "energy", energy: "20" }), now, "EUR", ROME),
      "Starts today at 22:00 and stops at 20 kWh.",
    );
    assert.equal(
      bookingSummary(en, form({ start: "at_time", time: "18:00" }), now, "EUR", ROME),
      "Starts tomorrow at 18:00 with no limit.",
    );
  });

  test("speaks Italian, with Italian numbers and money", () => {
    const it = hass("it");
    // Intl puts a no-break space before the currency sign.
    assert.equal(
      bookingSummary(it, form({ limit: "cost", cost: "5" }), now, "EUR", ROME),
      "Parte subito e si ferma a 5,00\u00a0€.",
    );
    assert.equal(
      bookingSummary(it, form({ start: "every_day", time: "06:30", limit: "duration", hours: "1", minutes: "45" }), now, "EUR", ROME),
      "Parte ogni giorno alle 06:30 e si ferma dopo 1 h 45 min.",
    );
  });

  test("writes limits briefly", () => {
    const it = hass("it");
    assert.equal(limitText(it, "energy", 7.5, "EUR"), "7,5 kWh");
    assert.equal(limitText(it, "cost", 2, "XYZ1"), "2,00 XYZ1");
    assert.equal(limitText(it, "duration", 90), "1 h 30 min");
    assert.equal(limitText(it, "none", 0), "");
  });
});
