import { useId } from "react";
import { label } from "../lib/labels";
const positions: Record<string, [number, number]> = {
  draft: [90, 180],
  pilot: [290, 180],
  active: [520, 80],
  review: [520, 285],
  paused: [760, 80],
  retired: [760, 285],
};
export function LifecycleGraph({
  edges,
  current,
}: {
  edges: { from: string; to: string }[];
  current: string;
}) {
  const marker = useId().replaceAll(":", "");
  return (
    <div className="lifecycle-graph">
      <svg
        viewBox="0 0 880 415"
        role="img"
        aria-label="Máquina de estados do lifecycle: transições permitidas"
      >
        <defs>
          <marker
            id={marker}
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--edge)" />
          </marker>
        </defs>
        {edges.map((e) => {
          const [x, y] = positions[e.from],
            [tx, ty] = positions[e.to];
          const reverse = tx < x || (tx === x && ty < y);
          const sx = x + (tx > x ? 67 : tx < x ? -67 : reverse ? 20 : -20),
            sy = y + (tx === x ? (ty > y ? 31 : -31) : 0);
          const ex = tx + (tx > x ? -70 : tx < x ? 70 : reverse ? 20 : -20),
            ey = ty + (tx === x ? (ty > y ? -34 : 34) : 0);
          const bend = reverse ? -65 : 0;
          return (
            <path
              key={e.from + e.to}
              data-transition={`${e.from}-${e.to}`}
              d={
                tx === x
                  ? `M ${sx} ${sy} L ${ex} ${ey}`
                  : `M ${sx} ${sy} C ${sx + (ex - sx) / 2} ${sy + bend}, ${sx + (ex - sx) / 2} ${ey + bend}, ${ex} ${ey}`
              }
              fill="none"
              stroke="var(--edge)"
              strokeWidth="1.8"
              markerEnd={`url(#${marker})`}
            />
          );
        })}
        {Object.entries(positions).map(([s, [x, y]]) => (
          <g
            key={s}
            data-state={s}
            data-current={s === current}
            className={s === current ? "state-current" : "state-possible"}
          >
            <rect x={x - 66} y={y - 30} width="132" height="60" rx="10" />
            <text x={x} y={y - 1} textAnchor="middle">
              {label(s)}
            </text>
            <text
              className="state-caption"
              x={x}
              y={y + 18}
              textAnchor="middle"
            >
              {s === current
                ? "ESTADO ATUAL"
                : s === "retired"
                  ? "TERMINAL"
                  : ""}
            </text>
          </g>
        ))}
        <text x="25" y="398" className="graph-legend">
          Setas: transições permitidas pelo contrato · Estado destacado:
          cadastro atual · Nenhuma transição executada
        </text>
      </svg>
    </div>
  );
}
