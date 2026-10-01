import { LitElement, html, nothing } from "lit";
import { mdiFormatListBulleted, mdiHomeLightningBoltOutline } from "@mdi/js";
import { DOMAIN } from "./entities";
import { hasString, localize } from "./localize";
import { defineElement } from "./register";
import type { HomeAssistant, WallboxCardConfig } from "./types";

// Options left out of the YAML while they keep these values.
const DEFAULTS: Partial<WallboxCardConfig> = {
  home_includes_wallbox: true,
  show_session: true,
  show_progress: true,
  show_controls: true,
  show_last_session: true,
};
const OPTIONAL_TEXT = ["name", "solar_power", "home_power", "grid_import_power"];

/**
 * Make sure Home Assistant's form is loaded: it comes with the editors of the
 * built-in cards, so load one of them.
 */
async function loadHaForm(): Promise<void> {
  if (customElements.get("ha-form")) {
    return;
  }
  const helpers = await (window as unknown as { loadCardHelpers?: () => Promise<any> }).loadCardHelpers?.();
  const card = await helpers?.createCardElement({ type: "entities", entities: [] });
  await card?.constructor?.getConfigElement?.();
}

class ThorWallboxCardEditor extends LitElement {
  static properties = {
    hass: { attribute: false },
    _config: { state: true },
  };

  declare hass?: HomeAssistant;
  declare _config?: WallboxCardConfig;

  setConfig(config: WallboxCardConfig): void {
    this._config = config;
  }

  connectedCallback(): void {
    super.connectedCallback();
    loadHaForm()
      .then(() => customElements.whenDefined("ha-form"))
      .then(() => this.requestUpdate());
  }

  protected render() {
    if (!this.hass || !this._config) {
      return nothing;
    }
    return html`
      <ha-form
        .hass=${this.hass}
        .data=${{ ...DEFAULTS, ...this._config }}
        .schema=${this._schema()}
        .computeLabel=${this._label}
        .computeHelper=${this._helper}
        @value-changed=${this._valueChanged}
      ></ha-form>
    `;
  }

  private _schema() {
    const power = { entity: { filter: { domain: "sensor", device_class: "power" } } };
    return [
      { name: "device_id", required: true, selector: { device: { filter: { integration: DOMAIN } } } },
      { name: "name", selector: { text: {} } },
      {
        name: "flow",
        type: "expandable",
        flatten: true,
        iconPath: mdiHomeLightningBoltOutline,
        title: localize(this.hass, "editor_flow"),
        schema: [
          { name: "solar_power", selector: power },
          { name: "home_power", selector: power },
          { name: "grid_import_power", selector: power },
          { name: "home_includes_wallbox", selector: { boolean: {} } },
        ],
      },
      {
        name: "content",
        type: "expandable",
        flatten: true,
        iconPath: mdiFormatListBulleted,
        title: localize(this.hass, "editor_content"),
        schema: [
          { name: "show_session", selector: { boolean: {} } },
          { name: "show_progress", selector: { boolean: {} } },
          { name: "show_controls", selector: { boolean: {} } },
          { name: "show_last_session", selector: { boolean: {} } },
        ],
      },
    ];
  }

  private _label = (schema: { name: string }): string => {
    const key = `editor_${schema.name}`;
    return hasString(key) ? localize(this.hass, key) : schema.name;
  };

  private _helper = (schema: { name: string }): string | undefined => {
    const key = `helper_${schema.name}`;
    return hasString(key) ? localize(this.hass, key) : undefined;
  };

  private _valueChanged(ev: CustomEvent): void {
    const config: Record<string, unknown> = { ...ev.detail.value };
    for (const [key, value] of Object.entries(DEFAULTS)) {
      if (config[key] === value) {
        delete config[key];
      }
    }
    for (const key of OPTIONAL_TEXT) {
      if (!config[key]) {
        delete config[key];
      }
    }
    this.dispatchEvent(
      new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }),
    );
  }
}

defineElement("thor-wallbox-card-editor", ThorWallboxCardEditor);
