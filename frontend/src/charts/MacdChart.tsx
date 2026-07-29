import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface MacdPoint {
  date: string;
  macd: number | null;
  signal: number | null;
  histogram: number | null;
}

export const MacdChart = ({ data, height = 170 }: { data: MacdPoint[]; height?: number }) => (
  <ResponsiveContainer width="100%" height={height}>
    <ComposedChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -18 }}>
      <CartesianGrid stroke="var(--border)" strokeDasharray="2 5" vertical={false} />
      <XAxis dataKey="date" hide />
      <YAxis
        width={46}
        tick={{ fill: "var(--text-dim)", fontSize: 11, fontFamily: "var(--font-mono)" }}
        axisLine={false}
        tickLine={false}
      />
      <Tooltip
        contentStyle={{
          background: "var(--panel-raised)",
          border: "1px solid var(--border)",
          borderRadius: 6,
          fontFamily: "var(--font-mono)",
          fontSize: 12,
        }}
        labelStyle={{ color: "var(--text-dim)", marginBottom: 4 }}
      />
      <Bar dataKey="histogram" name="Histogram" fill="var(--accent)" opacity={0.45} isAnimationActive={false} />
      <Line type="monotone" dataKey="macd" name="MACD" stroke="var(--positive)" strokeWidth={1.5} dot={false} isAnimationActive={false} connectNulls />
      <Line type="monotone" dataKey="signal" name="Signal" stroke="var(--negative)" strokeWidth={1.5} dot={false} isAnimationActive={false} connectNulls />
    </ComposedChart>
  </ResponsiveContainer>
);
