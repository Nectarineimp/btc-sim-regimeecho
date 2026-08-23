"""
RegimeEcho: Forward Monte Carlo Price Simulator
Approach B: Filtered Empirical Block Bootstrap (Non-Parametric Era 4 Echo)
"""

import argparse
from datetime import timedelta
import os
import numpy as np
import pandas as pd


def load_and_calibrate(data_path: str):
    """
    Ingest historical rates, isolate power-law detrended residuals,
    and extract empirical daily residual innovations from Era 4 (Spot ETF Era).
    """
    df = pd.read_csv(data_path)

    # Standardize column mapping
    time_col = "date" if "date" in df.columns else "time"
    price_col = "close" if "close" in df.columns else "price"

    df["time"] = pd.to_datetime(df[time_col])
    df["price"] = pd.to_numeric(df[price_col], errors="coerce")
    df = df.dropna(subset=["time", "price"]).sort_values("time").reset_index(drop=True)

    genesis = pd.to_datetime("2009-01-03 18:15:05", utc=True)
    if df["time"].dt.tz is None:
        df["time"] = df["time"].dt.tz_localize("UTC")

    df["tau"] = (df["time"] - genesis).dt.total_seconds() / 86400.0
    df = df[df["tau"] > 0].copy()
    df["log_tau"] = np.log(df["tau"])
    df["log_price"] = np.log(df["price"])

    # Longitudinal Secular Baseline: ln(P) = alpha + beta * ln(tau)
    slope, intercept = np.polyfit(df["log_tau"], df["log_price"], 1)
    df["residual"] = df["log_price"] - (intercept + slope * df["log_tau"])

    # Filter for Era 4 (Spot ETF Regime: 2024-01-11 onwards)
    era4_start = pd.to_datetime("2024-01-11", utc=True)
    df_era4 = df[df["time"] >= era4_start].copy().reset_index(drop=True)

    # Calculate empirical daily residual increments: delta_eps = eps_t - eps_{t-1}
    df_era4["residual_diff"] = df_era4["residual"].diff()
    empirical_innovations = df_era4["residual_diff"].dropna().values

    current_price = df["price"].iloc[-1]
    current_tau = df["tau"].iloc[-1]
    current_eps = df["residual"].iloc[-1]
    last_date = df["time"].iloc[-1]

    print("==================================================")
    print(" RegimeEcho Model Calibration (Era 4 Non-Parametric)")
    print("==================================================")
    print(f"Data Cutoff Date:            {last_date.strftime('%Y-%m-%d')}")
    print(f"Latest Reference Price:      ${current_price:,.2f}")
    print(f"Power-Law Intercept:         {intercept:.4f}")
    print(f"Power-Law Elasticity:        {slope:.4f}")
    print(f"Current Residual:            {current_eps:.4f}")
    print(f"Era 4 Empirical Sample Size: {len(empirical_innovations)} daily shocks")
    print(f"Daily Innovation Mean:       {np.mean(empirical_innovations):.6f}")
    print(f"Daily Innovation Std:        {np.std(empirical_innovations):.6f}")
    print("==================================================\n")

    return {
        "alpha": intercept,
        "beta": slope,
        "current_tau": current_tau,
        "current_eps": current_eps,
        "innovations": empirical_innovations,
        "last_date": last_date,
    }


def simulate_regimeecho(params: dict, n_paths: int = 10000, horizon_days: int = 365, block_size: int = 7):
    """
    Moving Block Bootstrap (MBB) simulation.
    Resamples contiguous blocks of empirical Era 4 innovations to preserve volatility clustering.
    """
    alpha = params["alpha"]
    beta = params["beta"]
    tau_0 = params["current_tau"]
    eps_0 = params["current_eps"]
    innovations = params["innovations"]

    n_innovations = len(innovations)
    max_start_idx = n_innovations - block_size
    n_blocks = int(np.ceil(horizon_days / block_size))

    np.random.seed(42)  # Deterministic seed for scientific reproducibility

    # Generate random block starting indices: [n_blocks, n_paths]
    start_indices = np.random.randint(0, max_start_idx + 1, size=(n_blocks, n_paths))

    # Assemble bootstrapped innovation paths
    resampled_shocks = np.zeros((n_blocks * block_size, n_paths))
    for b in range(n_blocks):
        for p in range(n_paths):
            idx = start_indices[b, p]
            resampled_shocks[b * block_size : (b + 1) * block_size, p] = innovations[idx : idx + block_size]

    # Truncate to horizon_days: [horizon_days, n_paths]
    shocks = resampled_shocks[:horizon_days, :]

    # Cumulative sum to build residual trajectories
    simulated_residuals = eps_0 + np.cumsum(shocks, axis=0)

    # Combine with deterministic power-law backbone
    tau_series = tau_0 + np.arange(1, horizon_days + 1)
    base_log_price = alpha + beta * np.log(tau_series)

    log_prices = base_log_price[:, np.newaxis] + simulated_residuals
    price_paths = np.exp(log_prices)

    return price_paths


def aggregate_monthly(price_paths: np.ndarray, last_date: pd.Timestamp):
    """
    Aggregate daily paths into 12 forward monthly buckets and extract High/Low percentiles.
    """
    horizon_days, n_paths = price_paths.shape
    date_range = [last_date + timedelta(days=i + 1) for i in range(horizon_days)]

    df_dates = pd.DataFrame({"date": date_range})
    df_dates["month_label"] = df_dates["date"].dt.strftime("%Y-%m")
    unique_months = df_dates["month_label"].unique()[:12]

    results = []

    for m in unique_months:
        idx = df_dates[df_dates["month_label"] == m].index
        month_paths = price_paths[idx, :]

        month_highs = np.max(month_paths, axis=0)
        month_lows = np.min(month_paths, axis=0)

        results.append({
            "Month": m,
            "Low_p05": np.percentile(month_lows, 5),
            "Low_p16": np.percentile(month_lows, 16),
            "Low_p50": np.percentile(month_lows, 50),
            "Low_p84": np.percentile(month_lows, 84),
            "Low_p95": np.percentile(month_lows, 95),
            "High_p05": np.percentile(month_highs, 5),
            "High_p16": np.percentile(month_highs, 16),
            "High_p50": np.percentile(month_highs, 50),
            "High_p84": np.percentile(month_highs, 84),
            "High_p95": np.percentile(month_highs, 95),
        })

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description="Run RegimeEcho Bitcoin Price Simulator")
    parser.add_argument("--data", type=str, default="data/btc_daily_price.csv", help="Path to reference CSV")
    parser.add_argument("--iterations", type=int, default=10000, help="Number of Monte Carlo paths")
    parser.add_argument("--block-size", type=int, default=7, help="Block size in days for Moving Block Bootstrap")
    parser.add_argument("--output", type=str, default="output/monthly_forecast.csv", help="Output CSV path")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    params = load_and_calibrate(args.data)
    price_paths = simulate_regimeecho(params, n_paths=args.iterations, horizon_days=365, block_size=args.block_size)
    df_forecast = aggregate_monthly(price_paths, params["last_date"])

    df_forecast.to_csv(args.output, index=False)
    print(f"Forecast successfully written to: {args.output}\n")

    display_df = df_forecast.copy()
    for col in display_df.columns:
        if col != "Month":
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")

    print(display_df[["Month", "Low_p05", "Low_p50", "High_p50", "High_p95"]].to_string(index=False))


if __name__ == "__main__":
    main()