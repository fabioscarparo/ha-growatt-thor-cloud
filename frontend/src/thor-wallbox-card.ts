import { LitElement, html, nothing, svg, type PropertyValues, type TemplateResult } from "lit";
import {
  mdiAlertCircleOutline,
  mdiArrowDown,
  mdiArrowLeft,
  mdiArrowRight,
  mdiArrowUp,
  mdiBatteryHigh,
  mdiBatteryLow,
  mdiBatteryMedium,
  mdiBatteryOutline,
  mdiCalendarClock,
  mdiCalendarRemove,
  mdiCloudOffOutline,
  mdiCreditCardWirelessOutline,
  mdiCurrencyEur,
  mdiEvStation,
  mdiFlash,
  mdiHistory,
  mdiLightningBolt,
  mdiLock,
  mdiLockOpenVariant,
  mdiMenuDown,
  mdiPlay,
  mdiRocketLaunch,
  mdiSolarPower,
  mdiStop,
  mdiThermometer,
  mdiTimerOutline,
  mdiTransmissionTower,
  mdiWeatherNight,
} from "@mdi/js";
import "./editor";
import { ACTIVE_STATES, SESSION_STATES, findDevices, resolveEntities } from "./entities";
import { computeFlow, type Flow } from "./flow";
import {
  formatClock,
  formatKw,
  formatMinutes,
  formatNumber,
  formatShortDate,
  numericState,
  powerInWatts,
} from "./format";
import { localize, type StringKey } from "./localize";
import { defineElement } from "./register";
import { cardStyles } from "./styles";
import type { HassEntity, HomeAssistant, WallboxCardConfig } from "./types";

declare const __CARD_VERSION__: string;

// Tile colors by charger status, from Home Assistant's palette.
const STATUS_COLORS: Record<string, string> = {
  charging: "var(--success-color, #43a047)",
  suspended_ev: "var(--warning-color, #ffa600)",
  suspended_evse: "var(--warning-color, #ffa600)",
  preparing: "var(--info-color, #039be5)",
  finishing: "var(--teal-color, #009688)",
  reserved: "var(--purple-color, #926bc7)",
  faulted: "var(--error-color, #db4437)",
  available: "var(--state-inactive-color, #9e9e9e)",
};
const UNAVAILABLE_COLOR = "var(--state-unavailable-color, #bdbdbd)";
const SOLAR_COLOR = "var(--energy-solar-color, #ff9800)";
const GRID_COLOR = "var(--energy-grid-consumption-color, #488fc2)";
const OFF_PEAK_COLOR = "var(--deep-purple-color, #6e41ab)";

const MODES: Record<string, { icon: string; color: string }> = {
  fast: { icon: mdiFlash, color: "var(--primary-color, #009ac7)" },
  pv_linkage: { icon: mdiSolarPower, color: SOLAR_COLOR },
  off_peak: { icon: mdiWeatherNight, color: OFF_PEAK_COLOR },
};

// Codes and states that carry no information.
const EMPTY_STATES = ["", "unknown", "unavailable", "NoError"];
// Below this, in W, a source is not feeding the wallbox.
const MIN_FLOW = 50;
// A flow's dot crosses its line in 6 s at the lowest power and in 0.75 s at full
// power (a single-phase wallbox at 32 A).
const SLOWEST_CROSSING = 6;
const FASTEST_CROSSING = 0.75;
const FULL_POWER = 7400;

/** Seconds for the dot to cross a line, in quarter seconds so small changes keep the pace. */
function flowDuration(watts: number): number {
  const share = Math.min(1, Math.max(0, (watts - MIN_FLOW) / (FULL_POWER - MIN_FLOW)));
  const seconds = SLOWEST_CROSSING - share * (SLOWEST_CROSSING - FASTEST_CROSSING);
  return Math.round(seconds * 4) / 4;
}

// Largest radius of the bend from the solar circle down to the battery.
const BEND_RADIUS = 24;

/** The home battery's links, as SVG paths in px from the top left of the flow. */
interface BatteryLinks {
  wallbox: string;
  solar?: string;
}

interface Badge {
  icon: string;
  text: string;
  label?: string;
  color?: string;
}

interface Alert {
  icon: string;
  color: string;
  title: string;
  text: string;
}

interface Button {
  icon: string;
  label: string;
  disabled: boolean;
  action: () => void;
}

function icon(path: string, size = 24): TemplateResult {
  return html`<svg viewBox="0 0 24 24" width=${size} height=${size} aria-hidden="true">
    <path d=${path}></path>
  </svg>`;
}

function hasValue(state?: string): state is string {
  return state !== undefined && !EMPTY_STATES.includes(state);
}

class ThorWallboxCard extends LitElement {
  static styles = cardStyles;

  static properties = {
    hass: { attribute: false },
    _config: { state: true },
    _links: { state: true },
  };

  declare hass?: HomeAssistant;
  declare _config?: WallboxCardConfig;
  declare _links?: BatteryLinks;

  // Draws the battery's links again when the flow changes size.
  private _resizeObserver?: ResizeObserver;
  private _observedFlow?: Element;

  // The device's entities, rebuilt when the registry or the device changes.
  private _ids = new Map<string, string>();
  private _idsSource?: { entities: HomeAssistant["entities"]; device?: string };

  static getConfigElement(): HTMLElement {
    return document.createElement("thor-wallbox-card-editor");
  }

  static getStubConfig(hass: HomeAssistant): Partial<WallboxCardConfig> {
    const [deviceId] = findDevices(hass);
    return deviceId ? { device_id: deviceId } : {};
  }

  setConfig(config: WallboxCardConfig): void {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    this._config = { ...config };
  }

  getCardSize(): number {
    return 7;
  }

  getGridOptions(): Record<string, number> {
    return { columns: 12, min_columns: 6 };
  }

  connectedCallback(): void {
    super.connectedCallback();
    // Back on the page, maybe at another size: updated() watches the flow again and
    // redraws the battery's links.
    if (this.hasUpdated) {
      this.requestUpdate();
    }
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._resizeObserver?.disconnect();
    this._observedFlow = undefined;
  }

  protected updated(changed: PropertyValues): void {
    super.updated(changed);
    const flow = this.renderRoot.querySelector(".flow") ?? undefined;
    if (flow !== this._observedFlow) {
      this._resizeObserver ??= new ResizeObserver(() => this._measureLinks());
      this._resizeObserver.disconnect();
      if (flow) {
        this._resizeObserver.observe(flow);
      }
      this._observedFlow = flow;
    }
    this._measureLinks();
  }

  protected shouldUpdate(changed: PropertyValues): boolean {
    if (changed.has("_config") || !this.hass) {
      return true;
    }
    const old = changed.get("hass") as HomeAssistant | undefined;
    if (!old) {
      return true;
    }
    if (
      old.entities !== this.hass.entities ||
      old.locale !== this.hass.locale ||
      old.language !== this.hass.language ||
      old.themes !== this.hass.themes
    ) {
      return true;
    }
    return this._watched().some((id) => old.states[id] !== this.hass!.states[id]);
  }

  private _watched(): string[] {
    const config = this._config;
    const ids = [...this._entityIds().values()];
    for (const id of [
      config?.solar_power,
      config?.home_power,
      config?.grid_import_power,
      config?.grid_export_power,
      config?.battery_power,
      config?.battery_soc,
    ]) {
      if (id) {
        ids.push(id);
      }
    }
    return ids;
  }

  private _entityIds(): Map<string, string> {
    const hass = this.hass!;
    const device = this._config?.device_id;
    if (this._idsSource?.entities !== hass.entities || this._idsSource?.device !== device) {
      this._ids = resolveEntities(hass, device);
      this._idsSource = { entities: hass.entities, device };
    }
    return this._ids;
  }

  private _id(key: string): string | undefined {
    return this._entityIds().get(key);
  }

  private _obj(key: string): HassEntity | undefined {
    const id = this._id(key);
    return id ? this.hass!.states[id] : undefined;
  }

  private _state(key: string): string | undefined {
    return this._obj(key)?.state;
  }

  private _available(key: string): boolean {
    const state = this._state(key);
    return state !== undefined && state !== "unavailable";
  }

  private _configured(entityId?: string): HassEntity | undefined {
    return entityId ? this.hass!.states[entityId] : undefined;
  }

  private _t(key: StringKey, vars?: Record<string, string>): string {
    return localize(this.hass, key, vars);
  }

  protected render(): TemplateResult | typeof nothing {
    if (!this._config || !this.hass) {
      return nothing;
    }
    if (!this._config.device_id) {
      return this._renderMessage(this._t("no_device"));
    }
    const statusObj = this._obj("sensor.status");
    if (!statusObj) {
      return this._renderMessage(this._t("device_not_found"));
    }
    const status = statusObj.state;
    const mode = this._state("select.charge_mode");
    const offline = status === "unavailable";
    const inSession = SESSION_STATES.includes(status);
    const power = powerInWatts(this._obj("sensor.power"));
    const style = [
      `--tile-color: ${STATUS_COLORS[status] ?? UNAVAILABLE_COLOR}`,
      `--mode-color: ${(mode && MODES[mode]?.color) || "var(--primary-color)"}`,
    ].join("; ");

    return html`
      <ha-card style=${style}>
        ${this._renderTile(statusObj, status, mode)}
        ${offline || power === undefined
          ? nothing
          : html`<div class="value" aria-label=${this._t("power")}>
              <span class="number">${formatNumber(this.hass, power / 1000, 1)}</span>
              <span class="unit">kW</span>
            </div>`}
        ${this._alerts(status).map((alert) => this._renderAlert(alert))}
        ${offline ? nothing : this._renderFlow(status, mode, power ?? 0)}
        ${this._renderBadges(status, mode, inSession)}
        ${this._renderFeatures(status, inSession)}
      </ha-card>
    `;
  }

  private _renderMessage(text: string): TemplateResult {
    return html`<ha-card><div class="message">${text}</div></ha-card>`;
  }

  private _renderTile(statusObj: HassEntity, status: string, mode?: string): TemplateResult {
    const hass = this.hass!;
    const device = hass.devices?.[this._config!.device_id!];
    const name = this._config!.name || device?.name_by_user || device?.name || "THOR";
    const secondary = [hass.formatEntityState(statusObj), this._detail(status, mode)]
      .filter(Boolean)
      .join(" · ");
    const modeIcon = mode ? MODES[mode]?.icon : undefined;
    return html`
      <div
        class="tile"
        role="button"
        tabindex="0"
        @click=${this._moreInfo}
        @keydown=${this._tileKeydown}
      >
        <div class="tile-icon">
          <div class="shape">${icon(mdiEvStation)}</div>
          ${modeIcon ? html`<div class="tile-badge">${icon(modeIcon, 12)}</div>` : nothing}
        </div>
        <div class="tile-info">
          <span class="primary">${name}</span>
          <span class="secondary">${secondary}</span>
        </div>
      </div>
    `;
  }

  /** What the status alone does not say, next to it on the second line. */
  private _detail(status: string, mode?: string): string {
    const hass = this.hass!;
    switch (status) {
      case "charging": {
        const current = numericState(this._obj("sensor.current"));
        const voltage = numericState(this._obj("sensor.voltage"));
        return [
          current === undefined ? "" : `${formatNumber(hass, current, 1)} A`,
          voltage === undefined ? "" : `${formatNumber(hass, voltage, 0)} V`,
        ]
          .filter(Boolean)
          .join(" · ");
      }
      case "available":
        return this._t("plug_in");
      case "preparing":
        return this._t("car_connected");
      case "suspended_evse":
        if (mode === "pv_linkage") {
          return this._t("waiting_surplus");
        }
        return mode === "off_peak" ? this._t("waiting_slot") : "";
      case "reserved":
        return this._reservation() ?? "";
      case "faulted": {
        const code = this._state("sensor.error_code");
        return hasValue(code) ? code : "";
      }
      default:
        return "";
    }
  }

  /** The next scheduled start, or undefined when there is none. */
  private _reservation(): string | undefined {
    const hass = this.hass!;
    const obj = this._obj("sensor.next_reservation");
    if (!obj || !hasValue(obj.state)) {
      return undefined;
    }
    const start = new Date(obj.state);
    if (obj.attributes.every_day && !Number.isNaN(start.getTime())) {
      const time = new Intl.DateTimeFormat(hass.locale?.language || hass.language, {
        hour: "2-digit",
        minute: "2-digit",
      }).format(start);
      return this._t("every_day", { time });
    }
    return hass.formatEntityState(obj);
  }

  private _alerts(status: string): Alert[] {
    const alerts: Alert[] = [];
    if (status === "unavailable") {
      alerts.push({
        icon: mdiCloudOffOutline,
        color: "var(--warning-color, #ffa600)",
        title: this._t("offline_title"),
        text: this._t("offline_text"),
      });
    }
    if (status === "faulted") {
      const code = this._state("sensor.error_code");
      const vendor = this._state("sensor.vendor_error_code");
      alerts.push({
        icon: mdiAlertCircleOutline,
        color: "var(--error-color, #db4437)",
        title: hasValue(code) ? `${this._t("fault")}: ${code}` : this._t("fault"),
        text: [hasValue(vendor) ? this._t("vendor_code", { code: vendor }) : "", this._t("fault_hint")]
          .filter(Boolean)
          .join(" "),
      });
    }
    if (
      this._state("select.authorization_mode") === "rfid" &&
      ["available", "preparing"].includes(status)
    ) {
      alerts.push({
        icon: mdiCreditCardWirelessOutline,
        color: "var(--info-color, #039be5)",
        title: this._t("rfid_title"),
        text: this._t("rfid_text"),
      });
    }
    return alerts;
  }

  private _renderAlert(alert: Alert): TemplateResult {
    return html`
      <div class="alert" style=${`--alert-color: ${alert.color}`}>
        ${icon(alert.icon)}
        <div class="text">
          <div class="title">${alert.title}</div>
          <div>${alert.text}</div>
        </div>
      </div>
    `;
  }

  /**
   * Solar, grid and home battery around the wallbox, as in the energy dashboard,
   * with where the wallbox's power comes from (see computeFlow).
   */
  private _renderFlow(status: string, mode: string | undefined, wallbox: number) {
    const config = this._config!;
    const hasSolar = Boolean(config.solar_power);
    const hasGrid = Boolean(config.grid_import_power || config.grid_export_power);
    const hasBattery = Boolean(config.battery_power);
    if (!hasSolar && !hasGrid && !hasBattery) {
      return nothing;
    }
    const hass = this.hass!;
    const solar = powerInWatts(this._configured(config.solar_power));
    const gridImport = powerInWatts(this._configured(config.grid_import_power));
    const gridExport = powerInWatts(this._configured(config.grid_export_power));
    const batteryPower = powerInWatts(this._configured(config.battery_power));
    const charging = status === "charging" && wallbox > MIN_FLOW;
    const flow = computeFlow({
      wallbox,
      charging,
      solar,
      gridImport,
      gridExport,
      home: powerInWatts(this._configured(config.home_power)),
      homeIncludesWallbox: config.home_includes_wallbox !== false,
      battery:
        batteryPower === undefined ? undefined : config.battery_charging_positive ? -batteryPower : batteryPower,
    });
    const soc = numericState(this._configured(config.battery_soc));

    const notes: string[] = [];
    if (charging) {
      const parts = [
        flow.fromSolar > MIN_FLOW ? this._t("from_solar", { value: formatKw(hass, flow.fromSolar) }) : "",
        flow.fromBattery > MIN_FLOW ? this._t("from_battery", { value: formatKw(hass, flow.fromBattery) }) : "",
        flow.fromGrid > MIN_FLOW ? this._t("from_grid", { value: formatKw(hass, flow.fromGrid) }) : "",
      ].filter(Boolean);
      if (parts.length) {
        const sentence = parts.join(", ");
        notes.push(`${sentence.charAt(0).toUpperCase()}${sentence.slice(1)}.`);
      }
    } else if (mode === "pv_linkage") {
      if (flow.surplus !== undefined) {
        notes.push(this._t("surplus", { value: formatKw(hass, flow.surplus) }));
      }
      if (flow.batteryFromSolar > MIN_FLOW) {
        notes.push(
          soc === undefined
            ? this._t("battery_charging", { value: formatKw(hass, flow.batteryCharging) })
            : this._t("battery_charging_soc", {
                value: formatKw(hass, flow.batteryCharging),
                soc: `${formatNumber(hass, soc, 0)} %`,
              }),
        );
      }
    }
    const value = (watts?: number) => (watts === undefined ? "-" : formatKw(hass, watts));
    // Empty places on the sides keep the wallbox in the middle, above the battery.
    const spacer = html`<div class="node spacer"></div><div class="line spacer"></div>`;

    return html`
      <div class="flow">
        <div class="row">
          ${hasSolar
            ? html`
                <div class="node solar">
                  <span class="label">${this._t("solar")}</span>
                  <div class="circle">${icon(mdiSolarPower)}<span>${value(solar)}</span></div>
                </div>
                ${this._renderLine("solar", flow.fromSolar, false)}
              `
            : spacer}
          <div class="node wallbox">
            <span class="label">${this._t("wallbox")}</span>
            <div class="circle">${icon(mdiEvStation)}<span>${formatKw(hass, wallbox)}</span></div>
          </div>
          ${hasGrid
            ? html`
                ${this._renderLine("grid", flow.fromGrid, true)}
                <div class="node grid">
                  <span class="label">${this._t("grid")}</span>
                  <div class="circle">
                    ${icon(mdiTransmissionTower)}
                    ${config.grid_export_power
                      ? html`<span class="import">${icon(mdiArrowLeft, 12)}${value(gridImport)}</span>
                          <span class="export">${icon(mdiArrowRight, 12)}${value(gridExport)}</span>`
                      : html`<span>${value(gridImport)}</span>`}
                  </div>
                </div>
              `
            : html`<div class="line spacer"></div><div class="node spacer"></div>`}
        </div>
        ${hasBattery ? this._renderBattery(flow, soc) : nothing}
        ${notes.length ? html`<p class="note">${notes.join(" ")}</p>` : nothing}
        ${hasBattery && this._links ? this._renderLinks(this._links, flow) : nothing}
      </div>
    `;
  }

  /** The home battery below the wallbox; _renderLinks draws its links. */
  private _renderBattery(flow: Flow, soc: number | undefined): TemplateResult {
    const hass = this.hass!;
    let batteryIcon = mdiBatteryHigh;
    if (soc !== undefined) {
      if (soc < 10) {
        batteryIcon = mdiBatteryOutline;
      } else if (soc <= 32.5) {
        batteryIcon = mdiBatteryLow;
      } else if (soc <= 72.5) {
        batteryIcon = mdiBatteryMedium;
      }
    }
    let power = html`<span>${formatKw(hass, 0)}</span>`;
    if (flow.batteryDischarging > MIN_FLOW) {
      power = html`<span class="discharging">${icon(mdiArrowUp, 12)}${formatKw(hass, flow.batteryDischarging)}</span>`;
    } else if (flow.batteryCharging > MIN_FLOW) {
      power = html`<span class="charging">${icon(mdiArrowDown, 12)}${formatKw(hass, flow.batteryCharging)}</span>`;
    }
    return html`
      <div class="node battery">
        <div class="circle">
          ${icon(batteryIcon)}
          ${soc === undefined ? nothing : html`<span>${formatNumber(hass, soc, 0)} %</span>`}
          ${power}
        </div>
        <span class="label">${this._t("battery")}</span>
      </div>
    `;
  }

  /**
   * Where the battery's links run, from where the circles are laid out: up to the
   * wallbox, and from the bottom of the solar circle, bending into the battery's side.
   */
  private _measureLinks(): void {
    const flow = this.renderRoot.querySelector(".flow");
    const circle = (node: string) => flow?.querySelector<HTMLElement>(`.node.${node} .circle`) ?? undefined;
    const battery = circle("battery");
    const wallbox = circle("wallbox");
    let links: BatteryLinks | undefined;
    if (battery && wallbox && battery.offsetWidth) {
      // Half pixels keep the 1px lines sharp.
      const centre = (el: HTMLElement) => Math.round(el.offsetLeft + el.offsetWidth / 2) + 0.5;
      const bottom = (el: HTMLElement) => el.offsetTop + el.offsetHeight;
      const y = Math.round(battery.offsetTop + battery.offsetHeight / 2) + 0.5;
      const solar = circle("solar");
      let bend: string | undefined;
      if (solar) {
        const x = centre(solar);
        const top = bottom(solar);
        const radius = Math.max(0, Math.min(BEND_RADIUS, y - top, battery.offsetLeft - x));
        bend = `M${x} ${top}V${y - radius}A${radius} ${radius} 0 0 0 ${x + radius} ${y}H${battery.offsetLeft}`;
      }
      links = { wallbox: `M${centre(battery)} ${battery.offsetTop}V${bottom(wallbox)}`, solar: bend };
    }
    if (JSON.stringify(links) !== JSON.stringify(this._links)) {
      this._links = links;
    }
  }

  /**
   * The battery's links, with a running dot where power flows: up to the wallbox
   * while it feeds the car, from solar while it charges from it.
   */
  private _renderLinks(links: BatteryLinks, flow: Flow): TemplateResult {
    const still = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const link = (path: string | undefined, kind: string, watts: number) => {
      if (!path) {
        return nothing;
      }
      const active = watts > MIN_FLOW;
      // Without motion, the dot stays halfway.
      const points = still ? "0.5;0.5" : "0;1";
      return svg`
        <g class="link ${kind} ${active ? "active" : ""}">
          <path d=${path}></path>
          ${active
            ? svg`<circle r="2.5">
                <animateMotion
                  path=${path}
                  dur="${flowDuration(watts)}s"
                  repeatCount="indefinite"
                  calcMode="linear"
                  keyPoints=${points}
                  keyTimes="0;1"
                ></animateMotion>
              </circle>`
            : nothing}
        </g>
      `;
    };
    return html`
      <svg class="links" aria-hidden="true">
        ${link(links.wallbox, "battery-out", flow.fromBattery)}
        ${link(links.solar, "battery-in", flow.batteryFromSolar)}
      </svg>
    `;
  }

  /** A source's link to the wallbox, with a running dot while it feeds the wallbox. */
  private _renderLine(source: "solar" | "grid", watts: number, towardsLeft: boolean): TemplateResult {
    const active = watts > MIN_FLOW;
    return html`
      <div
        class="line ${source} ${active ? "active" : ""} ${towardsLeft ? "reverse" : ""}"
        style=${active ? `--flow-duration: ${flowDuration(watts)}s` : ""}
      >
        <div class="track">${active ? html`<span class="dot"></span>` : nothing}</div>
      </div>
    `;
  }

  private _badges(status: string, mode: string | undefined, inSession: boolean): Badge[] {
    const hass = this.hass!;
    const config = this._config!;
    const badges: Badge[] = [];

    if (inSession && config.show_session !== false) {
      const energy = numericState(this._obj("sensor.session_energy"));
      const duration = numericState(this._obj("sensor.session_duration"));
      const cost = this._obj("sensor.session_cost");
      if (energy !== undefined) {
        badges.push({ icon: mdiLightningBolt, label: this._t("energy"), text: `${formatNumber(hass, energy, 2)} kWh` });
      }
      if (duration !== undefined) {
        badges.push({ icon: mdiTimerOutline, label: this._t("duration"), text: formatMinutes(duration) });
      }
      if (cost && numericState(cost) !== undefined) {
        badges.push({ icon: mdiCurrencyEur, label: this._t("cost"), text: hass.formatEntityState(cost) });
      }
    }
    if (!inSession && config.show_last_session !== false) {
      const end = new Date(this._state("sensor.last_session") ?? "");
      const energy = numericState(this._obj("sensor.last_session_energy"));
      if (!Number.isNaN(end.getTime())) {
        badges.push({
          icon: mdiHistory,
          label: this._t("last_session"),
          text: [formatShortDate(hass, end), energy === undefined ? "" : `${formatNumber(hass, energy, 2)} kWh`]
            .filter(Boolean)
            .join(" · "),
        });
      }
    }

    // The LOCK device class reads on = unlocked.
    const lock = this._state("binary_sensor.cable_lock");
    if (lock === "off") {
      badges.push({ icon: mdiLock, text: this._t("cable_locked") });
    } else if (lock === "on") {
      badges.push({ icon: mdiLockOpenVariant, text: this._t("cable_unlocked") });
    }

    if (mode === "pv_linkage") {
      const importGrid = this._state("switch.import_grid");
      const importPower = numericState(this._obj("number.import_grid_power"));
      if (importGrid === "on") {
        badges.push({
          icon: mdiTransmissionTower,
          color: GRID_COLOR,
          text:
            importPower === undefined
              ? this._t("grid_import")
              : this._t("grid_import_power", { power: `${formatNumber(hass, importPower, 1)} kW` }),
        });
      } else if (importGrid === "off") {
        badges.push({ icon: mdiSolarPower, color: SOLAR_COLOR, text: this._t("surplus_only") });
      }
    }
    if (this._state("switch.boost") === "on") {
      const type = this._obj("select.boost_type");
      badges.push({
        icon: mdiRocketLaunch,
        color: "var(--primary-color, #009ac7)",
        text: type && hasValue(type.state) ? this._t("boost", { type: hass.formatEntityState(type) }) : "Boost",
      });
    }
    if (mode === "off_peak") {
      const slots = [1, 2, 3]
        .map((n) => [
          formatClock(this._state(`time.off_peak_${n}_from`)),
          formatClock(this._state(`time.off_peak_${n}_to`)),
        ])
        .filter(([from, to]) => from && to && from !== to)
        .map(([from, to]) => `${from}-${to}`);
      if (slots.length) {
        badges.push({ icon: mdiWeatherNight, color: OFF_PEAK_COLOR, label: this._t("slots"), text: slots.join(", ") });
      }
    }
    const reservation = status === "reserved" ? undefined : this._reservation();
    if (reservation) {
      badges.push({
        icon: mdiCalendarClock,
        color: "var(--purple-color, #926bc7)",
        label: this._t("scheduled_start"),
        text: reservation,
      });
    }
    if (status === "suspended_ev" && this._state("switch.warm_up") === "on") {
      badges.push({ icon: mdiThermometer, color: "var(--deep-orange-color, #ff6f22)", text: this._t("warm_up") });
    }
    return badges;
  }

  private _renderBadges(status: string, mode: string | undefined, inSession: boolean) {
    const badges = this._badges(status, mode, inSession);
    if (!badges.length) {
      return nothing;
    }
    return html`
      <div class="badges">
        ${badges.map(
          (badge) => html`
            <div class="badge" style=${badge.color ? `--badge-color: ${badge.color}` : ""}>
              ${icon(badge.icon, 18)}
              <div class="info">
                ${badge.label ? html`<span class="label">${badge.label}</span>` : nothing}
                <span class="content">${badge.text}</span>
              </div>
            </div>
          `,
        )}
      </div>
    `;
  }

  private _renderFeatures(status: string, inSession: boolean) {
    const config = this._config!;
    const progress = config.show_progress === false ? nothing : this._renderProgress();
    const controls = config.show_controls === false ? nothing : this._renderControls(status, inSession);
    if (progress === nothing && controls === nothing) {
      return nothing;
    }
    return html`<div class="features">${progress}${controls}</div>`;
  }

  private _renderProgress() {
    const hass = this.hass!;
    const pct = numericState(this._obj("sensor.session_progress"));
    if (pct === undefined) {
      return nothing;
    }
    const caption = this._progressCaption();
    const width = Math.min(100, Math.max(0, pct));
    return html`
      <div class="progress">
        <div class="caption">
          <span>${caption}</span>
          <span class="pct">${formatNumber(hass, pct, 0)} %</span>
        </div>
        <div
          class="bar"
          role="progressbar"
          aria-label=${caption}
          aria-valuenow=${width}
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <div class="done" style=${`width: ${width}%`}></div>
          <div class="rest"></div>
        </div>
      </div>
    `;
  }

  /** The session limit, or the smart Boost energy, with how much of it is done. */
  private _progressCaption(): string {
    const hass = this.hass!;
    const limitObj = this._obj("sensor.session_limit");
    const limit = limitObj?.state;
    if (limit === "energy" || limit === "cost" || limit === "duration") {
      const label = this._t(`limit_${limit}` as StringKey);
      const target = limitObj?.attributes.value;
      const doneObj = this._obj(`sensor.session_${limit}`);
      const done = numericState(doneObj);
      if (done === undefined || typeof target !== "number") {
        return label;
      }
      const format = (value: number): string => {
        if (limit === "duration") {
          return formatMinutes(value);
        }
        if (limit === "energy") {
          return `${formatNumber(hass, value, 1)} kWh`;
        }
        return `${formatNumber(hass, value, 2)} ${doneObj?.attributes.unit_of_measurement ?? ""}`.trim();
      };
      return `${label} · ${this._t("done_of", { done: format(done), target: format(target) })}`;
    }
    const time = formatClock(this._state("time.boost_departure"));
    const label = time ? this._t("boost_by", { time }) : "Boost";
    const done = numericState(this._obj("sensor.session_energy"));
    const target = numericState(this._obj("number.boost_energy"));
    if (done === undefined || target === undefined) {
      return label;
    }
    return `${label} · ${this._t("done_of", {
      done: `${formatNumber(hass, done, 1)} kWh`,
      target: `${formatNumber(hass, target, 1)} kWh`,
    })}`;
  }

  /**
   * Start or stop, unlock and the charge mode, following the integration's rules:
   * no remote start or stop in RFID mode, no mode change while a session is open,
   * nothing while the wallbox is unreachable.
   */
  private _renderControls(status: string, inSession: boolean) {
    const offline = status === "unavailable";
    const rfid = this._state("select.authorization_mode") === "rfid";
    const chargingId = this._id("switch.charging");
    const cancelId = this._id("button.cancel_reservation");
    const unlockId = this._id("button.unlock");
    const buttons: Button[] = [];

    if (cancelId && this._available("button.cancel_reservation")) {
      buttons.push({
        icon: mdiCalendarRemove,
        label: this._t("cancel"),
        disabled: offline,
        action: () => this._call("button", "press", cancelId),
      });
    } else if (chargingId) {
      const switchReady = !offline && this._available("switch.charging");
      if (ACTIVE_STATES.includes(status)) {
        buttons.push({
          icon: mdiStop,
          label: this._t("stop"),
          disabled: rfid || !switchReady,
          action: () => this._call("switch", "turn_off", chargingId),
        });
      } else {
        buttons.push({
          icon: mdiPlay,
          label: this._t("start"),
          disabled: rfid || !switchReady || !["available", "preparing"].includes(status),
          action: () => this._call("switch", "turn_on", chargingId),
        });
      }
    }
    if (unlockId) {
      buttons.push({
        icon: mdiLockOpenVariant,
        label: this._t("unlock"),
        disabled: offline || !this._available("button.unlock"),
        action: () => this._call("button", "press", unlockId),
      });
    }
    const modeObj = this._obj("select.charge_mode");
    if (!buttons.length && !modeObj) {
      return nothing;
    }
    return html`
      ${buttons.length
        ? html`<div class="buttons">
            ${buttons.map(
              (button) => html`
                <button class="button" type="button" ?disabled=${button.disabled} @click=${button.action}>
                  ${icon(button.icon, 20)}
                  <span>${button.label}</span>
                </button>
              `,
            )}
          </div>`
        : nothing}
      ${modeObj ? this._renderModeSelect(modeObj, inSession || offline) : nothing}
      ${inSession ? html`<p class="note">${this._t("locked_note")}</p>` : nothing}
    `;
  }

  private _renderModeSelect(modeObj: HassEntity, locked: boolean): TemplateResult {
    const hass = this.hass!;
    const current = modeObj.state;
    const options: string[] = modeObj.attributes.options ?? [];
    const disabled = locked || current === "unavailable";
    return html`
      <div class="select ${disabled ? "disabled" : ""}">
        ${icon(MODES[current]?.icon ?? mdiEvStation, 20)}
        <div class="content">
          <span class="label">${this._t("charge_mode")}</span>
          <span class="current">${hass.formatEntityState(modeObj)}</span>
        </div>
        ${icon(mdiMenuDown, 20)}
        <select aria-label=${this._t("charge_mode")} ?disabled=${disabled} @change=${this._modeChanged}>
          ${options.map(
            (option) =>
              html`<option value=${option} ?selected=${option === current}>
                ${hass.formatEntityState(modeObj, option)}
              </option>`,
          )}
        </select>
      </div>
    `;
  }

  private _modeChanged = (ev: Event): void => {
    const select = ev.target as HTMLSelectElement;
    const entityId = this._id("select.charge_mode");
    const current = this._state("select.charge_mode") ?? "";
    const option = select.value;
    // The select follows the entity, which shows the new mode once it is applied.
    select.value = current;
    if (entityId && option !== current) {
      this._call("select", "select_option", entityId, { option });
    }
  };

  private async _call(
    domain: string,
    service: string,
    entityId: string,
    data: Record<string, unknown> = {},
  ): Promise<void> {
    try {
      await this.hass!.callService(domain, service, { entity_id: entityId, ...data });
    } catch (err) {
      const message = (err as { message?: string })?.message ?? String(err);
      this.dispatchEvent(
        new CustomEvent("hass-notification", { detail: { message }, bubbles: true, composed: true }),
      );
    }
  }

  private _moreInfo = (): void => {
    const entityId = this._id("sensor.status");
    if (entityId) {
      this.dispatchEvent(
        new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }),
      );
    }
  };

  private _tileKeydown = (ev: KeyboardEvent): void => {
    if (ev.key === "Enter" || ev.key === " ") {
      ev.preventDefault();
      this._moreInfo();
    }
  };
}

defineElement("thor-wallbox-card", ThorWallboxCard);

const customCards = ((window as unknown as { customCards?: Record<string, unknown>[] }).customCards ??= []);
if (!customCards.some((card) => card.type === "thor-wallbox-card")) {
  customCards.push({
    type: "thor-wallbox-card",
    name: localize(undefined, "card_name"),
    description: localize(undefined, "card_description"),
    preview: true,
    documentationURL: "https://github.com/fabioscarparo/ha-growatt-thor-cloud#wallbox-card",
  });
}

console.info(`%c THOR-WALLBOX-CARD %c ${__CARD_VERSION__} `, "color: #fff; background: #43a047", "");
