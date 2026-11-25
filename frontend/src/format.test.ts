import assert from "node:assert/strict";
import { describe, test } from "node:test";
import { formatShortDate, formatTimeInZone } from "./format";
import type { HomeAssistant } from "./types";

function hass(language: string, timeZone?: string): HomeAssistant {
  return {
    states: {},
    entities: {},
    devices: {},
    language,
    locale: { language, number_format: "language" },
    config: timeZone ? { time_zone: timeZone } : undefined,
    callService: async () => undefined,
    formatEntityState: (obj) => obj.state,
  };
}

describe("timezone formatting", () => {
  test("formats times on Home Assistant's clock regardless of browser timezone", () => {
    // 2026-11-10T21:30:00Z is 22:30 in Europe/Rome (UTC+1) and 16:30 in America/New_York (UTC-5).
    const instant = new Date("2026-11-10T21:30:00Z");
    assert.equal(formatTimeInZone(hass("en-GB", "Europe/Rome"), instant), "22:30");
    assert.equal(formatTimeInZone(hass("en-GB", "America/New_York"), instant), "16:30");
  });

  test("decides today vs earlier date in Home Assistant's time zone", () => {
    // 2026-11-10T23:30:00Z is 2026-11-11 00:30 in Rome, but still 2026-11-10 18:30 in New York.
    const event = new Date("2026-11-10T23:30:00Z");
    const now = new Date("2026-11-11T08:00:00Z");
    // In Rome both are on Nov 11 -> shows time.
    assert.equal(formatShortDate(hass("en-GB", "Europe/Rome"), event, now), "00:30");
    // In New York event is Nov 10 while now is Nov 11 -> shows short date.
    assert.equal(formatShortDate(hass("en-GB", "America/New_York"), event, now), "10 Nov");
  });

  test("falls back cleanly when the configured time zone is unknown", () => {
    const instant = new Date("2026-11-10T21:30:00Z");
    assert.ok(formatTimeInZone(hass("en-GB", "Not/A_Zone"), instant).length > 0);
  });
});
