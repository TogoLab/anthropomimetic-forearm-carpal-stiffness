"""
Direction (anisotropy orientation) comparison between Finger and Combined,
using a CIRCULAR / HARMONIC model instead of a categorical angle factor.

Why this script (vs direction_anova_finger_vs_combined.py):
    The hypothesis is about the *orientation* of the stiffness-anisotropy
    pattern, and push angle is a circular variable (0..330 deg).  A categorical
    C(condition)*C(angle) interaction is an omnibus "the profiles differ in some
    way" test (11 df) -- it can fire on a single-angle magnitude blip and does
    not isolate a rotation of the anisotropy axis.

    Here we fit harmonics of the angle:
        log(K) ~ condition * (cos t + sin t + cos 2t + sin 2t),   t = angle[rad]
    - log scale turns the multiplicative magnitude difference between conditions
      into a pure additive main effect, so the condition x harmonic INTERACTION
      tests the magnitude-independent *shape* (no ad-hoc grand-mean division).
    - 1st harmonic (1 cycle / 360 deg) = directional asymmetry; its phase is a
      peak direction.
    - 2nd harmonic (2 cycles / 360 deg, i.e. 180-deg periodic) = the bidirectional
      anisotropy AXIS, which is the physically meaningful "stiff direction" for a
      tissue-like anisotropy.  Its phase/2 is the axis orientation.

Tests reported:
    * Joint condition x harmonic interaction (4 df) via a nested-model F-test
      -> "does the angular pattern differ between conditions at all".
    * Separate 1st-harmonic (2 df) and 2nd-harmonic (2 df) interaction tests
      -> localizes WHETHER the asymmetry and/or the anisotropy axis differ.
    * Per-condition fitted amplitude / peak / axis orientation (deg).

Notes vs the old script:
    - The mixedlm(groups=rep) "robustness check" was removed: the replicate index
      1..8 is just a within-cell label (rep 1 at 0 deg has no relation to rep 1 at
      30 deg), so grouping by it is not a meaningful random-effects structure.  If a
      real grouping exists (subject / session / trial order), add it as `groups=`.
    - A physical lower bound (PHYS_MIN) drops implausible near-zero stiffness
      artifacts that pass the old `> 0` gate (e.g. 0.4 N/mm vs cell median ~80).

Run with:  MPLBACKEND=Agg python direction_harmonic_finger_vs_combined.py
"""

import os
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

# Reuse the exact data-building logic from the categorical script.
from direction_anova_finger_vs_combined import (
    build_long_data, CONDITIONS, ANGLES, RESULTS_DIR,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LONG_CSV = os.path.join(RESULTS_DIR, "direction_anova_long_data.csv")
PHYS_MIN = 5.0   # N/mm: drop physically implausible near-zero artifacts
N_HARM = 2       # number of harmonics (2 -> cos/sin of t and 2t)

FIT_PNG = os.path.join(RESULTS_DIR, "direction_harmonic_fit.png")
POLAR_PNG = os.path.join(RESULTS_DIR, "direction_harmonic_polar.png")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_data():
    """Use the cached long-format CSV if present, else recompute (slow)."""
    if os.path.exists(LONG_CSV):
        print(f"Loading cached data: {LONG_CSV}")
        df = pd.read_csv(LONG_CSV)
    else:
        print("Cached data not found; recomputing stiffness for all trials...")
        df = build_long_data()
    return df[["stiffness", "condition", "angle", "rep"]].copy()


def prepare(df):
    n0 = len(df)
    df = df[df["stiffness"] >= PHYS_MIN].copy()
    dropped = n0 - len(df)
    if dropped:
        print(f"[filter] dropped {dropped} trial(s) with stiffness < {PHYS_MIN} N/mm "
              f"(physically implausible artifacts)")
    df["theta"] = np.deg2rad(df["angle"])
    df["logK"] = np.log(df["stiffness"])
    # Explicit harmonic columns (named h1c, h1s, h2c, h2s, ...) for clean params.
    for k in range(1, N_HARM + 1):
        df[f"h{k}c"] = np.cos(k * df["theta"])
        df[f"h{k}s"] = np.sin(k * df["theta"])
    return df


def harmonic_terms():
    return [f"h{k}{cs}" for k in range(1, N_HARM + 1) for cs in ("c", "s")]


# ---------------------------------------------------------------------------
# Models / tests
# ---------------------------------------------------------------------------
def nested_interaction_test(df, terms, label):
    """F-test for adding condition x <terms> interaction over the additive model."""
    base = harmonic_terms()
    add = " + ".join(base)
    full_int = " + ".join(f"C(condition):{t}" for t in terms)
    full = ols(f"logK ~ C(condition) + {add} + {full_int}", data=df).fit()
    red = ols(f"logK ~ C(condition) + {add}", data=df).fit()
    t = anova_lm(red, full)
    F = t["F"].iloc[1]
    p = t["Pr(>F)"].iloc[1]
    ddf = int(t["df_diff"].iloc[1])
    print(f"\n=== {label} interaction (condition x {len(terms)} term(s), {ddf} df) ===")
    print(f"  F = {F:.4f}   p = {p:.6g}   {'SIGNIFICANT' if p < 0.05 else 'n.s.'}")
    return F, p, ddf


def fit_per_condition(df):
    """Per-condition harmonic fit -> amplitudes, 1st-harmonic peak, 2nd-harmonic axis."""
    add = " + ".join(harmonic_terms())
    out = {}
    for c in CONDITIONS:
        d = df[df["condition"] == c]
        m = ols(f"logK ~ {add}", data=d).fit()
        b = m.params
        rec = {"model": m, "intercept": b["Intercept"]}
        c1, s1 = b["h1c"], b["h1s"]
        rec["A1"] = float(np.hypot(c1, s1))
        rec["peak1_deg"] = float(np.rad2deg(np.arctan2(s1, c1)) % 360)
        if N_HARM >= 2:
            c2, s2 = b["h2c"], b["h2s"]
            rec["A2"] = float(np.hypot(c2, s2))
            # 180-deg periodic axis -> two equivalent orientations a, a+180
            rec["axis2_deg"] = float((np.rad2deg(np.arctan2(s2, c2)) / 2) % 180)
        out[c] = rec
    return out


def predict_curve(rec, deg_grid):
    t = np.deg2rad(deg_grid)
    b = rec["model"].params
    y = np.full_like(deg_grid, b["Intercept"], dtype=float)
    for k in range(1, N_HARM + 1):
        y += b[f"h{k}c"] * np.cos(k * t) + b[f"h{k}s"] * np.sin(k * t)
    return y  # log scale


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
COLORS = {"Finger": "#1f77b4", "Combined": "#d62728"}


def plot_fit(df, fits):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    grid = np.linspace(0, 360, 361)
    fig, ax = plt.subplots(figsize=(9, 5))
    for c in CONDITIONS:
        d = df[df["condition"] == c]
        g = d.groupby("angle")["stiffness"]
        ax.errorbar(g.mean().index, g.mean().values, yerr=g.sem().values,
                    fmt="o", capsize=3, color=COLORS[c], label=f"{c} (mean +/- SE)")
        ax.plot(grid, np.exp(predict_curve(fits[c], grid)),
                "-", color=COLORS[c], lw=2, alpha=0.8,
                label=f"{c} harmonic fit")
    ax.set_xlabel("Push angle [deg]")
    ax.set_ylabel("Stiffness [N/mm]")
    ax.set_xticks(ANGLES)
    ax.set_title("Harmonic fit of stiffness vs push angle (fit on log scale)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIT_PNG, dpi=150)
    print(f"\nSaved plot: {FIT_PNG}")


def plot_polar(fits):
    grid = np.linspace(0, 360, 361)
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="polar")
    for c in CONDITIONS:
        y = np.exp(predict_curve(fits[c], grid))
        ax.plot(np.deg2rad(grid), y, "-", color=COLORS[c], lw=2, label=c)
        # draw the 2nd-harmonic anisotropy axis
        if "axis2_deg" in fits[c]:
            a = fits[c]["axis2_deg"]
            r = np.nanmax(y) * 1.05
            for ang in (a, a + 180):
                ax.plot([np.deg2rad(ang)] * 2, [0, r], "--",
                        color=COLORS[c], lw=1.2, alpha=0.7)
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_title("Fitted stiffness profile + anisotropy axis (dashed)\n"
                 "(polar; radius = stiffness [N/mm])", fontsize=11)
    ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1.1))
    fig.tight_layout()
    fig.savefig(POLAR_PNG, dpi=150)
    print(f"Saved plot: {POLAR_PNG}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    df = load_data()
    print("\n--- Valid n per condition (raw) ---")
    print(df.groupby("condition")["stiffness"].agg(["count", "median", "std"]))

    df = prepare(df)

    # 1) Joint test: does the angular pattern differ between conditions at all?
    nested_interaction_test(df, harmonic_terms(), "JOINT (all harmonics)")
    # 2) Localize: directional asymmetry (1st) vs anisotropy axis (2nd).
    nested_interaction_test(df, ["h1c", "h1s"], "1st harmonic (directional asymmetry)")
    if N_HARM >= 2:
        nested_interaction_test(df, ["h2c", "h2s"], "2nd harmonic (anisotropy AXIS)")

    # Per-condition orientation
    fits = fit_per_condition(df)
    print("\n--- Per-condition harmonic geometry (log-scale fit) ---")
    for c in CONDITIONS:
        r = fits[c]
        line = (f"  {c:9s}: 1st-harm amp={r['A1']:.3f}, peak={r['peak1_deg']:.1f} deg")
        if "axis2_deg" in r:
            line += (f" | 2nd-harm amp={r['A2']:.3f}, "
                     f"axis={r['axis2_deg']:.1f} / {(r['axis2_deg']+180)%360:.0f} deg")
        print(line)

    plot_fit(df, fits)
    plot_polar(fits)

    print("\n========== SUMMARY ==========")
    print(f"Model: log(stiffness) ~ condition * {N_HARM} harmonics of push angle.")
    print(f"Magnitude difference is absorbed by the additive condition main effect")
    print(f"(log scale), so the interaction tests magnitude-independent SHAPE.")
    print(f"Library: statsmodels {sm.__version__}.")


if __name__ == "__main__":
    main()
