/**
 * <thor-wallbox-booking>: the card's booking dialog, for a Fast charge.
 *
 * The card adds this element when the user taps its "Scheduled start" row and removes it
 * when the dialog fires `closed`. The dialog opens at once, as a modal native <dialog>
 * styled like Home Assistant's own dialogs, and becomes a bottom sheet on phones. It asks:
 *
 * - when to start: now, at a time (once) or every day at a time;
 * - the limit at which the charger stops, if any: energy (kWh), cost (in the charger's
 *   currency) or duration (hours and minutes).
 *
 * A sentence under the fields sums the booking up, or says what is still missing. The
 * main button sends it with the integration's `start_charging` action and closes the
 * dialog; when the action fails, its message shows in the dialog, which stays open.
 *
 * The form's data, its rules and the action's data live in booking.ts; this element only
 * draws them and reacts to the user. Being in the card's shadow root, the dialog
 * inherits the theme's variables, so it follows the light and dark themes.
 */
import { LitElement, css, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import {
  type BookingForm,
  LIMITS,
  START_MODES,
  bookingError,
  bookingSummary,
  serviceData,
} from "./booking";
import { DOMAIN } from "./entities";
import { localize, type StringKey } from "./localize";
import { defineElement } from "./register";
import type { HomeAssistant } from "./types";

// Labels of the choices, among the card's strings.
const START_LABELS: Record<string, StringKey> = {
  now: "start_now",
  at_time: "start_at_time",
  every_day: "start_every_day",
};
const LIMIT_LABELS: Record<string, StringKey> = {
  none: "limit_none",
  energy: "energy",
  cost: "cost",
  duration: "duration",
};

/** The symbol of an ISO 4217 currency ("€" for "EUR"), or `currency` as it is. */
function currencySymbol(hass: HomeAssistant, currency?: string): string {
  if (!currency || !/^[A-Z]{3}$/.test(currency)) {
    return currency ?? "";
  }
  try {
    const parts = new Intl.NumberFormat(hass.locale?.language || hass.language, {
      style: "currency",
      currency,
    }).formatToParts(0);
    return parts.find((part) => part.type === "currency")?.value ?? currency;
  } catch {
    return currency;
  }
}

class ThorWallboxBooking extends LitElement {
  static properties = {
    hass: { attribute: false },
    deviceId: { attribute: false },
    form: { attribute: false },
    currency: { attribute: false },
    rfid: { attribute: false },
    replaces: { attribute: false },
    _form: { state: true },
    _busy: { state: true },
    _error: { state: true },
  };

  declare hass?: HomeAssistant;
  // The charger's device, which the action targets.
  declare deviceId?: string;
  // The form to start from (see initialForm in booking.ts); read once, when the dialog opens.
  declare form?: BookingForm;
  // Unit of the cost limit, as the integration reports it (e.g. "EUR").
  declare currency?: string;
  // RFID mode: sessions start with the card, so only a start at a time can be set.
  declare rfid: boolean;
  // The charger has a scheduled start, which a new one replaces.
  declare replaces: boolean;
  declare _form?: BookingForm;
  // The action is on its way: the main button waits for it.
  declare _busy: boolean;
  // The message of a failed action.
  declare _error?: string;

  constructor() {
    super();
    this.rfid = false;
    this.replaces = false;
    this._busy = false;
  }

  private _t(key: StringKey, vars?: Record<string, string>): string {
    return localize(this.hass, key, vars);
  }

  private get _dialog(): HTMLDialogElement | null {
    return this.renderRoot.querySelector("dialog");
  }

  protected willUpdate(changed: PropertyValues): void {
    super.willUpdate(changed);
    if (!this._form && this.form) {
      this._form = { ...this.form };
    }
  }

  protected firstUpdated(): void {
    this._dialog?.showModal();
  }

  /** Close the dialog; `closed` follows. */
  close = (): void => {
    this._dialog?.close();
  };

  protected render(): TemplateResult | typeof nothing {
    const form = this._form;
    if (!form || !this.hass) {
      return nothing;
    }
    const error = bookingError(form);
    const starts = START_MODES.filter((mode) => !(this.rfid && mode === "now"));
    const dark = Boolean(this.hass.themes?.darkMode);
    return html`
      <dialog
        aria-labelledby="title"
        style=${`color-scheme: ${dark ? "dark" : "light"}`}
        @click=${this._backdropClick}
        @close=${this._closed}
      >
        <h2 id="title" class="title">${this._t("schedule")}</h2>
        <div class="content">
          <div class="field">
            <span class="field-label" id="start-label">${this._t("booking_start")}</span>
            ${this._segmented("start-label", starts, START_LABELS, form.start, (start) => this._set({ start }))}
            ${this.rfid ? html`<p class="note">${this._t("booking_rfid")}</p>` : nothing}
          </div>
          ${form.start === "now"
            ? nothing
            : html`<label class="input">
                <span class="name">${this._t("booking_time")}</span>
                <input
                  type="time"
                  required
                  .value=${form.time}
                  @input=${(ev: Event) => this._set({ time: (ev.target as HTMLInputElement).value })}
                />
              </label>`}
          <div class="field">
            <span class="field-label" id="limit-label">${this._t("booking_limit")}</span>
            ${this._segmented("limit-label", LIMITS, LIMIT_LABELS, form.limit, (limit) => this._set({ limit }))}
          </div>
          ${this._renderValue(form)}
          <p class="summary ${error ? "missing" : ""}" aria-live="polite">
            ${error
              ? this._t(error)
              : bookingSummary(this.hass, form, new Date(), this.currency, this.hass.config?.time_zone)}
          </p>
          ${this.replaces && form.start !== "now" ? html`<p class="note">${this._t("booking_replaces")}</p>` : nothing}
          ${this._error ? html`<div class="alert" role="alert">${this._error}</div>` : nothing}
        </div>
        <div class="actions">
          <button class="action text" type="button" @click=${this.close}>${this._t("booking_cancel")}</button>
          <button class="action filled" type="button" ?disabled=${Boolean(error) || this._busy} @click=${this._submit}>
            ${form.start === "now" ? this._t("start") : this._t("booking_confirm")}
          </button>
        </div>
      </dialog>
    `;
  }

  /** A segmented control, like Home Assistant's: one choice among a few, as radio buttons. */
  private _segmented<T extends string>(
    labelledBy: string,
    options: readonly T[],
    labels: Record<string, StringKey>,
    selected: T,
    choose: (option: T) => void,
  ): TemplateResult {
    return html`
      <div class="segmented" role="radiogroup" aria-labelledby=${labelledBy}>
        ${options.map(
          (option) => html`
            <button
              class="option ${option === selected ? "selected" : ""}"
              type="button"
              role="radio"
              aria-checked=${option === selected ? "true" : "false"}
              @click=${() => choose(option)}
            >
              <span>${this._t(labels[option])}</span>
            </button>
          `,
        )}
      </div>
    `;
  }

  /** The value of the chosen limit: energy, cost, or hours and minutes. */
  private _renderValue(form: BookingForm): TemplateResult | typeof nothing {
    // Text fields with a numeric keyboard rather than type="number": these keep what the
    // user types as it is, decimal comma included (see BookingForm).
    const field = (
      value: string,
      label: string,
      inputmode: string,
      change: (value: string) => void,
    ) => html`<input
      type="text"
      inputmode=${inputmode}
      autocomplete="off"
      placeholder="0"
      aria-label=${label}
      .value=${value}
      @input=${(ev: Event) => change((ev.target as HTMLInputElement).value)}
    />`;
    switch (form.limit) {
      case "energy":
        return html`<label class="input">
          <span class="name">${this._t("energy")}</span>
          ${field(form.energy, this._t("energy"), "decimal", (energy) => this._set({ energy }))}
          <span class="unit">kWh</span>
        </label>`;
      case "cost":
        return html`<label class="input">
          <span class="name">${this._t("cost")}</span>
          ${field(form.cost, this._t("cost"), "decimal", (cost) => this._set({ cost }))}
          <span class="unit">${currencySymbol(this.hass!, this.currency)}</span>
        </label>`;
      case "duration":
        return html`<div class="input">
          <span class="name">${this._t("duration")}</span>
          ${field(form.hours, `${this._t("duration")} (h)`, "numeric", (hours) => this._set({ hours }))}
          <span class="unit">h</span>
          ${field(form.minutes, `${this._t("duration")} (min)`, "numeric", (minutes) => this._set({ minutes }))}
          <span class="unit">min</span>
        </div>`;
      default:
        return nothing;
    }
  }

  private _set(patch: Partial<BookingForm>): void {
    this._form = { ...this._form!, ...patch };
    this._error = undefined;
  }

  private _submit = async (): Promise<void> => {
    const form = this._form;
    if (!form || !this.hass || !this.deviceId || bookingError(form) || this._busy) {
      return;
    }
    this._busy = true;
    this._error = undefined;
    try {
      await this.hass.callService(DOMAIN, "start_charging", serviceData(form, this.deviceId));
      this.close();
    } catch (err) {
      this._error = (err as { message?: string })?.message ?? String(err);
    } finally {
      this._busy = false;
    }
  };

  /** A click on the dimmed page around the dialog closes it, as in Home Assistant. */
  private _backdropClick = (ev: MouseEvent): void => {
    const dialog = this._dialog;
    if (!dialog || ev.target !== dialog) {
      return;
    }
    const box = dialog.getBoundingClientRect();
    const inside =
      ev.clientX >= box.left && ev.clientX <= box.right && ev.clientY >= box.top && ev.clientY <= box.bottom;
    if (!inside) {
      this.close();
    }
  };

  private _closed = (): void => {
    this.dispatchEvent(new CustomEvent("closed"));
  };

  // Home Assistant's dialog and its controls, through the theme's variables (see the
  // card's styles.ts for the same patterns on the card).
  static styles = css`
    :host {
      --accent: var(--primary-color, #009ac7);
    }
    dialog {
      width: min(580px, 95vw);
      max-width: 95vw;
      max-height: min(80vh, 720px);
      box-sizing: border-box;
      padding: 0;
      border: none;
      overflow: hidden;
      border-radius: var(--ha-dialog-border-radius, var(--ha-border-radius-3xl, 24px));
      background: var(--ha-dialog-surface-background, var(--card-background-color, #fff));
      color: var(--primary-text-color);
      box-shadow: var(--ha-box-shadow-l, 0 16px 32px -6px rgba(0, 0, 0, 0.2));
      font-family: var(--ha-font-family-body, Roboto, Noto, sans-serif);
      -webkit-font-smoothing: antialiased;
    }
    dialog[open] {
      display: flex;
      flex-direction: column;
      animation: dialog-in 200ms ease-out;
    }
    dialog::backdrop {
      background: rgba(0, 0, 0, 0.32);
    }
    .title {
      margin: 0;
      padding: 24px 24px 16px;
      font-size: var(--ha-font-size-2xl, 24px);
      line-height: 1.2;
      font-weight: var(--ha-font-weight-normal, 400);
    }
    .content {
      flex: 1;
      min-height: 0;
      overflow: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding: 0 24px;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .field-label {
      font-size: var(--ha-font-size-m, 14px);
      font-weight: var(--ha-font-weight-medium, 500);
    }
    .note,
    .summary {
      margin: 0;
      font-size: var(--ha-font-size-s, 12px);
      line-height: 1.4;
      color: var(--secondary-text-color);
    }
    .summary {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--primary-text-color);
    }
    .summary.missing {
      color: var(--secondary-text-color);
    }

    /* Segmented control, like ha-control-select. */
    .segmented {
      position: relative;
      display: flex;
      gap: 4px;
      padding: 4px;
      height: 44px;
      box-sizing: border-box;
      border-radius: var(--ha-border-radius-lg, 12px);
    }
    .segmented::before {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: var(--disabled-color, #bdbdbd);
      opacity: 0.2;
    }
    .option {
      position: relative;
      flex: 1;
      min-width: 0;
      padding: 0 4px;
      border: none;
      border-radius: calc(var(--ha-border-radius-lg, 12px) - 4px);
      background: none;
      font-family: inherit;
      font-size: var(--ha-font-size-m, 14px);
      font-weight: var(--ha-font-weight-medium, 500);
      color: var(--primary-text-color);
      cursor: pointer;
      outline: none;
    }
    .option::before {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: var(--accent);
      opacity: 0;
      transition: opacity 80ms ease-in-out;
    }
    .option:hover::before {
      opacity: 0.2;
    }
    .option.selected {
      color: var(--text-primary-color, #fff);
    }
    .option.selected::before {
      opacity: 1;
    }
    .option:focus-visible {
      box-shadow: 0 0 0 2px var(--accent);
    }
    .option span {
      position: relative;
      display: block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* A labelled field on the neutral fill of Home Assistant's controls. */
    .input {
      position: relative;
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 48px;
      padding: 0 12px;
      box-sizing: border-box;
      border-radius: var(--ha-border-radius-lg, 12px);
    }
    .input::before {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: var(--disabled-color, #bdbdbd);
      opacity: 0.2;
      pointer-events: none;
    }
    .input > * {
      position: relative;
    }
    .input:focus-within {
      box-shadow: 0 0 0 2px var(--accent);
    }
    .input .name {
      flex: 1;
      min-width: 0;
      font-size: var(--ha-font-size-m, 14px);
    }
    .input .unit {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    /* 16px: smaller text makes iOS zoom into the field. */
    .input input {
      width: 64px;
      min-width: 0;
      padding: 8px 0;
      border: none;
      background: none;
      font-family: inherit;
      font-size: 16px;
      text-align: end;
      color: var(--primary-text-color);
      outline: none;
    }
    .input input::placeholder {
      color: var(--secondary-text-color);
      opacity: 0.6;
    }
    .input input[type="time"] {
      width: auto;
    }

    .alert {
      position: relative;
      padding: 12px;
      border-radius: var(--ha-border-radius-lg, 12px);
      overflow: hidden;
      font-size: var(--ha-font-size-m, 14px);
      line-height: 1.4;
    }
    .alert::before {
      content: "";
      position: absolute;
      inset: 0;
      background: var(--error-color, #db4437);
      opacity: 0.12;
    }

    /* Buttons, like ha-button: plain for Cancel, filled for the main action. */
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding: 24px;
    }
    .action {
      position: relative;
      overflow: hidden;
      height: 40px;
      padding: 0 16px;
      border: none;
      border-radius: var(--ha-border-radius-pill, 9999px);
      background: none;
      font-family: inherit;
      font-size: var(--ha-font-size-m, 14px);
      font-weight: var(--ha-font-weight-medium, 500);
      cursor: pointer;
      outline: none;
    }
    .action:focus-visible {
      box-shadow: 0 0 0 2px var(--accent);
    }
    .action.text {
      color: var(--accent);
    }
    .action.text::before {
      content: "";
      position: absolute;
      inset: 0;
      background: var(--accent);
      opacity: 0;
      transition: opacity 180ms ease-in-out;
    }
    .action.text:hover::before {
      opacity: 0.12;
    }
    .action.filled {
      background: var(--accent);
      color: var(--text-primary-color, #fff);
    }
    .action:disabled {
      cursor: not-allowed;
      opacity: 0.5;
    }

    /* Phones and short screens: a bottom sheet, as Home Assistant's adaptive dialogs. */
    @media (max-width: 870px), (max-height: 500px) {
      dialog {
        width: 100vw;
        max-width: 100vw;
        max-height: 90vh;
        margin: auto 0 0;
        border-radius: var(--ha-border-radius-2xl, 20px) var(--ha-border-radius-2xl, 20px) 0 0;
        padding-bottom: var(--safe-area-inset-bottom, 0px);
      }
      dialog[open] {
        animation-name: sheet-in;
      }
    }
    @keyframes dialog-in {
      from {
        opacity: 0;
        transform: scale(0.96);
      }
    }
    @keyframes sheet-in {
      from {
        transform: translateY(100%);
      }
    }
    @media (prefers-reduced-motion: reduce) {
      dialog[open] {
        animation: none;
      }
    }
  `;
}

defineElement("thor-wallbox-booking", ThorWallboxBooking);

declare global {
  interface HTMLElementTagNameMap {
    "thor-wallbox-booking": ThorWallboxBooking;
  }
}
