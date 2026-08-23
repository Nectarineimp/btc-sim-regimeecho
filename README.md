# btc-sim-regimeecho
Filtered Empirical Block Bootstrap (Non-Parametric Era 4 Echo)

# RegimeEcho (btc-sim-regimeecho)

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Approach B: Filtered Empirical Block Bootstrap (Non-Parametric Era 4 Echo)**

**RegimeEcho** is a strictly non-parametric simulation engine. Rejecting synthetic Gaussian increments, RegimeEcho stochastically resamples genuine empirical price and residual trajectories directly from **Era 4 (Spot ETF / Institutional Regime)**, perfectly preserving real-world fat tails, skewness, and volatility clustering.

---

## Theoretical Framework

Rather than imposing parametric distribution functions ($a \ priori$ modeling), RegimeEcho preserves empirical microstructure:

1. **Residual Innovation Sampling:** Stationary daily residuals $\hat{\varepsilon}_t$ are extracted from Era 4 data ($N \approx 864$ days).
2. **Moving Block Bootstrap (MBB):** Daily return vectors are resampled in contiguous blocks of length $L \sim \text{Geometric}(p)$ to preserve serial autocorrelation and volatility memory.
3. **Power-Law Drift Integration:** Resampled innovations are projected onto the forward deterministic power-law backbone:
   $$P_{t+k} = \exp\left(\hat{\alpha} + \hat{\beta}\ln(\tau_t + k) + \hat{\varepsilon}^*_{t+k}\right)$$

This approach eliminates model risk by simulating only what the institutional market regime has empirically demonstrated.

---

## Output Architecture

Over $M = 10{,}000$ iterations, the engine computes:
- **12-Month Median High / Low:** Baseline expectation
- **$1\sigma$ Envelope (16th–84th Percentile):** Empirical core density
- **$2\sigma$ Envelope (5th–95th Percentile):** Historical extreme tail risk

---

## Quickstart

```bash
# Clone and install dependencies
git clone [https://github.com/Nectarineimp/btc-sim-regimeecho.git](https://github.com/Nectarineimp/btc-sim-regimeecho.git)
cd btc-sim-regimeecho
poetry install

# Run non-parametric block bootstrap
poetry run python src/simulate.py --iterations 10000 --block-size 7 --output output/monthly_forecast.csv
```
