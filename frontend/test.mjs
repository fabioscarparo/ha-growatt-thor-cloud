// Runs the Wallbox card's unit tests: every src/*.test.ts file.
//
// The tests are TypeScript, which not every supported Node version can run as such. So
// esbuild first compiles them the same way it builds the card (bundled ES modules) into a
// temporary folder, and Node's built-in test runner (node --test) then runs the compiled
// files. The folder is the system's temporary folder on purpose: recent Node versions
// (e.g. 26) read the runner's arguments as glob patterns, and those skip anything inside
// node_modules.
//
// Usage, from frontend/: npm test. The exit status is the test runner's, non-zero when a
// test fails, so CI fails with it.
import { spawnSync } from "node:child_process";
import { mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { build } from "esbuild";

const tests = (await readdir("src")).filter((name) => name.endsWith(".test.ts"));
const out = await mkdtemp(join(tmpdir(), "card-tests-"));
try {
  await build({
    entryPoints: tests.map((name) => `src/${name}`),
    outdir: out,
    // .mjs: Node loads the output as ES modules wherever the folder is.
    outExtension: { ".js": ".mjs" },
    bundle: true,
    format: "esm",
    platform: "node",
    target: "node22",
    logLevel: "warning",
  });
  const run = spawnSync(
    process.execPath,
    ["--test", ...tests.map((name) => join(out, name.replace(/\.ts$/, ".mjs")))],
    { stdio: "inherit" },
  );
  process.exitCode = run.status ?? 1;
} finally {
  await rm(out, { recursive: true, force: true });
}
