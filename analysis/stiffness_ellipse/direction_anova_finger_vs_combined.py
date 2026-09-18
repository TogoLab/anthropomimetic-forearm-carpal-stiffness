"""
Direction (anisotropy orientation) comparison between Finger and Combined conditions.

Hypothesis (案1):
    Not the *magnitude* of stiffness, but its *direction* (the angle-dependent
    pattern / orientation of anisotropy) differs between the Finger condition and
    the Combined condition.

Method:
    1. Compute stiffness for 2 conditions x 12 angles x 8 repetitions.
    2. Normalize each condition by its own grand mean so overall scale -> 1
       (this removes the magnitude difference between conditions).
    3. Two-way ANOVA: stiffness_norm ~ C(condition) * C(angle), using Type II SS.
       The condition x angle INTERACTION term tests whether the angle-dependent
       pattern (= direction) differs between conditions after scale removal.
    4. Also run the raw (un-normalized) interaction for contrast.
    5. Plot normalized angle profiles (mean +/- SE) for both conditions.

Run with:  MPLBACKEND=Agg python direction_anova_finger_vs_combined.py
"""

import os
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lib.analyze import calcurate_sttiffness

import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE = "datas/normal/0202"
ANGLES = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
REPS = range(1, 9)  # 1..8
MEASUREMENT_DISTANCE = 3
USE_KALMAN = True

CONDITIONS = {
    "Finger":   {"dir": "finger_contraction",      "start_force": 0.6},
    "Combined": {"dir": "super_high_contraction",  "start_force": 0.7},
}

RESULTS_DIR = "results"
PNG_PATH = os.path.join(RESULTS_DIR, "direction_profile_finger_vs_combined.png")


# ---------------------------------------------------------------------------
# 1. Build long-format data
# ---------------------------------------------------------------------------
def build_long_data():
    rows = []
    for cond, cfg in CONDITIONS.items():
        d = cfg["dir"]
        sf = cfg["start_force"]
        for deg in ANGLES:
            for i in REPS:
                force_file = os.path.join(BASE, d, "force_gage", f"push_{deg}_deg_{i}.csv")
                motion_file = os.path.join(BASE, d, "motion_capture", f"Push_{deg}_deg_{str(i).zfill(3)}.csv")
                if not (os.path.exists(force_file) and os.path.exists(motion_file)):
                    print(f"[MISSING] {cond} {deg}deg rep{i}")
                    continue
                stiffness, error_file = calcurate_sttiffness(
                    force_file=force_file,
                    motion_file=motion_file,
                    start_force=sf,
                    measurement_distance=MEASUREMENT_DISTANCE,
                    middle_plot=False,
                    use_kalman=USE_KALMAN,
                )
                if error_file != "" or stiffness <= 0:
                    print(f"[INVALID] {cond} {deg}deg rep{i} stiffness={stiffness} err='{error_file}'")
                    continue
                rows.append({
                    "stiffness": float(stiffness),
                    "condition": cond,
                    "angle": int(deg),
                    "rep": int(i),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. Normalize by per-condition grand mean
# ---------------------------------------------------------------------------
def normalize(df):
    df = df.copy()
    gm = df.groupby("condition")["stiffness"].transform("mean")
    df["stiffness_norm"] = df["stiffness"] / gm
    return df


# ---------------------------------------------------------------------------
# 3+4. Two-way ANOVA (Type II)
# ---------------------------------------------------------------------------
def two_way_anova(df, response):
    model = smf.ols(f"{response} ~ C(condition) * C(angle)", data=df).fit()
    table = anova_lm(model, typ=2)
    return table


def report_interaction(table, label):
    row = table.loc["C(condition):C(angle)"]
    F = row["F"]
    p = row["PR(>F)"]
    print(f"\n=== {label}: condition x angle interaction ===")
    print(f"  F = {F:.4f}")
    print(f"  p = {p:.6g}")
    print(f"  significant (alpha=0.05): {'YES' if p < 0.05 else 'NO'}")
    return F, p


# ---------------------------------------------------------------------------
# 5. Plot normalized angle profiles
# ---------------------------------------------------------------------------
def plot_profiles(df):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"Finger": "tab:blue", "Combined": "tab:red"}
    for cond in CONDITIONS:
        sub = df[df["condition"] == cond]
        grp = sub.groupby("angle")["stiffness_norm"]
        means = grp.mean()
        sems = grp.sem()
        angles = means.index.values
        ax.errorbar(angles, means.values, yerr=sems.values,
                    marker="o", capsize=3, label=cond, color=colors.get(cond))
    ax.axhline(1.0, color="gray", ls="--", lw=0.8, alpha=0.7)
    ax.set_xlabel("Push angle [deg]")
    ax.set_ylabel("Normalized stiffness (cond grand mean = 1)")
    ax.set_title("Normalized stiffness angle profile: Finger vs Combined")
    ax.set_xticks(ANGLES)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(PNG_PATH, dpi=150)
    print(f"\nSaved plot: {PNG_PATH}")


# ---------------------------------------------------------------------------
# 6. Optional mixed-effects robustness check
#    Repetition block (rep) as random effect; condition & angle fixed.
# ---------------------------------------------------------------------------
def mixed_model_check(df):
    try:
        # group = rep block (1..8); pseudo-replication within angle blocks.
        md = smf.mixedlm(
            "stiffness_norm ~ C(condition) * C(angle)",
            data=df,
            groups=df["rep"],
        )
        mdf = md.fit(reml=True, method="lbfgs")
        # Wald test for the interaction terms
        inter_terms = [n for n in mdf.params.index if "C(condition)" in n and "C(angle)" in n]
        if inter_terms:
            import numpy as _np
            L = _np.zeros((len(inter_terms), len(mdf.params)))
            names = list(mdf.params.index)
            for r, t in enumerate(inter_terms):
                L[r, names.index(t)] = 1.0
            wald = mdf.wald_test(L, scalar=True)
            print("\n=== Mixed model robustness check (rep block as random effect) ===")
            print(f"  Joint Wald test on interaction terms: stat={float(wald.statistic):.4f}, p={float(wald.pvalue):.6g}")
            print(f"  Random-effect (rep) variance: {mdf.cov_re.values.ravel()}")
        return mdf
    except Exception as e:
        print(f"\n[mixed model skipped] {e}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Computing stiffness for all trials (this may take a while)...")
    df = build_long_data()

    print("\n--- Valid n per condition ---")
    print(df.groupby("condition")["stiffness"].agg(["count", "mean", "std"]))

    print("\n--- Cell mean stiffness (raw) [condition x angle] ---")
    pivot = df.pivot_table(index="angle", columns="condition", values="stiffness", aggfunc="mean")
    counts = df.pivot_table(index="angle", columns="condition", values="stiffness", aggfunc="count")
    print(pivot.round(1))
    print("\n--- Valid n per cell ---")
    print(counts.fillna(0).astype(int))

    df = normalize(df)

    # Raw interaction
    table_raw = two_way_anova(df, "stiffness")
    print("\n--- RAW two-way ANOVA table (Type II) ---")
    print(table_raw)
    F_raw, p_raw = report_interaction(table_raw, "RAW (un-normalized)")

    # Normalized interaction
    table_norm = two_way_anova(df, "stiffness_norm")
    print("\n--- NORMALIZED two-way ANOVA table (Type II) ---")
    print(table_norm)
    F_norm, p_norm = report_interaction(table_norm, "NORMALIZED")

    plot_profiles(df)

    mixed_model_check(df)

    # Save the long data for reuse
    out_csv = os.path.join(RESULTS_DIR, "direction_anova_long_data.csv")
    df.to_csv(out_csv, index=False)
    print(f"\nSaved long data: {out_csv}")

    print("\n========== SUMMARY ==========")
    print(f"Normalization: divide by per-condition grand mean (scale -> 1).")
    print(f"SS type: Type II (statsmodels anova_lm typ=2).")
    print(f"Library: statsmodels {sm.__version__}.")
    print(f"NORMALIZED interaction: F={F_norm:.4f}, p={p_norm:.6g} "
          f"-> {'SIGNIFICANT' if p_norm < 0.05 else 'n.s.'}")
    print(f"RAW interaction:        F={F_raw:.4f}, p={p_raw:.6g} "
          f"-> {'SIGNIFICANT' if p_raw < 0.05 else 'n.s.'}")


if __name__ == "__main__":
    main()
