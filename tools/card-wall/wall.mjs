// Builds the Wallbox card images of the README: assets/card/wall-light.svg and
// assets/card/wall-dark.svg.
//
// What an image is
//   A "wall" of nine cards in three columns. Each card is a scenario of cards.html
//   (charging in Fast, PV Linkage and Off-peak, with the home battery, a scheduled start,
//   a fault...), drawn by the card the integration ships. The three columns end at the
//   same height: the spare height of a shorter column is spread over its gaps.
//
// How it is built
//   1. A local web server (127.0.0.1, free port) serves cards.html and the built card.
//   2. Headless Chrome opens every scenario, light and dark, and prints the card to a
//      one-page PDF the size of the card. prefers-reduced-motion is on, so the animated
//      dots of the energy flow stand still, halfway along their lines.
//   3. pdf_to_svg.py (Python, PyMuPDF) turns each PDF into an SVG with the text drawn as
//      paths: GitHub shows the images with <img>, which cannot load web fonts.
//   4. SVGO shrinks each card, the cards are stacked into one SVG per theme, the glyphs
//      and clip paths that every card repeats are kept once, and SVGO shrinks the wall.
//
// Usage, from this folder
//   npm install                 once: installs puppeteer-core and svgo
//   npm run wall                writes the two images into assets/card
//   npm run wall -- <folder>    writes them into <folder> instead, e.g. to compare
//
// Requirements
//   - The card built from the current sources (in frontend/: npm run build).
//   - Google Chrome, found automatically; set CHROME=<path> to use another Chrome.
//   - Python 3 with PyMuPDF (pip install pymupdf); set PYTHON=<path> to use a Python
//     other than python3, e.g. one in a virtual environment.
//   - Internet access: cards.html loads the Roboto font from Google Fonts.

import { execFileSync } from "node:child_process";
import { access, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";
import { optimize } from "svgo";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const ROOT = resolve(HERE, "../..");
// The card as the integration serves it, built by `npm run build` in frontend/.
const CARD = join(ROOT, "custom_components/growatt_thor_cloud/frontend/thor-wallbox-card.js");
// Where the images go: the folder given on the command line, else the README's assets.
const OUT = resolve(process.argv[2] ?? join(ROOT, "assets/card"));

// The wall, column by column, top to bottom: keys of SCENARIOS in cards.html. Each column
// should hold one card with the home battery (the tallest kind), so the columns come out
// of similar height and their gaps stay even.
const COLUMNS = [
  ["charging_fast_limit", "available", "offpeak_charging"],
  ["scheduled", "pv_boost", "pv_waiting"],
  ["pv_grid", "pv_surplus", "faulted"],
];
const THEMES = ["light", "dark"];
// Space between two columns, and between two cards of the tallest column, in pixels.
const GAP = 24;
// SVGO settings, for every card and for the walls: coordinates rounded to two decimals,
// and optimisation passes repeated until the file stops shrinking.
const SVGO = { multipass: true, floatPrecision: 2 };

/**
 * Starts the web server Chrome loads the scenarios from. It serves only the two files the
 * page needs, on 127.0.0.1 and a free port chosen by the system.
 */
async function serve() {
  const files = {
    "/cards.html": [join(HERE, "cards.html"), "text/html; charset=utf-8"],
    "/thor-wallbox-card.js": [CARD, "text/javascript; charset=utf-8"],
  };
  const server = createServer(async (request, response) => {
    const file = files[new URL(request.url, "http://localhost").pathname];
    if (!file) {
      response.writeHead(404).end();
      return;
    }
    const [path, type] = file;
    response.writeHead(200, { "Content-Type": type }).end(await readFile(path));
  });
  await new Promise((listening) => server.listen(0, "127.0.0.1", listening));
  return server;
}

/**
 * Prints every scenario of the wall, in both themes, to <folder>/<scenario>-<theme>.pdf,
 * each PDF one page the size of the card.
 */
async function printCards(origin, folder) {
  await mkdir(folder, { recursive: true });
  const browser = await puppeteer.launch({
    // Without CHROME, puppeteer finds the installed Google Chrome (stable channel).
    ...(process.env.CHROME ? { executablePath: process.env.CHROME } : { channel: "chrome" }),
    args: ["--hide-scrollbars"],
  });
  try {
    const page = await browser.newPage();
    // Larger than any card (440 px wide), so no card wraps or scrolls.
    await page.setViewport({ width: 600, height: 1200, deviceScaleFactor: 1 });
    await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
    for (const scenario of COLUMNS.flat()) {
      for (const theme of THEMES) {
        await page.goto(`${origin}/cards.html?scenario=${scenario}&theme=${theme}&lang=en`, {
          waitUntil: "networkidle0",
        });
        // cards.html sets its title to "ready <width>x<height>" once the card is final.
        await page.waitForFunction(() => document.title.startsWith("ready"), { timeout: 15_000 });
        const [width, height] = (await page.title()).split(" ")[1].split("x").map(Number);
        await page.pdf({
          path: join(folder, `${scenario}-${theme}.pdf`),
          width: `${width}px`,
          height: `${height}px`,
          printBackground: true,
          pageRanges: "1",
          margin: { top: 0, right: 0, bottom: 0, left: 0 },
        });
      }
    }
  } finally {
    await browser.close();
  }
}

/**
 * Splits a card's SVG into its size (CSS pixels), its viewBox and its content. Every id in
 * the content, and every reference to one, gets `prefix`: SVGO names the ids of each card
 * a, b, c..., so without it the cards would clash once they share one file.
 */
function parseCard(svg, prefix) {
  const root = svg.match(/<svg([^>]*)>/);
  const attribute = (name) => root[1].match(new RegExp(`${name}="([^"]+)"`))[1];
  let content = svg.slice(root.index + root[0].length, svg.lastIndexOf("</svg>"));
  content = content
    .replace(/id="([^"]+)"/g, (_, id) => `id="${prefix}${id}"`)
    .replace(/href="#([^"]+)"/g, (_, id) => `href="#${prefix}${id}"`)
    .replace(/url\(#([^)]+)\)/g, (_, id) => `url(#${prefix}${id})`);
  return {
    width: Number(attribute("width")),
    height: Number(attribute("height")),
    viewBox: attribute("viewBox"),
    content,
  };
}

/** A number as a short SVG attribute: at most six significant digits, no trailing zeros. */
function number(value) {
  return String(Number(value.toPrecision(6)));
}

/**
 * Stacks the cards of one theme into one SVG. Each card becomes a nested <svg> placed at
 * its x and y, so its own coordinates stay as they are. The columns sit side by side, GAP
 * apart; the tallest column has GAP between its cards and the others spread their spare
 * height over their gaps, so all columns end at the bottom of the wall.
 */
function composeWall(columns) {
  const heights = columns.map((column) => column.reduce((sum, card) => sum + card.height, 0));
  const wallHeight = Math.max(...heights) + GAP * 2;
  const wallWidth = columns.reduce((sum, column) => sum + column[0].width, 0) + GAP * (columns.length - 1);
  const parts = [];
  let x = 0;
  columns.forEach((column, index) => {
    const gap = (wallHeight - heights[index]) / (column.length - 1);
    let y = 0;
    for (const card of column) {
      parts.push(
        `<svg x="${number(x)}" y="${number(y)}" width="${number(card.width)}" height="${number(card.height)}" ` +
          `viewBox="${card.viewBox}">${card.content}</svg>`,
      );
      y += card.height + gap;
    }
    x += column[0].width + GAP;
  });
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" ' +
    `width="${number(wallWidth)}" height="${number(wallHeight)}" viewBox="0 0 ${number(wallWidth)} ${number(wallHeight)}">` +
    `${parts.join("")}</svg>`
  );
}

/**
 * Keeps one copy of the glyph outlines and clip paths that the cards repeat. The text of
 * nine cards is drawn with the same few dozen glyphs, each a <path id=...> referenced by
 * <use>: identical definitions are dropped, and their references point to the copy kept.
 * Without this step the wall would be several times larger.
 */
function dedupe(svg) {
  const kept = new Map(); // definition (without its id) -> id of the copy kept
  const replaced = new Map(); // id of a dropped copy -> id of the copy kept
  const keep = (id, definition) => {
    if (kept.has(definition)) {
      replaced.set(id, kept.get(definition));
      return false;
    }
    kept.set(definition, id);
    return true;
  };
  return svg
    .replace(/<path id="([^"]+)"([^>]*)\/>/g, (element, id, rest) => (keep(id, `path${rest}`) ? element : ""))
    .replace(/<clipPath id="([^"]+)"([^>]*)>([\s\S]*?)<\/clipPath>/g, (element, id, attributes, content) =>
      keep(id, `clip${attributes}${content}`) ? element : "",
    )
    .replace(/href="#([^"]+)"/g, (_, id) => `href="#${replaced.get(id) ?? id}"`)
    .replace(/url\(#([^)]+)\)/g, (_, id) => `url(#${replaced.get(id) ?? id})`);
}

async function main() {
  // Fail early, with a hint, rather than with a blank card in Chrome.
  await access(CARD).catch(() => {
    throw new Error(`${CARD} is missing: build the card first (in frontend/: npm run build)`);
  });
  const work = await mkdtemp(join(tmpdir(), "card-wall-"));
  const server = await serve();
  try {
    // 1-2. Print every card to a PDF.
    await printCards(`http://127.0.0.1:${server.address().port}`, join(work, "pdf"));
    // 3. PDF to SVG, text as paths.
    execFileSync(process.env.PYTHON ?? "python3", [join(HERE, "pdf_to_svg.py"), join(work, "pdf"), join(work, "svg")], {
      stdio: "inherit",
    });
    // 4. One wall per theme.
    await mkdir(OUT, { recursive: true });
    for (const theme of THEMES) {
      const columns = await Promise.all(
        COLUMNS.map((column, c) =>
          Promise.all(
            column.map(async (scenario, r) => {
              const svg = await readFile(join(work, "svg", `${scenario}-${theme}.svg`), "utf8");
              return parseCard(optimize(svg, SVGO).data, `c${c}${r}`);
            }),
          ),
        ),
      );
      const wall = optimize(dedupe(composeWall(columns)), SVGO).data;
      await writeFile(join(OUT, `wall-${theme}.svg`), wall);
      console.log(`${join(OUT, `wall-${theme}.svg`)}: ${Math.round(wall.length / 1024)} KB`);
    }
  } finally {
    server.close();
    await rm(work, { recursive: true, force: true });
  }
}

await main();
