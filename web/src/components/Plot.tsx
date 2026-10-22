"use client";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { ArrowsOut } from "@phosphor-icons/react";
import { fmt } from "@/components/Value";

export type Series = { key: string; label: string; y: (number | null)[]; x?: number[]; color: string; width?: number; dash?: string };
export type Band = { lo: (number | null)[]; hi: (number | null)[]; color: string; label: string };
type Props = {
  x: number[]; series: Series[]; band?: Band; diff?: { y: (number | null)[]; label: string };
  xLabel: string; yLabel: string; ticks?: number[]; window?: [number, number] | null; height?: number; ariaLabel: string;
  domain?: [number, number]; onDomain?: (d: [number, number] | undefined) => void;  // shared zoom between linked plots
};

const PAD = { l: 64, r: 12, t: 10, b: 34 };
const tick = (v: number) => (Math.abs(v) >= 1e4 ? `${fmt(v / 1000)}k` : fmt(v));

function niceTicks(lo: number, hi: number, n = 5): number[] {
  const span = hi - lo || 1, raw = span / n, mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * mag).find((s) => span / s <= n) ?? 10 * mag;
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(+v.toPrecision(12));
  return out;
}

const nearest = (xs: number[], v: number) => {  // xs ascending
  let a = 0, b = xs.length - 1;
  while (b - a > 1) { const m = (a + b) >> 1; if (xs[m] < v) a = m; else b = m; }
  return Math.abs(xs[a] - v) <= Math.abs(xs[b] - v) ? a : b;
};

function path(xs: number[], ys: (number | null)[], sx: (v: number) => number, sy: (v: number) => number, x0: number, x1: number) {
  let d = "", pen = false;
  for (let i = 0; i < xs.length; i++) {
    const y = ys[i];
    if (y == null || xs[i] < x0 || xs[i] > x1) { pen = false; continue; }
    d += `${pen ? "L" : "M"}${sx(xs[i]).toFixed(1)},${sy(y).toFixed(1)}`;
    pen = true;
  }
  return d;
}

/** Spectra as thin lines with drag-to-zoom (double-click resets), a crosshair readout of every series, an optional
 * difference panel sharing the x range, reflection ticks and a shaded fit window. */
export default function Plot({ x, series, band, diff, xLabel, yLabel, ticks, window: win, height = 260, ariaLabel, domain, onDomain }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const clip = useId();
  const [w, setW] = useState(640);
  const [own, setOwn] = useState<[number, number]>();
  const [hover, setHover] = useState<number>();
  const [drag, setDrag] = useState<[number, number]>();
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setW(Math.max(280, e.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const full: [number, number] = [x[0], x[x.length - 1]];
  const [x0, x1] = domain ?? own ?? full;
  const setDomain = (d?: [number, number]) => (onDomain ? onDomain(d) : setOwn(d));
  const iw = w - PAD.l - PAD.r, ih = height - PAD.t - 8, base = PAD.t + ih;
  const dTop = base + 10, dh = diff ? 76 : 0, axisY = diff ? dTop + dh : base, total = axisY + PAD.b;
  const sx = (v: number) => PAD.l + ((v - x0) / (x1 - x0)) * iw;
  const inv = (px: number) => x0 + ((px - PAD.l) / iw) * (x1 - x0);

  const scale = (ys: (number | null)[][], xs: number[][]) => {
    let lo = Infinity, hi = -Infinity;
    ys.forEach((arr, j) => arr.forEach((v, i) => { const xv = xs[j][i]; if (v != null && xv >= x0 && xv <= x1) { lo = Math.min(lo, v); hi = Math.max(hi, v); } }));
    if (!isFinite(lo)) [lo, hi] = [0, 1];
    const pad = (hi - lo || Math.abs(hi) || 1) * 0.06;
    return [lo - pad, hi + pad] as const;
  };
  const [y0, y1] = useMemo(() => scale([...series.map((s) => s.y), ...(band ? [band.lo, band.hi] : [])], [...series.map((s) => s.x ?? x), ...(band ? [x, x] : [])]),
    [series, band, x, x0, x1]); // eslint-disable-line react-hooks/exhaustive-deps
  const sy = (v: number) => PAD.t + (1 - (v - y0) / (y1 - y0)) * ih;
  const [d0, d1] = useMemo(() => (diff ? scale([diff.y], [x]) : [0, 1]), [diff, x, x0, x1]); // eslint-disable-line react-hooks/exhaustive-deps
  const sd = (v: number) => dTop + (1 - (v - d0) / (d1 - d0)) * dh;

  const paths = useMemo(() => series.map((s) => path(s.x ?? x, s.y, sx, sy, x0, x1)), [series, x, x0, x1, y0, y1, w]); // eslint-disable-line react-hooks/exhaustive-deps
  const bandPath = useMemo(() => {
    if (!band) return "";
    const idx = x.map((_, i) => i).filter((i) => x[i] >= x0 && x[i] <= x1 && band.lo[i] != null && band.hi[i] != null);
    if (!idx.length) return "";
    return `M${idx.map((i) => `${sx(x[i]).toFixed(1)},${sy(band.hi[i]!).toFixed(1)}`).join("L")}L${idx.reverse().map((i) => `${sx(x[i]).toFixed(1)},${sy(band.lo[i]!).toFixed(1)}`).join("L")}Z`;
  }, [band, x, x0, x1, y0, y1, w]); // eslint-disable-line react-hooks/exhaustive-deps
  const diffPath = useMemo(() => (diff ? path(x, diff.y, sx, sd, x0, x1) : ""), [diff, x, x0, x1, d0, d1, w]); // eslint-disable-line react-hooks/exhaustive-deps

  const px = (e: React.PointerEvent) => e.clientX - (box.current?.getBoundingClientRect().left ?? 0);
  const hx = hover == null ? undefined : inv(hover);
  const readout = hx == null ? [] : series.map((s) => { const xs = s.x ?? x, i = nearest(xs, hx); return { s, v: s.y[i], xv: xs[i] }; });
  const zoomed = !!(domain ?? own);

  return (
    <div ref={box} className="relative w-full min-w-0 select-none">
      <svg width={w} height={total} role="img" aria-label={ariaLabel} className="block max-w-full touch-pan-y"
        onPointerMove={(e) => { const p = px(e); setHover(p >= PAD.l && p <= PAD.l + iw ? p : undefined); if (drag) setDrag([drag[0], p]); }}
        onPointerLeave={() => { setHover(undefined); setDrag(undefined); }}
        onPointerDown={(e) => { const p = px(e); if (p >= PAD.l) setDrag([p, p]); }}
        onPointerUp={() => {
          if (drag && Math.abs(drag[1] - drag[0]) > 6) {
            const [a, b] = [inv(Math.min(...drag)), inv(Math.max(...drag))];
            setDomain([Math.max(a, full[0]), Math.min(b, full[1])]);
          }
          setDrag(undefined);
        }}
        onDoubleClick={() => setDomain(undefined)}>
        {niceTicks(y0, y1).map((t) => (
          <g key={`y${t}`}>
            <line x1={PAD.l} x2={PAD.l + iw} y1={sy(t)} y2={sy(t)} stroke="var(--border-soft)" strokeWidth={1} />
            <text x={PAD.l - 6} y={sy(t)} dy="0.32em" textAnchor="end" className="fill-meta text-[11px] tabular-nums">{tick(t)}</text>
          </g>
        ))}
        {niceTicks(x0, x1, Math.max(3, Math.round(iw / 90))).map((t) => (
          <text key={`x${t}`} x={sx(t)} y={axisY + 16} textAnchor="middle" className="fill-meta text-[11px] tabular-nums">{fmt(t)}</text>
        ))}
        <text x={PAD.l + iw / 2} y={axisY + 30} textAnchor="middle" className="fill-muted text-[11px]">{xLabel}</text>
        <text transform={`translate(11 ${PAD.t + ih / 2}) rotate(-90)`} textAnchor="middle" className="fill-muted text-[11px]">{yLabel}</text>
        {win ? <rect x={sx(Math.max(win[0], x0))} y={PAD.t} width={Math.max(0, sx(Math.min(win[1], x1)) - sx(Math.max(win[0], x0)))} height={ih} fill="var(--surface-warm)" opacity={0.6} /> : null}
        <clipPath id={clip}><rect x={PAD.l} y={0} width={iw} height={total} /></clipPath>
        <g clipPath={`url(#${clip})`}>
          {bandPath ? <path d={bandPath} fill={band!.color} opacity={0.18} /> : null}
          {series.map((s, i) => <path key={s.key} d={paths[i]} fill="none" stroke={s.color} strokeWidth={s.width ?? 1.5} strokeDasharray={s.dash} strokeLinejoin="round" />)}
          {ticks?.filter((t) => t >= x0 && t <= x1).map((t) => <line key={`t${t}`} x1={sx(t)} x2={sx(t)} y1={base - 10} y2={base} stroke="var(--series-2)" strokeWidth={1.5} />)}
          {diff ? (
            <>
              <line x1={PAD.l} x2={PAD.l + iw} y1={sd(0)} y2={sd(0)} stroke="var(--border-soft)" />
              <path d={diffPath} fill="none" stroke="var(--muted)" strokeWidth={1} />
            </>
          ) : null}
          {drag ? <rect x={Math.min(...drag)} y={PAD.t} width={Math.abs(drag[1] - drag[0])} height={axisY - PAD.t} fill="var(--accent)" opacity={0.08} /> : null}
          {hover != null ? <line x1={hover} x2={hover} y1={PAD.t} y2={axisY} stroke="var(--meta)" strokeWidth={1} /> : null}
        </g>
        <line x1={PAD.l} x2={PAD.l + iw} y1={axisY} y2={axisY} stroke="var(--meta)" strokeWidth={1} />
        {diff ? <text x={PAD.l + 6} y={dTop + 10} className="fill-meta text-[11px]">{diff.label}</text> : null}
      </svg>

      <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 pl-16 text-xs text-muted">
        {series.map((s) => (
          <span key={s.key} className="inline-flex items-center gap-1.5">
            <svg width="16" height="8" aria-hidden><line x1="0" x2="16" y1="4" y2="4" stroke={s.color} strokeWidth={2} strokeDasharray={s.dash} /></svg>{s.label}
          </span>
        ))}
        {band ? <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-4 rounded-[2px]" style={{ background: band.color, opacity: 0.25 }} aria-hidden />{band.label}</span> : null}
        {ticks?.length ? <span className="inline-flex items-center gap-1.5"><svg width="8" height="10" aria-hidden><line x1="4" x2="4" y1="0" y2="10" stroke="var(--series-2)" strokeWidth={2} /></svg>reflections</span> : null}
        <span className="ml-auto text-meta">{zoomed ? "" : "Drag to zoom"}</span>
        {zoomed ? <button onClick={() => setDomain(undefined)} className="btn btn-ghost py-0.5 text-xs"><ArrowsOut size={12} weight="bold" aria-hidden />Reset zoom</button> : null}
      </div>

      {hx != null && readout.length ? (
        <div className="pointer-events-none absolute top-2 z-10 rounded-sm bg-surface px-2.5 py-1.5 text-xs shadow-raised ring-1 ring-line"
          style={hover! > w / 2 ? { right: w - hover! + 12 } : { left: hover! + 12 }}>
          <div className="font-medium tabular-nums text-fg">{xLabel.split(" (")[0]} {fmt(readout[0].xv)}</div>
          {readout.map(({ s, v }) => (
            <div key={s.key} className="flex items-center gap-1.5 text-muted">
              <span className="h-0.5 w-3" style={{ background: s.color }} aria-hidden /><span className="font-medium tabular-nums text-fg">{v == null ? "n/a" : fmt(v)}</span>{s.label}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
