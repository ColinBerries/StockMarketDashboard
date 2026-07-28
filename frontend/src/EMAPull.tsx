import React, { useEffect } from "react";

import { configs } from "./lib/configs";

const fetchEMAData = async (
  ticker: string,
  period: number,
  signal?: AbortSignal,
) => {
  const r = await fetch(
    `${configs.BACKEND}/ema/${encodeURIComponent(ticker)}?period=${period}`,
    { signal },
  );

  if (r.status !== 200) {
    return { message: "Yikers" };
  }

  return await r.json();
};

interface EMAPullProps {
  ticker: string;
  setPrice: React.Dispatch<React.SetStateAction<string>>;
  period?: number; //optional; defaults to 50
}

const EMAPull = ({ ticker, setPrice, period = 50 }: EMAPullProps) => {
  useEffect(() => {
    const controller = new AbortController();
    fetchEMAData(ticker, period, controller.signal)
      .then((data) => {
        const emaArr =
          data?.emaValue ??
          data?.data?.emaValue ??
          data?.results?.emaValue ??
          [];

        let emaVal: any;

        if (Array.isArray(emaArr) && emaArr.length > 0) {
          emaVal = emaArr[emaArr.length - 1]?.ema;
        }

        if (emaVal !== undefined) {
          setPrice(String(emaVal));
        } else {
          setPrice("N/A");
        }
      })
      .catch((error) => {
        if (error?.name !== "AbortError") {
          setPrice("N/A");
        }
      });
    return () => controller.abort();
  }, [period, ticker, setPrice]);

  return null;
};

export default EMAPull;
