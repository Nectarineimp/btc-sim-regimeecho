# RegimeEcho (`btc-sim-regimeecho`)

> **Empirical Moving Block Bootstrap (Non-Parametric Era 4 Regime Model)**
> 

`RegimeEcho` is a non-parametric Monte Carlo forecasting engine designed to project forward Bitcoin price trajectories without imposing restrictive distribution assumptions ($a\ priori$ parametric models). Instead of drawing synthetic Gaussian or Levy innovations, the engine stochastically resamples genuine empirical price and residual dynamics directly from **Era 4 (Spot ETF / Institutional Regime)**, fully preserving real-world fat tails, skewness, and volatility clustering.

---

## Analytical Purpose & Tournament Role

Within the 12-month stochastic forecasting tournament alongside parametric engines (`TrueTether`, `TailWhip`, `Chamberlain`, `GateKeeper`), `RegimeEcho` serves as the **empirical control and regime-conditioned benchmark**:

* **Model Risk Elimination:** Parametric stochastic differential equations (e.g., Ornstein-Uhlenbeck or Merton Jump-Diffusion) assume idealized mathematical formulations. `RegimeEcho` eliminates functional misspecification by constraining forward variance to behaviors already demonstrated by the market.


* **Institutional Structural Break Isolation:** Bitcoin's market microstructure shifted fundamentally after January 11, 2024 (Era 4 spot ETF launch). Earlier eras (2009–2023) exhibit retail-driven parabolic runs and unconstrained structural drawdowns that distort modern institutional depth. `RegimeEcho` isolates and replays Era 4 dynamics.


* **Benchmark for Volatility Clustering:** By sampling multi-day contiguous blocks rather than independent daily increments, `RegimeEcho` tests whether empirical institutional autocorrelation outperforms continuous-time diffusion formulations over a 12-month forward horizon.



---

## Mathematical Architecture

The simulation decomposes Bitcoin price formation into a **deterministic secular trend** and an **empirical stochastic residual process**.

### 1. Longitudinal Secular Power-Law Baseline

Secular valuation is anchored to elapsed market time $\tau_t$ calculated in days since the Bitcoin Genesis Block (`2009-01-03 18:15:05 UTC`):

$$\tau_t = \frac{t - t_{\text{genesis}}}{86{,}400}$$

An Ordinary Least Squares (OLS) linear regression calibrates long-term elasticity across historical log space:

$$\ln(P_t) = \alpha + \beta \ln(\tau_t) + \varepsilon_t$$

Where:

* $\alpha$: Intercept parameter representing early protocol scale.


* $\beta$: Elasticity of price with respect to protocol age.


* $\varepsilon_t$: Detrended residual capturing macroeconomic cycles, speculation, and liquidity shocks.



### 2. Empirical Era 4 Residual Innovation Extraction

The historical residual series is segmented to isolate the post-ETF institutional regime ($t \ge \text{2024-01-11}$):

$$\Delta \varepsilon_t = \varepsilon_t - \varepsilon_{t-1}$$

This generates a discrete empirical shock pool $I_{\text{Era4}} = \{\Delta \varepsilon_1, \Delta \varepsilon_2, \dots, \Delta \varepsilon_N\}$.

### 3. Moving Block Bootstrap (MBB)

To maintain the time-series autocorrelation of volatility regimes (ARCH/GARCH-like clustering) without estimating conditional heteroskedasticity parameters, daily residual shocks are resampled in contiguous blocks of length $L$ (default $L = 7$ days):

$$B_{j} = \left( \Delta \varepsilon_{s}, \Delta \varepsilon_{s+1}, \dots, \Delta \varepsilon_{s+L-1} \right), \quad s \sim \text{Uniform}(1, N - L + 1)$$

For each simulated forward path $p \in [1, M]$ and block index $b \in [1, \lceil H / L \rceil]$:

1. A valid starting index $s$ is randomly selected from Era 4 history.


2. Contiguous blocks are concatenated to build a forward horizon of $H = 365$ days.


3. Forward residual trajectories are accumulated from the current market residual $\varepsilon_0$:



$$\varepsilon_{t}^* = \varepsilon_0 + \sum_{k=1}^{t} \Delta \varepsilon_k^*$$

### 4. Forward Price Trajectory Reconstruction

Forward price paths are computed by mapping the accumulated empirical residuals back onto the forward power-law spine:

$$P_{t+k} = \exp\left( \alpha + \beta \ln(\tau_0 + k) + \varepsilon_{t+k}^* \right)$$

---

## Output Aggregation Schema

For each of the $M = 10{,}000$ simulated daily paths, monthly calendar extrema are extracted across each forward month bucket $m \in [1, 12]$:

$$H_m^{(p)} = \max_{t \in m} P_t^{(p)}, \qquad L_m^{(p)} = \min_{t \in m} P_t^{(p)}$$

The final forecast file (`monthly_forecast.csv`) outputs empirical quantile distributions for both bounds:

| Field | Description | Quantile |
| --- | --- | --- |
| `Month` | Calendar bucket (`YYYY-MM`)

 | — |
| `Low_p05` | 2$\sigma$ Lower Bounding Tail

 | 5th percentile of monthly minimums

 |
| `Low_p16` | 1$\sigma$ Lower Density Core

 | 16th percentile of monthly minimums

 |
| `Low_p50` | Expected Median Floor

 | 50th percentile of monthly minimums

 |
| `Low_p84` | 1$\sigma$ Upper Floor Density

 | 84th percentile of monthly minimums

 |
| `Low_p95` | 2$\sigma$ Upper Floor Tail

 | 95th percentile of monthly minimums

 |
| `High_p05` | 2$\sigma$ Lower Ceiling Tail

 | 5th percentile of monthly maximums

 |
| `High_p16` | 1$\sigma$ Lower Ceiling Density

 | 16th percentile of monthly maximums

 |
| `High_p50` | Expected Median Ceiling

 | 50th percentile of monthly maximums

 |
| `High_p84` | 1$\sigma$ Upper Ceiling Density

 | 84th percentile of monthly maximums

 |
| `High_p95` | 2$\sigma$ Upper Bounding Tail

 | 95th percentile of monthly maximums

 |

---

## Installation & Setup

Ensure Python 3.12+ and Poetry are configured on your system.

```bash
# Clone the repository
git clone https://github.com/Nectarineimp/btc-sim-regimeecho.git[cite: 3]
cd btc-sim-regimeecho[cite: 3]

# Install locked dependencies via Poetry
poetry install[cite: 3]

```

### Required Data Schema

The model expects daily historical close prices formatted as `data/btc_daily_price.csv`:

```csv
date,close
2010-07-18,0.08584
2010-07-19,0.08080
...
2026-10-05,94120.50

```

(Accepts either `date`/`time` and `close`/`price` column headers).

---

## CLI Execution & Options

Run the simulator directly through Poetry:

```bash
# Standard 10,000 iteration run with 7-day resampling blocks
poetry run python src/simulate.py \
  --data data/btc_daily_price.csv \
  --iterations 10000 \
  --block-size 7 \
  --output output/monthly_forecast.csv

```

### Argument Reference

| Flag | Default | Type | Description |
| --- | --- | --- | --- |
| `--data`<br> | `data/btc_daily_price.csv`<br> | `str`<br> | Path to historical daily Bitcoin price CSV.

 |
| `--iterations`<br> | `10000`<br> | `int`<br> | Total forward Monte Carlo trajectories to simulate.

 |
| `--block-size`<br> | `7`<br> | `int`<br> | Contiguous sampling block length $L$ in days.

 |
| `--output`<br> | `output/monthly_forecast.csv`<br> | `str`<br> | Filepath destination for output quantile CSV.

 |

---

## Tournament Visualization Integration

To plot `RegimeEcho` against other tournament models (`TrueTether`, `TailWhip`, `Chamberlain`) and compare directly to realized market actuals, render via `btc-sim-visualizer`:

```bash
# Render RegimeEcho solo forecast
poetry run python -m visualizer output/monthly_forecast.csv \
  --output output/regimeecho_forecast.png

# Render multi-model tournament overlay with live market actuals
poetry run python -m visualizer \
  ../btc-sim-truetether/output/monthly_forecast.csv \
  output/monthly_forecast.csv \
  ../btc-sim-tailwhip/output/monthly_forecast.csv \
  --actuals data/actuals.csv \
  --output output/tournament_overlay.png

```

In the multi-model overlay visualizer, `RegimeEcho` renders with its signature **Royal Blue** palette (`#4da6ff` / `RGB(0.25, 0.55, 0.95)`), blending into magenta when overlapping with `TrueTether` and cyan when overlapping with `TailWhip`.

---

## Verification & Execution Steps

1. **Verify Era 4 Data:** Ensure `data/btc_daily_price.csv` contains recent price history beyond January 11, 2024, to supply adequate residual innovation samples.


2. **Execute Engine:** Run `poetry run python src/simulate.py --iterations 10000 --block-size 7`.


3. **Inspect Output:** Confirm that `output/monthly_forecast.csv` contains 12 rows corresponding to forward calendar months with monotonically increasing quantiles (`Low_p05` $\le$ `Low_p16` $\le$ `Low_p50` $\le$ `High_p50` $\le$ `High_p95`).


4. **Update Overlay:** Point `btc-sim-visualizer` to the generated output to track tournament coverage calibration.
