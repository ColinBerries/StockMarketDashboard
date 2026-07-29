import { useEffect, useState } from "react";
import { CanslimResult, fetchCanslimTicker, isCanslimResult } from "../lib/api";

export const useCanslimTicker = (ticker: string) => {
  const [data, setData] = useState<CanslimResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    const controller = new AbortController();
    setError(null);

    fetchCanslimTicker(ticker, controller.signal)
      .then((response) => {
        if (isCanslimResult(response)) {
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
      });

    return () => controller.abort();
  }, [ticker]);

  return { data, error };
};
