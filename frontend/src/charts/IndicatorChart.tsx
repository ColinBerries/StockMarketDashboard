import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface LineSeries {
  key: string;
  label: string;
  color: string;
  dashed?: boolean;
}

interface IndicatorChartProps {
  data: Array<Record<string, string | number | null>>;
  series: LineSeries[];
  height?: number;
  referenceLines?: number[];
}

const tooltipStyle = {
  background: "var(--panel-raised)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  fontFamily: "var(--font-mono)",
  fontSize: 12,
  padding: "6px 10px",
};

export const IndicatorChart = ({ data, series, height = 170, referenceLines }: IndicatorChartProps) => (
  <ResponsiveContainer width="100%" height={height}>
    <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -18 }}>
      <CartesianGrid stroke="var(--border)" strokeDasharray="2 5" vertical={false} />
      <XAxis dataKey="date" hide />
      <YAxis
        width={46}
        tick={{ fill: "var(--text-dim)", fontSize: 11, fontFamily: "var(--font-mono)" }}
        axisLine={false}
        tickLine={false}
        domain={["auto", "auto"]}
      />
      {referenceLines?.map((value) => (
        <ReferenceLine key={value} y={value} stroke="var(--border)" strokeDasharray="3 3" />
      ))}
      <Tooltip
        contentStyle={tooltipStyle}
        labelStyle={{ color: "var(--text-dim)", marginBottom: 4 }}
        itemStyle={{ padding: 0 }}
      />
      {series.map((s) => (
        <Line
          key={s.key}
          type="monotone"
          dataKey={s.key}
          name={s.label}
          stroke={s.color}
          strokeWidth={1.5}
          strokeDasharray={s.dashed ? "4 3" : undefined}
          dot={false}
          isAnimationActive={false}
          connectNulls
        />
      ))}
    </LineChart>
  </ResponsiveContainer>
);
