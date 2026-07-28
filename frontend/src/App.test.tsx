import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App";

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({ status: 500 } as Response),
  ) as jest.Mock;
});

test("renders the price and EMA sections", async () => {
  render(<App />);
  expect(
    screen.getByRole("heading", { name: /closing price/i }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("heading", {
      name: /exponential moving average/i,
    }),
  ).toBeInTheDocument();
  expect(
    await screen.findByText(/portfolio signals are unavailable/i),
  ).toBeInTheDocument();
});
