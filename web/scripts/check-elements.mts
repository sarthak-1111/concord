// Self-check of the periodic table layout and formula helpers: npm run check
import { place, parseFormula, formula, SYMBOLS } from "../src/lib/elements.ts";
const at = (s: string) => place(SYMBOLS.indexOf(s) + 1);
const want: Record<string, [number, number]> = { H: [1, 1], He: [1, 18], B: [2, 13], Ne: [2, 18], Al: [3, 13], K: [4, 1], Ti: [4, 4], Pt: [6, 10], Hf: [6, 4], Rn: [6, 18], La: [9, 3], Lu: [9, 17], Ac: [10, 3], Rf: [7, 4], Og: [7, 18] };
for (const [s, [r, c]] of Object.entries(want)) { const p = at(s); if (p.row !== r || p.col !== c) throw new Error(`${s} at ${p.row},${p.col}`); }
const cells = new Set(SYMBOLS.map((_, i) => { const p = place(i + 1); return `${p.row},${p.col}`; }));
if (cells.size !== 118) throw new Error(`overlap: ${cells.size}`);
if (formula(parseFormula("Pt3Co")) !== "Pt3Co" || formula(parseFormula("Ce0.8Zr0.2O2")) !== "Ce0.8Zr0.2O2") throw new Error("formula");
console.log("ok");
