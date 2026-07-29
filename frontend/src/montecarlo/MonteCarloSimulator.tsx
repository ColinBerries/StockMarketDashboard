import { useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  fetchMonteCarloSimulation,
  isMonteCarloResult,
  MonteCarloResult,
  ReturnDistribution,
  RiskProfile,
} from "../lib/api";
import { formatCurrency, formatPercent } from "../lib/format";
import styles from "./MonteCarloSimulator.module.css";

const RISK_PROFILES: Array<{ value: RiskProfile; label: string }> = [
  { value: "conservative", label: "Conservative (20% stocks)" },
  { value: "moderate", label: "Moderate (50% stocks)" },
  { value: "aggressive", label: "Aggressive (80% stocks)" },
];

interface ChartPoint {
  year: number;
  outerRange: [number, number];
  innerRange: [number, number];
  median: number;
}

export const MonteCarloSimulator = () => {
  const [initial, setInitial] = useState(10000);
  const [years, setYears] = useState(10);
  const [riskProfile, setRiskProfile] = useState<RiskProfile>("moderate");
  const [distribution, setDistribution] = useState<ReturnDistribution>("gaussian");
  const [target, setTarget] = useState<number | "">("");
  const [result, setResult] = useState<MonteCarloResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fat-tailed sampling is meaningfully slower than Gaussian (see
      // Signals/monte_carlo.py) -- fewer iterations keeps the request snappy.
      const iterations = distribution === "stable" ? 400 : 800;
      const response = await fetchMonteCarloSimulation({
        initial,
        years,
        riskProfile,
        distribution,
        iterations,
        target: target === "" ? undefined : target,
      });
      if (isMonteCarloResult(response)) {
        setResult(response);
        setError(null);
      } else {
        setResult(null);
        setError(response.error);
      }
    } finally {
      setLoading(false);
    }
  };

  const chartData: ChartPoint[] =
    result?.bands.map((band) => ({
      year: band.year,
      outerRange: [band.p5, band.p95],
      innerRange: [band.p25, band.p75],
      median: band.p50,
    })) ?? [];

  return (
    <section className={styles.card}>
      <header className={styles.header}>
        <h2>Portfolio Monte Carlo Projector</h2>
        <span className={styles.subtitle}>
          Return assumptions are fitted from real SPY history, not hardcoded.
        </span>
      </header>

      <div className={styles.form}>
        <label className={styles.field}>
          <span>Starting amount</span>
          <input
            type="number"
            min={1}
            value={initial}
            onChange={(event) => setInitial(Number(event.target.value))}
          />
        </label>
        <label className={styles.field}>
          <span>Years</span>
          <input
            type="number"
            min={1}
            max={30}
            value={years}
            onChange={(event) => setYears(Number(event.target.value))}
          />
        </label>
        <label className={styles.field}>
          <span>Risk profile</span>
          <select
            value={riskProfile}
            onChange={(event) => setRiskProfile(event.target.value as RiskProfile)}
          >
            {RISK_PROFILES.map((profile) => (
              <option key={profile.value} value={profile.value}>
                {profile.label}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.field}>
          <span>Return model</span>
          <select
            value={distribution}
            onChange={(event) => setDistribution(event.target.value as ReturnDistribution)}
          >
            <option value="gaussian">Gaussian (textbook)</option>
            <option value="stable">Fat-tailed (Mandelbrot-style)</option>
          </select>
        </label>
        <label className={styles.field}>
          <span>Target amount (optional)</span>
          <input
            type="number"
            min={0}
            value={target}
            onChange={(event) =>
              setTarget(event.target.value === "" ? "" : Number(event.target.value))
            }
            placeholder="e.g. 50000"
          />
        </label>
        <button className={styles.runButton} onClick={runSimulation} disabled={loading}>
          {loading ? "Running…" : "Run simulation"}
        </button>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {result && (
        <>
          <div className={styles.chartWrap}>
            <ResponsiveContainer width="100%" height={280}>
              <ComposedChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="2 5" vertical={false} />
                <XAxis
                  dataKey="year"
                  tick={{ fill: "var(--text-dim)", fontSize: 11, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                  label={{
                    value: "Year",
                    position: "insideBottom",
                    offset: -2,
                    fill: "var(--text-dim)",
                    fontSize: 11,
                  }}
                />
                <YAxis
                  width={70}
                  tick={{ fill: "var(--text-dim)", fontSize: 11, fontFamily: "var(--font-mono)" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(value: number) => formatCurrency(value)}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--panel-raised)",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    fontFamily: "var(--font-mono)",
                    fontSize: 12,
                  }}
                  labelFormatter={(year) => `Year ${year}`}
                  formatter={(value, name) => {
                    if (Array.isArray(value)) {
                      const [low, high] = value as [number, number];
                      return [`${formatCurrency(low)} \u2013 ${formatCurrency(high)}`, name];
                    }
                    return [formatCurrency(Number(value)), name];
                  }}
                />
                <Area
                  dataKey="outerRange"
                  name="5th-95th pct"
                  stroke="none"
                  fill="var(--accent)"
                  fillOpacity={0.12}
                  isAnimationActive={false}
                />
                <Area
                  dataKey="innerRange"
                  name="25th-75th pct"
                  stroke="none"
                  fill="var(--accent)"
                  fillOpacity={0.28}
                  isAnimationActive={false}
                />
                <Line
                  dataKey="median"
                  name="Median"
                  stroke="var(--text)"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className={styles.summaryRow}>
            <div className={styles.summaryItem}>
              <span className={styles.summaryLabel}>Median outcome</span>
              <span className={styles.summaryValue}>
                {formatCurrency(result.final_value_percentiles.p50)}
              </span>
            </div>
            <div className={styles.summaryItem}>
              <span className={styles.summaryLabel}>5th&ndash;95th percentile</span>
              <span className={styles.summaryValue}>
                {formatCurrency(result.final_value_percentiles.p5)} &ndash;{" "}
                {formatCurrency(result.final_value_percentiles.p95)}
              </span>
            </div>
            {result.probability_of_target !== undefined && (
              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>
                  Chance of reaching {formatCurrency(result.target_value ?? 0)}
                </span>
                <span className={styles.summaryValue}>
                  {formatPercent(result.probability_of_target * 100, 1)}
                </span>
              </div>
            )}
          </div>

          <p className={styles.assumptions}>
            Fitted from SPY history: {formatPercent(result.assumptions.annualized_stock_mean * 100, 1)}{" "}
            annualized return, {formatPercent(result.assumptions.annualized_stock_std * 100, 1)}{" "}
            annualized volatility
            {result.distribution === "stable" &&
              `, tail index \u03b1 \u2248 ${result.assumptions.stable_alpha.toFixed(2)} (2.0 = Gaussian)`}
            .
          </p>
        </>
      )}
    </section>
  );
};
