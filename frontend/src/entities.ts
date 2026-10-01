import type { HomeAssistant } from "./types";

export const DOMAIN = "growatt_thor_cloud";

// Charger statuses, as the status sensor reports them.
export const ACTIVE_STATES = ["charging", "suspended_ev", "suspended_evse"];
export const SESSION_STATES = [...ACTIVE_STATES, "finishing"];

/** Devices of the integration, in the order Home Assistant lists their entities. */
export function findDevices(hass: HomeAssistant): string[] {
  const devices = new Set<string>();
  for (const entry of Object.values(hass.entities)) {
    if (entry.platform === DOMAIN && entry.device_id) {
      devices.add(entry.device_id);
    }
  }
  return [...devices];
}

/**
 * The device's entities by "<domain>.<translation key>", e.g. "sensor.status".
 *
 * The key names each entity in the integration, so entities keep being found
 * after they are renamed.
 */
export function resolveEntities(hass: HomeAssistant, deviceId?: string): Map<string, string> {
  const ids = new Map<string, string>();
  if (!deviceId) {
    return ids;
  }
  for (const entry of Object.values(hass.entities)) {
    if (entry.platform !== DOMAIN || entry.device_id !== deviceId || !entry.translation_key) {
      continue;
    }
    ids.set(`${entry.entity_id.split(".")[0]}.${entry.translation_key}`, entry.entity_id);
  }
  return ids;
}
