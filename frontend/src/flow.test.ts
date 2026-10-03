import assert from "node:assert/strict";
import { describe, test } from "node:test";
import { computeFlow, type Flow, type FlowInput } from "./flow";

// Power in W. The wallbox is idle and the home sensor measures it, unless a test says otherwise.
function flow(fields: Partial<FlowInput>): Flow {
  return computeFlow({ wallbox: 0, charging: false, homeIncludesWallbox: true, ...fields });
}

function split({ fromSolar, fromBattery, fromGrid }: Flow) {
  return { fromSolar, fromBattery, fromGrid };
}

describe("surplus", () => {
  test("is the power going to the grid, net of the import", () => {
    assert.equal(flow({ gridImport: 0, gridExport: 500 }).surplus, 500);
    assert.equal(flow({ gridImport: 300, gridExport: 0 }).surplus, 0);
    // Meters read at slightly different times.
    assert.equal(flow({ gridImport: 300, gridExport: 800 }).surplus, 500);
  });

  test("with the export sensor, leaves out what a charging battery takes", () => {
    const result = flow({ solar: 4000, home: 1000, gridImport: 0, gridExport: 500, battery: -2500 });
    assert.equal(result.surplus, 500);
  });

  test("without the export sensor, is solar minus the rest of the home and the battery charge", () => {
    assert.equal(flow({ solar: 4000, home: 1000 }).surplus, 3000);
    assert.equal(flow({ solar: 4000, home: 1000, battery: -2500 }).surplus, 500);
    assert.equal(flow({ solar: 1000, home: 1500 }).surplus, 0);
  });

  test("leaves the wallbox out of a home sensor that measures it", () => {
    assert.equal(flow({ wallbox: 2800, solar: 4000, home: 3800 }).surplus, 3000);
    assert.equal(flow({ wallbox: 2800, solar: 4000, home: 1000, homeIncludesWallbox: false }).surplus, 3000);
  });

  test("is unknown without the export sensor and without solar or home", () => {
    assert.equal(flow({ gridImport: 500 }).surplus, undefined);
    assert.equal(flow({ solar: 4000 }).surplus, undefined);
  });
});

describe("charging power", () => {
  test("serves the rest of the home first, from solar, then the battery, then the grid", () => {
    const result = flow({
      wallbox: 7192,
      charging: true,
      solar: 2500,
      home: 8492,
      gridImport: 3492,
      gridExport: 0,
      battery: 2500,
    });
    assert.deepEqual(split(result), { fromSolar: 1200, fromBattery: 2500, fromGrid: 3492 });
  });

  test("at night comes from the battery and the grid", () => {
    const result = flow({ wallbox: 7200, charging: true, solar: 0, home: 7500, gridImport: 5800, battery: 1700 });
    assert.deepEqual(split(result), { fromSolar: 0, fromBattery: 1400, fromGrid: 5800 });
  });

  test("gets the solar left by the battery, the grid export and the rest of the home", () => {
    const result = flow({
      wallbox: 1400,
      charging: true,
      solar: 4000,
      home: 2400,
      gridImport: 0,
      gridExport: 600,
      battery: -1000,
    });
    assert.deepEqual(split(result), { fromSolar: 1400, fromBattery: 0, fromGrid: 0 });
  });

  test("works out the rest of the home from the meters without a home sensor", () => {
    // Rest of the home: 4000 solar - 300 export - 2800 wallbox = 900.
    const result = flow({ wallbox: 2800, charging: true, solar: 4000, gridImport: 0, gridExport: 300 });
    assert.deepEqual(split(result), { fromSolar: 2800, fromBattery: 0, fromGrid: 0 });
  });

  test("takes from the grid no more than the grid import", () => {
    assert.deepEqual(split(flow({ wallbox: 7000, charging: true, gridImport: 2000 })), {
      fromSolar: 0,
      fromBattery: 0,
      fromGrid: 2000,
    });
  });

  test("comes from the grid when no source is known", () => {
    assert.deepEqual(split(flow({ wallbox: 7000, charging: true })), { fromSolar: 0, fromBattery: 0, fromGrid: 7000 });
  });

  test("is not split while the wallbox is not charging", () => {
    const result = flow({ wallbox: 2000, solar: 4000, home: 3000, gridImport: 0, battery: 1000 });
    assert.deepEqual(split(result), { fromSolar: 0, fromBattery: 0, fromGrid: 0 });
  });
});

describe("home battery", () => {
  test("splits its power into charging and discharging", () => {
    const charging = flow({ battery: -2600 });
    assert.equal(charging.batteryCharging, 2600);
    assert.equal(charging.batteryDischarging, 0);
    const discharging = flow({ battery: 1700 });
    assert.equal(discharging.batteryCharging, 0);
    assert.equal(discharging.batteryDischarging, 1700);
  });

  test("charges from solar first, except what goes to the grid", () => {
    assert.equal(flow({ solar: 3800, gridExport: 300, battery: -2600 }).batteryFromSolar, 2600);
    assert.equal(flow({ solar: 1500, gridExport: 0, battery: -2600 }).batteryFromSolar, 1500);
  });

  test("charging from the grid at night takes no solar", () => {
    assert.equal(flow({ solar: 0, gridImport: 2000, battery: -2000 }).batteryFromSolar, 0);
  });
});
