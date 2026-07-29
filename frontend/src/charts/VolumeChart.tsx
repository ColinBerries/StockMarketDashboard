import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCompact } from "../lib/format";

interface VolumePoint {
  date: string;
  volume: number | null;
}

export const VolumeChart = ({ data, height = 140 }: { data: VolumePoint[]; height?: number }) => (
  <ResponsiveContainer width="100%" height={height}>
    <BarChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -18 }}>
      <XAxis dataKey="date" hide />
      <YAxis
        width={46}
        tick={{ fill: "var(--text-dim)", fontSize: 11, fontFamily: "var(--font-mono)" }}
        axisLine={false}
        tickLine={false}
        tickFormatter={(value: number) => formatCompact(value)}
      />
      <Tooltip
        contentStyle={{
          background: "var(--panel-raised)",
          border: "1px solid var(--border)",
          borderRadius: 6,
          fontFamily: "var(--font-mono)",
          fontSize: 12,
        }}
        formatter={(value) => formatCompact(typeof value === "number" ? value : Number(value))}
        labelStyle={{ color: "var(--text-dim)", marginBottom: 4 }}
      />
      <Bar dataKey="volume" name="Volume" fill="var(--accent)" opacity={0.55} isAnimationActive={false} />
    </BarChart>
  </ResponsiveContainer>
);
