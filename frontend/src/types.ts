// The parts of Home Assistant's frontend objects the card uses.

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
  last_changed: string;
  last_updated: string;
}

export interface EntityRegistryDisplayEntry {
  entity_id: string;
  device_id?: string;
  platform?: string;
  translation_key?: string;
}

export interface DeviceRegistryEntry {
  id: string;
  name: string | null;
  name_by_user: string | null;
}

export interface FrontendLocale {
  language: string;
  number_format?: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  entities: Record<string, EntityRegistryDisplayEntry>;
  devices: Record<string, DeviceRegistryEntry>;
  language: string;
  locale: FrontendLocale;
  themes?: unknown;
  callService(domain: string, service: string, data?: Record<string, unknown>): Promise<unknown>;
  formatEntityState(stateObj: HassEntity, state?: string): string;
}

export interface WallboxCardConfig {
  type: string;
  device_id?: string;
  name?: string;
  solar_power?: string;
  home_power?: string;
  grid_import_power?: string;
  home_includes_wallbox?: boolean;
  show_session?: boolean;
  show_progress?: boolean;
  show_controls?: boolean;
  show_last_session?: boolean;
}
