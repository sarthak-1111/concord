/** The 118 elements in order of atomic number (symbols and names from pymatgen). */
export const SYMBOLS = "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split(" ");
export const NAMES = "Hydrogen|Helium|Lithium|Beryllium|Boron|Carbon|Nitrogen|Oxygen|Fluorine|Neon|Sodium|Magnesium|Aluminum|Silicon|Phosphorus|Sulfur|Chlorine|Argon|Potassium|Calcium|Scandium|Titanium|Vanadium|Chromium|Manganese|Iron|Cobalt|Nickel|Copper|Zinc|Gallium|Germanium|Arsenic|Selenium|Bromine|Krypton|Rubidium|Strontium|Yttrium|Zirconium|Niobium|Molybdenum|Technetium|Ruthenium|Rhodium|Palladium|Silver|Cadmium|Indium|Tin|Antimony|Tellurium|Iodine|Xenon|Cesium|Barium|Lanthanum|Cerium|Praseodymium|Neodymium|Promethium|Samarium|Europium|Gadolinium|Terbium|Dysprosium|Holmium|Erbium|Thulium|Ytterbium|Lutetium|Hafnium|Tantalum|Tungsten|Rhenium|Osmium|Iridium|Platinum|Gold|Mercury|Thallium|Lead|Bismuth|Polonium|Astatine|Radon|Francium|Radium|Actinium|Thorium|Protactinium|Uranium|Neptunium|Plutonium|Americium|Curium|Berkelium|Californium|Einsteinium|Fermium|Mendelevium|Nobelium|Lawrencium|Rutherfordium|Dubnium|Seaborgium|Bohrium|Hassium|Meitnerium|Darmstadtium|Roentgenium|Copernicium|Nihonium|Flerovium|Moscovium|Livermorium|Tennessine|Oganesson".split("|");

export type Block = "s" | "p" | "d" | "f";
const STARTS = [3, 11, 19, 37, 55, 87];  // first element of periods 2 to 7

/** Grid position (row 1-7, the f-block on rows 9-10; column = group 1-18) of atomic number z. */
export function place(z: number): { row: number; col: number; block: Block } {
  if (z <= 2) return { row: 1, col: z === 1 ? 1 : 18, block: z === 1 ? "s" : "p" };
  const k = STARTS.findLastIndex((s) => z >= s), period = k + 2, i = z - STARTS[k];
  let col: number;
  if (period <= 3) col = i < 2 ? i + 1 : i + 11;
  else if (period <= 5 || i < 2) col = i + 1;
  else if (i <= 16) return { row: period + 3, col: i + 1, block: "f" };  // La-Lu, Ac-Lr
  else col = i - 13;
  return { row: period, col, block: col <= 2 ? "s" : col <= 12 ? "d" : "p" };
}

/** "Pt3Co" → [["Pt", 3], ["Co", 1]]; amounts default to 1. */
export function parseFormula(f: string): [string, number][] {
  return [...f.matchAll(/([A-Z][a-z]?)(\d+(?:\.\d+)?)?/g)].filter((m) => SYMBOLS.includes(m[1])).map((m) => [m[1], m[2] ? +m[2] : 1]);
}

export const formula = (parts: [string, number][]) => parts.map(([s, n]) => s + (n === 1 ? "" : String(n))).join("");
