import { useEffect, useState } from "react";
import {
  fetchTickerDashboard,
  isTickerDashboard,
  TickerDashboard,
} from "../lib/api";

interface UseTickerDashboardResult {
  data: TickerDashboard | null;
  error: string | null;
  loading: boolean;
}

export const useTickerDashboard = (ticker: string): UseTickerDashboardResult => {
  const [data, setData] = useState<TickerDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ticker) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    fetchTickerDashboard(ticker, controller.signal)
      .then((response) => {
        if (isTickerDashboard(response)) {
          setData(response);
          setError(null);
        } else {
          setData(null);
          setError(response.error);
        }
      })
      .catch((err) => {
        if (err?.name !== "AbortError") {
          setData(null);
          setError(String(err));
        }
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [ticker]);

  return { data, error, loading };
};
