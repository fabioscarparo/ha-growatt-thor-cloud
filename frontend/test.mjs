// Runs the card's unit tests (src/*.test.ts): esbuild compiles them as it does the card,
// then Node's test runner runs them.
import { spawnSync } from "node:child_process";
import { readdir, rm } from "node:fs/promises";
import { build } from "esbuild";

const OUT = "node_modules/.cache/card-tests";
const tests = (await readdir("src")).filter((name) => name.endsWith(".test.ts"));

await rm(OUT, { recursive: true, force: true });
await build({
  entryPoints: tests.map((name) => `src/${name}`),
  outdir: OUT,
  outExtension: { ".js": ".mjs" },
  bundle: true,
  format: "esm",
  platform: "node",
  target: "node22",
  logLevel: "warning",
});
const run = spawnSync(
  process.execPath,
  ["--test", ...tests.map((name) => `${OUT}/${name.replace(/\.ts$/, ".mjs")}`)],
  { stdio: "inherit" },
);
process.exit(run.status ?? 1);
