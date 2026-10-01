// Bundles the card into the integration, which serves it to the frontend.
import { readFile } from "node:fs/promises";
import { build } from "esbuild";

const { version } = JSON.parse(await readFile("package.json", "utf8"));

await build({
  entryPoints: ["src/thor-wallbox-card.ts"],
  outfile: "../custom_components/growatt_thor_cloud/frontend/thor-wallbox-card.js",
  bundle: true,
  format: "esm",
  target: "es2021",
  minify: true,
  define: { __CARD_VERSION__: JSON.stringify(version) },
  logLevel: "info",
});
