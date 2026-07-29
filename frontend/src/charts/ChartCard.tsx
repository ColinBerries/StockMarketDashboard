import { ReactNode } from "react";
import styles from "./ChartCard.module.css";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  error?: string;
  children: ReactNode;
}

export const ChartCard = ({ title, subtitle, error, children }: ChartCardProps) => (
  <section className={styles.card}>
    <header className={styles.header}>
      <h3 className={styles.title}>{title}</h3>
      {subtitle && <span className={styles.subtitle}>{subtitle}</span>}
    </header>
    {error ? <p className={styles.error}>Unavailable — {error}</p> : children}
  </section>
);
