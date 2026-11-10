/**
 * Booking a Fast charge from the card: the booking dialog's form, as plain data.
 *
 * The dialog (booking-dialog.ts) edits a BookingForm and sends it with the integration's
 * `growatt_thor_cloud.start_charging` action, which either starts charging now or
 * schedules a start at a time (once, or every day), with an optional limit of energy,
 * cost or duration at which the charger stops. This module holds everything that is not
 * drawing:
 *
 * - where the form starts from: the scheduled start the charger already has, so that
 *   the dialog edits it, or else the integration's Fast entities (*Fast - Start*,
 *   *Fast - Start at*, *Fast - Limit* and its values);
 * - what makes the form valid, with the same rules as the action;
 * - the action's data;
 * - the sentence that sums the booking up, and the short text of a limit.
 *
 * It uses no DOM, so its tests (booking.test.ts) run in Node.
 *
 * Times are "HH:MM" on Home Assistant's clock (its configured time zone): that is how
 * the integration reads a start time, whatever the time zone of the browser.
 */
import { formatAmount, formatMinutes, formatMoney } from "./format";
import { localize, type StringKey } from "./localize";
import type { HomeAssistant } from "./types";

export const START_MODES = ["now", "at_time", "every_day"] as const;
export const LIMITS = ["none", "energy", "cost", "duration"] as const;
export type StartMode = (typeof START_MODES)[number];
export type Limit = (typeof LIMITS)[number];

// Bounds of a duration limit, in minutes: from 1 minute to 23 h 59 min.
const MAX_DURATION = 24 * 60 - 1;
const CLOCK = /^([01]\d|2[0-3]):[0-5]\d$/;

/**
 * The dialog's fields. Numbers are kept as the user typed them (the value of an
 * <input>), so a half-typed "7," is not rewritten while typing; they are read when the
 * form is checked and sent, with a point or a comma before the decimals. An empty
 * string is a field not filled in.
 */
export interface BookingForm {
  start: StartMode;
  time: string; // "HH:MM", for a start at a time or every day.
  limit: Limit;
  energy: string; // kWh
  cost: string; // In the charger's currency.
  hours: string; // Duration limit: hours and minutes, "" read as 0.
  minutes: string;
}

/** Values the form starts from; anything missing starts empty. */
export interface BookingDefaults {
  start?: string;
  time?: string; // "HH:MM"
  limit?: string;
  energy?: number;
  cost?: number;
  duration?: number; // Minutes.
}

/** Why a form cannot be sent: the key of the message the dialog shows. */
export type BookingError = "error_time" | "error_energy" | "error_cost" | "error_duration";

function isStartMode(value?: string): value is StartMode {
  return (START_MODES as readonly string[]).includes(value ?? "");
}

function isLimit(value?: string): value is Limit {
  return (LIMITS as readonly string[]).includes(value ?? "");
}

/** A finite number as form text ("20", "0.25"); "" for anything else. */
function text(value?: number): string {
  return value !== undefined && Number.isFinite(value) ? String(value) : "";
}

/**
 * "HH:MM" of `date` on the clock of `timeZone` (an IANA name such as "Europe/Rome"),
 * or of the browser when it is missing or unknown.
 */
export function clockIn(date: Date, timeZone?: string): string {
  const options: Intl.DateTimeFormatOptions = { hour: "2-digit", minute: "2-digit", hourCycle: "h23" };
  let parts: Intl.DateTimeFormatPart[];
  try {
    parts = new Intl.DateTimeFormat("en-GB", { ...options, timeZone }).formatToParts(date);
  } catch {
    parts = new Intl.DateTimeFormat("en-GB", options).formatToParts(date);
  }
  const part = (type: string) => parts.find((p) => p.type === type)?.value ?? "00";
  return `${part("hour")}:${part("minute")}`;
}

/**
 * The defaults of a scheduled start, from the "Fast - Next scheduled start" sensor:
 * its state (the start, ISO 8601) and attributes (`every_day`, `limit`, `limit_value`,
 * with a duration in minutes). Undefined when there is no scheduled start.
 */
export function reservationDefaults(
  state: string | undefined,
  attributes: Record<string, unknown>,
  timeZone?: string,
): BookingDefaults | undefined {
  const start = new Date(state ?? "");
  if (Number.isNaN(start.getTime())) {
    return undefined;
  }
  const limit = typeof attributes.limit === "string" ? attributes.limit : "none";
  const value = typeof attributes.limit_value === "number" ? attributes.limit_value : undefined;
  return {
    start: attributes.every_day ? "every_day" : "at_time",
    time: clockIn(start, timeZone),
    limit,
    energy: limit === "energy" ? value : undefined,
    cost: limit === "cost" ? value : undefined,
    duration: limit === "duration" ? value : undefined,
  };
}

/** The form the dialog opens with. In RFID mode a start "now" becomes a start at a time. */
export function initialForm(defaults: BookingDefaults, rfid: boolean): BookingForm {
  const start = isStartMode(defaults.start) ? defaults.start : "now";
  const duration = defaults.duration !== undefined && defaults.duration > 0 ? Math.round(defaults.duration) : undefined;
  return {
    start: rfid && start === "now" ? "at_time" : start,
    time: CLOCK.test(defaults.time ?? "") ? defaults.time! : "",
    limit: isLimit(defaults.limit) ? defaults.limit : "none",
    energy: text(defaults.energy),
    cost: text(defaults.cost),
    hours: duration === undefined ? "" : String(Math.floor(duration / 60)),
    minutes: duration === undefined ? "" : String(duration % 60),
  };
}

/** A typed number, with a point or a comma before the decimals; NaN when empty or not a number. */
function number(value: string): number {
  const typed = value.trim().replace(",", ".");
  return typed === "" ? NaN : Number(typed);
}

/** The duration limit in minutes; NaN unless hours and minutes are whole numbers in range. */
export function durationMinutes(form: BookingForm): number {
  const hours = form.hours.trim() === "" ? 0 : Number(form.hours);
  const minutes = form.minutes.trim() === "" ? 0 : Number(form.minutes);
  if (!Number.isInteger(hours) || !Number.isInteger(minutes) || hours < 0 || minutes < 0 || minutes > 59) {
    return NaN;
  }
  return hours * 60 + minutes;
}

/** The first reason the form cannot be sent, or undefined when it can. */
export function bookingError(form: BookingForm): BookingError | undefined {
  if (form.start !== "now" && !CLOCK.test(form.time)) {
    return "error_time";
  }
  switch (form.limit) {
    case "energy":
      return number(form.energy) > 0 ? undefined : "error_energy";
    case "cost":
      return number(form.cost) > 0 ? undefined : "error_cost";
    case "duration": {
      const minutes = durationMinutes(form);
      return minutes >= 1 && minutes <= MAX_DURATION ? undefined : "error_duration";
    }
    default:
      return undefined;
  }
}

/** The data of the `growatt_thor_cloud.start_charging` action for a valid form. */
export function serviceData(form: BookingForm, deviceId: string): Record<string, unknown> {
  const data: Record<string, unknown> = { device_id: deviceId, limit: form.limit };
  if (form.limit === "energy") {
    data.value = number(form.energy);
  } else if (form.limit === "cost") {
    data.value = number(form.cost);
  } else if (form.limit === "duration") {
    data.value = durationMinutes(form);
  }
  if (form.start !== "now") {
    data.start_time = form.time;
    data.every_day = form.start === "every_day";
  }
  return data;
}

/** "HH:MM" as the user's language writes times (e.g. "10:00 PM" in American English). */
function formatClockTime(hass: HomeAssistant, time: string): string {
  const [hours, minutes] = time.split(":").map(Number);
  return new Intl.DateTimeFormat(hass.locale?.language || hass.language, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(2000, 0, 1, hours, minutes));
}

/**
 * A limit as a short text: "20 kWh", "5,00 €", "2 h 30 min"; "" without a limit.
 * `value` is in kWh, in `currency` or in minutes, by limit.
 */
export function limitText(hass: HomeAssistant, limit: string, value: number, currency?: string): string {
  switch (limit) {
    case "energy":
      return `${formatAmount(hass, value, 2)} kWh`;
    case "cost":
      return formatMoney(hass, value, currency);
    case "duration":
      return formatMinutes(value);
    default:
      return "";
  }
}

/**
 * One sentence that sums a valid form up, e.g. "Starts today at 22:00 and stops at
 * 20 kWh." A start at a time is today when that time is still ahead on Home Assistant's
 * clock (`now`, in `timeZone`), else tomorrow, as the integration schedules it.
 */
export function bookingSummary(
  hass: HomeAssistant,
  form: BookingForm,
  now: Date,
  currency?: string,
  timeZone?: string,
): string {
  const t = (key: StringKey, vars?: Record<string, string>) => localize(hass, key, vars);
  let start: string;
  if (form.start === "now") {
    start = t("summary_now");
  } else {
    const time = formatClockTime(hass, form.time);
    if (form.start === "every_day") {
      start = t("summary_every_day", { time });
    } else {
      start = form.time > clockIn(now, timeZone) ? t("summary_today", { time }) : t("summary_tomorrow", { time });
    }
  }
  let limit: string;
  if (form.limit === "none") {
    limit = t("summary_no_limit");
  } else {
    const value = form.limit === "duration" ? durationMinutes(form) : number(form.limit === "energy" ? form.energy : form.cost);
    const amount = limitText(hass, form.limit, value, currency);
    limit = form.limit === "duration" ? t("summary_stops_after", { value: amount }) : t("summary_stops_at", { value: amount });
  }
  return t("summary", { start, limit });
}
