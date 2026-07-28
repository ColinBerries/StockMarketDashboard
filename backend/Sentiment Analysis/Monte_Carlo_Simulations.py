import random

import matplotlib.pyplot as plt
import pandas as pd


def port_end_value(
    stock_ret: float = 0.1,
    rf: float = 0.03,
    stock_weight: float = 0.5,
    portfolio_initial_value: float = 1000,
) -> float:
    portfolio_return = rf * (1 - stock_weight) + stock_ret * stock_weight
    return portfolio_initial_value * (1 + portfolio_return)


def port_end_value_simulations(
    stock_mean: float = 0.1,
    stock_std: float = 0.2,
    stock_weight: float = 0.5,
    n_iter: int = 1000,
) -> list[float]:
    return [
        port_end_value(
            random.normalvariate(stock_mean, stock_std),
            stock_weight=stock_weight,
        )
        for _ in range(n_iter)
    ]


def create_dataframe_from_results(results: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"Portfolio End Values": results})


def visualize_results(frame: pd.DataFrame) -> None:
    frame.plot.hist(bins=100)
    plt.show()


def probability_table(frame: pd.DataFrame) -> pd.Series:
    percentiles = [index / 20 for index in range(1, 20)]
    return frame["Portfolio End Values"].quantile(percentiles)


def probability_of_objective(
    frame: pd.DataFrame,
    desired_cash: float = 1050,
) -> float:
    return float(
        (frame["Portfolio End Values"] >= desired_cash).astype(int).mean()
    )


def model_outputs(
    results: list[float],
    desired_cash: float = 1050,
    visualize: bool = True,
) -> tuple[pd.Series, float]:
    frame = create_dataframe_from_results(results)
    if visualize:
        visualize_results(frame)
    return (
        probability_table(frame),
        probability_of_objective(frame, desired_cash=desired_cash),
    )


def display_model_summary(
    results: list[float],
    desired_cash: float = 1050,
    visualize: bool = True,
) -> None:
    table, probability = model_outputs(
        results,
        desired_cash=desired_cash,
        visualize=visualize,
    )
    print("Probability Table")
    print(table.apply(lambda value: f"${value:.2f}"))
    print(
        f"\nProbability of getting ${desired_cash:,.0f} in cash: "
        f"{probability:.1%}\n"
    )


if __name__ == "__main__":
    simulation_results = port_end_value_simulations()
    display_model_summary(simulation_results)
