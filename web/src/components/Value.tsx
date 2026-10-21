import { Fragment } from "react";

export function fmt(v: unknown): string {
  if (typeof v === "number") {
    if (Number.isInteger(v)) return String(v);
    return Math.abs(v) >= 1e4 || (v !== 0 && Math.abs(v) < 1e-3) ? v.toExponential(2) : String(+v.toPrecision(4));
  }
  if (v === null || v === undefined) return "–";
  if (typeof v === "boolean") return v ? "yes" : "no";
  return String(v);
}

const isRecord = (x: unknown): x is Record<string, unknown> => !!x && typeof x === "object" && !Array.isArray(x);

/** Any tool output: numbers rounded for reading, lists of records as tables, records as key–value lists. */
export default function Value({ v }: { v: unknown }) {
  if (Array.isArray(v) && v.length > 0 && v.every(isRecord)) {
    const cols = Array.from(new Set(v.flatMap((row) => Object.keys(row))));
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              {cols.map((c) => <th key={c} className="px-2 py-1 font-medium">{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {v.map((row, i) => (
              <tr key={i} className="border-b border-slate-100 align-top">
                {cols.map((c) => <td key={c} className="px-2 py-1 tabular-nums"><Value v={row[c]} /></td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  if (Array.isArray(v)) return <span className="tabular-nums">{v.map(fmt).join(", ")}</span>;
  if (isRecord(v)) {
    return (
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-xs">
        {Object.entries(v).map(([k, x]) => (
          <Fragment key={k}>
            <dt className="text-slate-500">{k}</dt>
            <dd className="min-w-0 break-words tabular-nums text-slate-800"><Value v={x} /></dd>
          </Fragment>
        ))}
      </dl>
    );
  }
  return <span className="tabular-nums">{fmt(v)}</span>;
}
