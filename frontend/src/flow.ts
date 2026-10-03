/** Power around the wallbox, in W; undefined where no sensor is set. */
export interface FlowInput {
  wallbox: number;
  charging: boolean;
  solar?: number;
  gridImport?: number;
  gridExport?: number;
  home?: number;
  homeIncludesWallbox: boolean;
  /** Positive while the battery discharges, negative while it charges. */
  battery?: number;
}

export interface Flow {
  fromSolar: number;
  fromBattery: number;
  fromGrid: number;
  /** Power the wallbox could take in PV Linkage; undefined when it cannot be worked out. */
  surplus?: number;
  batteryCharging: number;
  batteryDischarging: number;
  /** The part of the battery's charge that comes from solar. */
  batteryFromSolar: number;
}

/**
 * Where the wallbox's power comes from, and the surplus it could use.
 *
 * In PV Linkage the wallbox reads the grid meter: only power that would leave the
 * home is surplus, so a charging home battery takes it first. While the wallbox
 * charges, the rest of the home is served first, from solar, then the battery, then
 * the grid; the wallbox gets what is left of each. A charging battery takes its
 * share of solar before the home.
 */
export function computeFlow(input: FlowInput): Flow {
  const batteryDischarging = Math.max(0, input.battery ?? 0);
  const batteryCharging = Math.max(0, -(input.battery ?? 0));

  // The rest of the home, without the wallbox: from its sensor, else from the meters.
  let rest: number | undefined;
  if (input.home !== undefined) {
    rest = Math.max(0, input.home - (input.homeIncludesWallbox ? input.wallbox : 0));
  } else if (input.solar !== undefined && input.gridImport !== undefined && input.gridExport !== undefined) {
    rest = Math.max(
      0,
      input.solar + input.gridImport + batteryDischarging - input.gridExport - batteryCharging - input.wallbox,
    );
  }

  let surplus: number | undefined;
  if (input.gridExport !== undefined) {
    surplus = Math.max(0, input.gridExport - (input.gridImport ?? 0));
  } else if (input.solar !== undefined && rest !== undefined) {
    surplus = Math.max(0, input.solar - rest - batteryCharging);
  }

  let fromSolar = 0;
  let fromBattery = 0;
  let fromGrid = 0;
  if (input.charging) {
    // Solar used in the home, once the battery and the grid have taken theirs.
    const solarInHome = Math.max(0, (input.solar ?? 0) - batteryCharging - (input.gridExport ?? 0));
    let needed = rest ?? 0;
    const solarToRest = Math.min(needed, solarInHome);
    needed -= solarToRest;
    fromSolar = Math.min(input.wallbox, solarInHome - solarToRest);
    const batteryToRest = Math.min(needed, batteryDischarging);
    fromBattery = Math.min(input.wallbox - fromSolar, batteryDischarging - batteryToRest);
    fromGrid = Math.max(0, input.wallbox - fromSolar - fromBattery);
    if (input.gridImport !== undefined) {
      fromGrid = Math.min(fromGrid, input.gridImport);
    }
  }

  const batteryFromSolar = Math.min(batteryCharging, Math.max(0, (input.solar ?? 0) - (input.gridExport ?? 0)));
  return { fromSolar, fromBattery, fromGrid, surplus, batteryCharging, batteryDischarging, batteryFromSolar };
}
