import type { HassEntity, HomeAssistant } from "./types";

/** The locale for numbers, following the user's number format setting. */
function numberLocale(hass: HomeAssistant): string | undefined {
  switch (hass.locale?.number_format) {
    case "comma_decimal":
      return "en-US";
    case "decimal_comma":
      return "de";
    case "space_comma":
      return "fr";
    case "system":
      return undefined;
    default:
      return hass.locale?.language || hass.language;
  }
}

export function formatNumber(hass: HomeAssistant, value: number, digits: number): string {
  return new Intl.NumberFormat(numberLocale(hass), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    useGrouping: hass.locale?.number_format !== "none",
  }).format(value);
}

/** Watts as kW with one decimal, e.g. "7,2 kW". */
export function formatKw(hass: HomeAssistant, watts: number): string {
  return `${formatNumber(hass, watts / 1000, 1)} kW`;
}

/** Minutes as "1 h 24 min" or "30 min". */
export function formatMinutes(minutes: number): string {
  const total = Math.round(minutes);
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  if (!hours) {
    return `${rest} min`;
  }
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

/** A time entity's "HH:MM:SS" state as "HH:MM"; undefined when not set. */
export function formatClock(state?: string): string | undefined {
  const match = /^(\d{2}):(\d{2})/.exec(state ?? "");
  return match ? `${match[1]}:${match[2]}` : undefined;
}

/** A date as "18 lug" (or the time, when it is today). */
export function formatShortDate(hass: HomeAssistant, date: Date): string {
  const language = hass.locale?.language || hass.language;
  if (date.toDateString() === new Date().toDateString()) {
    return new Intl.DateTimeFormat(language, { hour: "2-digit", minute: "2-digit" }).format(date);
  }
  return new Intl.DateTimeFormat(language, { day: "numeric", month: "short" }).format(date);
}

/** A power sensor's state in W, whatever its unit; undefined when unknown. */
export function powerInWatts(stateObj?: HassEntity): number | undefined {
  if (!stateObj) {
    return undefined;
  }
  const value = Number(stateObj.state);
  if (stateObj.state === "" || !Number.isFinite(value)) {
    return undefined;
  }
  switch (stateObj.attributes.unit_of_measurement) {
    case "kW":
      return value * 1000;
    case "MW":
      return value * 1_000_000;
    default:
      return value;
  }
}

/** A numeric state, or undefined when unknown or unavailable. */
export function numericState(stateObj?: HassEntity): number | undefined {
  if (!stateObj || stateObj.state === "") {
    return undefined;
  }
  const value = Number(stateObj.state);
  return Number.isFinite(value) ? value : undefined;
}
