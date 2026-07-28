import React, { useEffect } from "react";
import { configs } from "./lib/configs";

const fetchTickerData = async (ticker: string) => {
  const r = await fetch(`${configs.BACKEND}/tickers/${ticker}`);

  if (r.status !== 200) {
    return { message: "Yikers" };
  }

  return await r.json();
};

interface TickerPullProps {
  ticker: string;
  setPrice: React.Dispatch<React.SetStateAction<string>>;
}

const TickerPull = ({ ticker, setPrice }: TickerPullProps) => {
  useEffect(() => {
    fetchTickerData(ticker).then((a) => {
      const closingPrices =
        a?.closingPrices ??
        a?.data?.closingPrices ??
        a?.results?.closingPrices ??
        [];
      const closeVal = Array.isArray(closingPrices)
        ? closingPrices[closingPrices.length - 1]?.close
        : a?.price;

      if (closeVal !== undefined) {
        setPrice(String(closeVal));
      } else {
        setPrice("N/A");
      }
    }).catch(() => setPrice("N/A"));
  }, [ticker, setPrice]);

  return null;
};

export default TickerPull;
