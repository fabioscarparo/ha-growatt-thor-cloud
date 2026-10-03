import { css } from "lit";

// Home Assistant's tile card, badges, alerts, energy distribution circles and
// card features, through the theme's variables.
export const cardStyles = css`
  :host {
    --tile-color: var(--state-inactive-color, #9e9e9e);
  }
  ha-card {
    height: 100%;
    overflow: hidden;
  }
  svg {
    display: block;
    flex: none;
    fill: currentColor;
  }
  .message {
    padding: 16px;
    color: var(--secondary-text-color);
  }

  .tile {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 64px;
    padding: 8px 16px 0;
    box-sizing: border-box;
    cursor: pointer;
    outline: none;
    border-radius: var(--ha-card-border-radius, 12px);
  }
  .tile:focus-visible {
    box-shadow: inset 0 0 0 2px var(--tile-color);
  }
  .tile-icon {
    position: relative;
    flex: none;
    width: 36px;
    height: 36px;
  }
  .tile-icon .shape {
    position: relative;
    width: 36px;
    height: 36px;
    border-radius: 18px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--tile-color);
  }
  .tile-icon .shape::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--tile-color);
    opacity: 0.2;
  }
  .tile-icon .shape svg {
    position: relative;
  }
  .tile-badge {
    position: absolute;
    top: -3px;
    right: -3px;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--mode-color, var(--primary-color));
    color: var(--white-color, #fff);
  }
  .tile-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .primary,
  .secondary {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--primary-text-color);
  }
  .primary {
    font-size: var(--ha-font-size-m, 14px);
    font-weight: var(--ha-font-weight-medium, 500);
    line-height: var(--ha-line-height-normal, 1.6);
    letter-spacing: 0.1px;
  }
  .secondary {
    font-size: var(--ha-font-size-s, 12px);
    line-height: var(--ha-line-height-condensed, 1.2);
    letter-spacing: 0.4px;
  }

  .value {
    display: flex;
    align-items: baseline;
    gap: 4px;
    padding: 0 16px 16px;
    line-height: var(--ha-line-height-condensed, 1.2);
  }
  .value .number {
    font-size: var(--ha-font-size-3xl, 28px);
  }
  .value .unit {
    font-size: var(--ha-font-size-l, 16px);
    color: var(--secondary-text-color);
  }

  .alert {
    position: relative;
    display: flex;
    margin: 0 16px 16px;
    padding: 12px;
    border-radius: var(--ha-border-radius-lg, 12px);
    overflow: hidden;
  }
  .alert::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--alert-color);
    opacity: 0.12;
  }
  .alert svg {
    position: relative;
    color: var(--alert-color);
  }
  .alert .text {
    position: relative;
    margin-inline: 8px;
    line-height: normal;
    color: var(--primary-text-color);
  }
  .alert .title {
    margin-top: 2px;
    font-weight: var(--ha-font-weight-bold, 700);
  }

  .flow {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 0 16px 16px;
  }
  .flow .row {
    display: flex;
    align-items: flex-start;
    justify-content: center;
  }
  .node {
    flex: none;
    width: 80px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .node .label {
    height: 20px;
    max-width: 80px;
    font-size: var(--ha-font-size-s, 12px);
    color: var(--secondary-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .node .circle {
    width: 80px;
    height: 80px;
    box-sizing: border-box;
    border: 2px solid var(--node-color);
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    font-size: var(--ha-font-size-s, 12px);
    line-height: 12px;
    text-align: center;
    color: var(--primary-text-color);
  }
  .node.solar {
    --node-color: var(--energy-solar-color, #ff9800);
  }
  .node.grid {
    --node-color: var(--energy-grid-consumption-color, #488fc2);
  }
  .node.wallbox {
    --node-color: var(--tile-color);
  }
  /* Centred on the circles, below their 20px label. */
  .line {
    flex: 1;
    max-width: 120px;
    display: flex;
    align-items: center;
    height: 6px;
    margin-top: 57px;
    color: var(--disabled-color, #bdbdbd);
    opacity: 0.5;
  }
  .line.active {
    opacity: 1;
  }
  .line.solar.active {
    color: var(--energy-solar-color, #ff9800);
  }
  .line.grid.active {
    color: var(--energy-grid-consumption-color, #488fc2);
  }
  .line .track {
    position: relative;
    flex: 1;
    height: 1px;
    background: currentColor;
  }
  /* Runs towards the wallbox, faster as more power flows. */
  .line .dot {
    position: absolute;
    top: -2px;
    left: 0;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: currentColor;
    animation: flow var(--flow-duration, 3s) linear infinite;
  }
  .line.reverse .dot {
    animation-direction: reverse;
  }
  @keyframes flow {
    from {
      left: 0;
    }
    to {
      left: calc(100% - 5px);
    }
  }
  .node.spacer,
  .line.spacer {
    visibility: hidden;
  }
  .circle .import,
  .circle .export,
  .circle .charging,
  .circle .discharging {
    display: flex;
    align-items: center;
    gap: 2px;
  }
  .circle .import svg {
    color: var(--energy-grid-consumption-color, #488fc2);
  }
  .circle .export svg {
    color: var(--energy-grid-return-color, #8353d1);
  }
  .circle .charging svg {
    color: var(--energy-battery-in-color, #f06292);
  }
  .circle .discharging svg {
    color: var(--energy-battery-out-color, #4db6ac);
  }

  /* The home battery below the wallbox, its label underneath. */
  .node.battery {
    --node-color: var(--energy-battery-out-color, #4db6ac);
    align-self: center;
    margin-top: 20px;
  }
  .node.battery .label {
    margin-top: 4px;
  }
  /* The battery's links, drawn over the flow once the circles are laid out. */
  .links {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    overflow: visible;
    pointer-events: none;
  }
  .link {
    color: var(--disabled-color, #bdbdbd);
    opacity: 0.5;
  }
  .link path {
    fill: none;
    stroke: currentColor;
    stroke-width: 1;
  }
  .link circle {
    fill: currentColor;
  }
  .link.active {
    opacity: 1;
  }
  .link.battery-out.active {
    color: var(--energy-battery-out-color, #4db6ac);
  }
  .link.battery-in.active {
    color: var(--energy-battery-in-color, #f06292);
  }

  @media (prefers-reduced-motion: reduce) {
    .line .dot {
      animation: none;
      left: calc(50% - 2.5px);
    }
  }
  .flow .note,
  .note {
    margin: 0;
    font-size: var(--ha-font-size-s, 12px);
    line-height: 1.4;
    color: var(--secondary-text-color);
  }

  .badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0 16px 16px;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    height: 36px;
    min-width: 36px;
    box-sizing: border-box;
    padding: 0 12px;
    border-width: var(--ha-card-border-width, 1px);
    border-style: solid;
    border-color: var(--ha-card-border-color, var(--divider-color, #e0e0e0));
    border-radius: 18px;
    background: var(--ha-card-background, var(--card-background-color, #fff));
  }
  .badge svg {
    margin-inline-start: -4px;
    color: var(--badge-color, var(--secondary-text-color));
  }
  .badge .info {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  .badge .label {
    font-size: var(--ha-font-size-xs, 10px);
    font-weight: var(--ha-font-weight-medium, 500);
    line-height: 10px;
    letter-spacing: 0.1px;
    color: var(--secondary-text-color);
  }
  .badge .content {
    font-size: var(--ha-font-size-s, 12px);
    font-weight: var(--ha-font-weight-medium, 500);
    line-height: var(--ha-line-height-condensed, 1.2);
    letter-spacing: 0.1px;
    color: var(--primary-text-color);
  }

  .features {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 0 16px 16px;
  }
  .progress .caption {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 0 4px 4px;
    font-size: var(--ha-font-size-s, 12px);
    line-height: var(--ha-line-height-condensed, 1.2);
    letter-spacing: 0.4px;
    color: var(--primary-text-color);
  }
  .progress .caption .pct {
    font-weight: var(--ha-font-weight-medium, 500);
  }
  .bar {
    display: flex;
    height: 42px;
    border-radius: var(--ha-card-features-border-radius, 12px);
    overflow: hidden;
  }
  .bar .done {
    background: var(--tile-color);
  }
  .bar .rest {
    flex: 1;
    background: var(--tile-color);
    opacity: 0.2;
  }
  .buttons {
    display: flex;
    gap: 12px;
  }
  .button {
    position: relative;
    overflow: hidden;
    z-index: 0;
    flex: 1 1 0;
    min-width: 0;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 0 8px;
    border: none;
    border-radius: var(--ha-card-features-border-radius, 12px);
    background: none;
    font-family: inherit;
    font-size: var(--ha-font-size-m, 14px);
    font-weight: var(--ha-font-weight-medium, 500);
    color: var(--primary-text-color);
    cursor: pointer;
    outline: none;
  }
  .button::before,
  .select::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--disabled-color, #bdbdbd);
    opacity: 0.2;
    transition: opacity 180ms ease-in-out;
    pointer-events: none;
  }
  .button:hover:not(:disabled)::before,
  .select:not(.disabled):hover::before {
    opacity: 0.3;
  }
  .button:focus-visible,
  .select:focus-within {
    box-shadow: 0 0 0 2px var(--tile-color);
  }
  .button:disabled {
    cursor: not-allowed;
    color: var(--disabled-text-color, #bdbdbd);
  }
  .button svg,
  .button span {
    position: relative;
  }
  .button span {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .select {
    position: relative;
    overflow: hidden;
    height: 42px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 10px;
    box-sizing: border-box;
    border-radius: var(--ha-card-features-border-radius, 12px);
    letter-spacing: 0.25px;
    color: var(--primary-text-color);
  }
  .select.disabled {
    color: var(--disabled-color, #bdbdbd);
  }
  .select svg,
  .select .content {
    position: relative;
  }
  .select .content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    line-height: var(--ha-line-height-condensed, 1.2);
  }
  .select .label {
    font-size: var(--ha-font-size-s, 12px);
    letter-spacing: 0.4px;
  }
  .select .current {
    font-size: var(--ha-font-size-m, 14px);
  }
  .select select {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    margin: 0;
    opacity: 0;
    cursor: pointer;
    font-size: 16px;
  }
  .select select:disabled {
    cursor: not-allowed;
  }
  .features .note {
    padding: 0 4px;
  }
`;
