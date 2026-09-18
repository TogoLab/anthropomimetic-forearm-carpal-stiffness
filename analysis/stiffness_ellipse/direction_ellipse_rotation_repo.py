"""
Stiffness-ellipse rotation test (Finger vs Combined) using the SAME ellipse
fit as the paper / repo: lib.fitting.fit_cartesian on the per-angle mean
stiffness, then the min/max-stiffness angles (angles of the closest/farthest
ellipse point from the origin), exactly as all_ellipse_fitting_stiffnes.py.

Inference added here (the repo only point-estimates the angles):
    statistic = circular difference of the MAX-stiffness angle between conditions
                (the rotation of the ellipse's stiff direction), in [0,180].
    1. Stratified PERMUTATION test: shuffle condition labels within each angle
       -> p(rotation >= observed).  Magnitude-free: the statistic is an angle.
    2. BOOTSTRAP (resample reps within condition x angle) -> 95% CI of rotation.

Cached long data results/direction_anova_long_data.csv (per-rep stiffness).
Run:  MPLBACKEND=Agg python direction_ellipse_rotation_repo.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lib import fitting

LONG_CSV = "results/direction_anova_long_data.csv"
ANGLES = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
PHYS_MIN = 5.0            # drop physically implausible near-zero artifacts
N_PERM = 5000
N_BOOT = 3000
SEED = 20250620
CONDS = ["Finger", "Combined"]
COLORS = {"Finger": "#1f77b4", "Combined": "#d62728"}
PNG = "results/direction_ellipse_rotation_repo.png"
PNG_NULL = "results/direction_ellipse_rotation_nulldist.png"


def ellipse_minmax_angles(mean_stiff):
    """Repo method: fit_cartesian on (r,theta)->(x,y); return (min_ang, max_ang) deg
    of the closest / farthest ellipse point from the origin."""
    theta = np.radians(ANGLES)
    r = np.asarray(mean_stiff, dtype=float)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    a, b, h, k, phi = fitting.fit_cartesian(x, y)
    t = np.linspace(0, 2 * np.pi, 10000)
    xe = h + a * np.cos(t) * np.cos(phi) - b * np.sin(t) * np.sin(phi)
    ye = k + a * np.cos(t) * np.sin(phi) + b * np.sin(t) * np.cos(phi)
    norm = np.hypot(xe, ye)
    min_ang = np.degrees(np.arctan2(ye[norm.argmin()], xe[norm.argmin()])) % 360
    max_ang = np.degrees(np.arctan2(ye[norm.argmax()], xe[norm.argmax()])) % 360
    return min_ang, max_ang, (a, b, h, k, phi)


def circ_diff(a, b):
    """Circular distance between two directions in [0,180]."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def mean_per_angle(stiff, ang):
    """Mean stiffness per angle, ordered by ANGLES (NaN-safe via reindex)."""
    s = pd.Series(stiff).groupby(ang).mean()
    return s.reindex(ANGLES).values


def plot_nulldist(null, observed, p_perm, n_perm, path):
    """Permutation null-distribution figure, tuned for legibility.

    Fixes vs the old version: focused x-range (the bulk lives in 0-60°), a
    white-boxed 95th-pct label, the tiny p-value tail made readable via a zoom
    inset, the tail count spelled out, and consistent p formatting.
    """
    null = np.asarray(null, float)
    pct95 = np.percentile(null, 95)
    XMAX = 70.0
    BW = 2.0                                   # bin width [deg]
    bins = np.arange(0, XMAX + BW, BW)
    tail_mask = null >= observed - 1e-9
    n_tail = int(tail_mask.sum())
    n_hidden = int((null > XMAX).sum())

    fig, ax = plt.subplots(figsize=(8, 4.6))
    counts, _, _ = ax.hist(null, bins=bins, color="#bbbbbb", edgecolor="white",
                           label="shuffled-label rotations (null)")
    tail = null[tail_mask & (null <= XMAX)]
    if tail.size:
        ax.hist(tail, bins=bins, color="#2ca02c", edgecolor="white",
                label=f"tail $\\geq$ observed  ({n_tail}/{len(null)},  p = {p_perm:.4f})")
    ymax = counts.max() * 1.08

    ax.axvline(observed, color="black", lw=2.2)
    ax.text(observed - 0.8, ymax * 0.80, f"observed\n{observed:.0f}° ", ha="right",
            va="top", fontsize=10, fontweight="bold")
    ax.axvline(pct95, color="#e69500", ls="--", lw=1.6)
    ax.text(pct95 - 0.8, ymax * 0.80, f"95th pct\n{pct95:.0f}° ", color="#e69500",
            ha="right", va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#e69500", alpha=0.9))

    ax.set_xlim(-2, XMAX)
    ax.set_ylim(0, ymax)
    ax.set_xlabel("Ellipse rotation |Δ max-stiffness angle| [deg]")
    ax.set_ylabel("Permutations (count)")
    ax.set_title(f"Permutation null distribution ({n_perm} label shuffles)\n"
                 f"observed {observed:.0f}° lies in the upper tail  →  p = {p_perm:.4f}",
                 fontsize=11)
    ax.legend(fontsize=9, loc="upper right")

    # zoom inset on the tail, parked in the empty bottom-right so it hides no bars
    axin = ax.inset_axes([0.80, 0.14, 0.18, 0.38])
    zlo, zhi = 46.0, 64.0
    zbins = np.arange(zlo, zhi + 1, 1.0)
    zmask = (null >= zlo) & (null <= zhi)
    zc, _, _ = axin.hist(null[zmask], bins=zbins, color="#bbbbbb", edgecolor="white")
    ztail = null[tail_mask & (null <= zhi)]
    if ztail.size:
        axin.hist(ztail, bins=zbins, color="#2ca02c", edgecolor="white")
    axin.axvline(observed, color="black", lw=1.8)
    axin.set_xlim(zlo, zhi)
    axin.set_ylim(0, max(5.0, (zc.max() if zc.size else 0) * 1.2))
    axin.set_title("tail zoom (46–64°)", fontsize=8)
    axin.set_ylabel("count", fontsize=8)
    axin.tick_params(labelsize=7)

    if n_hidden:
        ax.text(0.99, -0.20,
                f"{n_hidden} permutation(s) > {XMAX:.0f}° not shown (null max {null.max():.0f}°)",
                transform=ax.transAxes, ha="right", va="top", fontsize=7, color="#777777")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    return fig


def main():
    rng = np.random.default_rng(SEED)
    df = pd.read_csv(LONG_CSV)
    n0 = len(df)
    df = df[df["stiffness"] >= PHYS_MIN].reset_index(drop=True)
    if n0 - len(df):
        print(f"[filter] dropped {n0 - len(df)} trial(s) with stiffness < {PHYS_MIN}")

    cond = df["condition"].values
    ang = df["angle"].values
    K = df["stiffness"].values

    # ---- observed ----
    fit = {}
    for c in CONDS:
        m = cond == c
        mn, mx, params = ellipse_minmax_angles(mean_per_angle(K[m], ang[m]))
        fit[c] = dict(min=mn, max=mx, params=params)
        print(f"{c:9s}: max-stiffness angle = {mx:6.1f} deg, "
              f"min-stiffness angle = {mn:6.1f} deg")
    rot_max = circ_diff(fit["Finger"]["max"], fit["Combined"]["max"])
    rot_min = circ_diff(fit["Finger"]["min"], fit["Combined"]["min"])
    print(f"\nObserved rotation: Δmax = {rot_max:.1f} deg, Δmin = {rot_min:.1f} deg")

    # ---- 1. stratified permutation test (statistic = Δmax angle) ----
    idx_by_angle = [np.where(ang == a)[0] for a in np.unique(ang)]
    null = np.empty(N_PERM)
    for i in range(N_PERM):
        perm = cond.copy()
        for ix in idx_by_angle:
            perm[ix] = rng.permutation(cond[ix])
        _, mxf, _ = ellipse_minmax_angles(mean_per_angle(K[perm == "Finger"], ang[perm == "Finger"]))
        _, mxc, _ = ellipse_minmax_angles(mean_per_angle(K[perm == "Combined"], ang[perm == "Combined"]))
        null[i] = circ_diff(mxf, mxc)
    p_perm = (np.sum(null >= rot_max - 1e-9) + 1) / (N_PERM + 1)
    print(f"\n[Permutation] p(Δmax >= observed) = {p_perm:.4g}  "
          f"(null median {np.median(null):.1f}, 95th {np.percentile(null, 95):.1f} deg)")
    np.savez(PNG_NULL.replace(".png", ".npz"), null=null, observed=rot_max, p=p_perm)

    # ---- figure (B): permutation null distribution ----
    plot_nulldist(null, rot_max, p_perm, N_PERM, PNG_NULL)
    print(f"Saved plot: {PNG_NULL}")

    # ---- 2. bootstrap CI on Δmax ----
    keys = list(pd.DataFrame({"c": cond, "a": ang}).groupby(["c", "a"]).indices.values())
    boot = np.empty(N_BOOT)
    for i in range(N_BOOT):
        take = np.concatenate([rng.choice(v, size=len(v), replace=True) for v in keys])
        sc, sa, sk = cond[take], ang[take], K[take]
        _, mxf, _ = ellipse_minmax_angles(mean_per_angle(sk[sc == "Finger"], sa[sc == "Finger"]))
        _, mxc, _ = ellipse_minmax_angles(mean_per_angle(sk[sc == "Combined"], sa[sc == "Combined"]))
        boot[i] = circ_diff(mxf, mxc)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"[Bootstrap]   Δmax = {rot_max:.1f} deg, 95% CI [{lo:.1f}, {hi:.1f}]")

    # ---- figure: fitted ellipses (cartesian) + max-stiffness directions ----
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    t = np.linspace(0, 2 * np.pi, 1000)
    for c in CONDS:
        a, b, h, k, phi = fit[c]["params"]
        xe = h + a * np.cos(t) * np.cos(phi) - b * np.sin(t) * np.sin(phi)
        ye = k + a * np.cos(t) * np.sin(phi) + b * np.sin(t) * np.cos(phi)
        ax.plot(xe, ye, "-", color=COLORS[c], lw=2.5,
                label=f"{c} (max@{fit[c]['max']:.0f}°)")
        rmax = np.hypot(xe, ye).max()
        amx = np.radians(fit[c]["max"])
        ax.plot([0, rmax * np.cos(amx)], [0, rmax * np.sin(amx)], "--",
                color=COLORS[c], lw=1.6, alpha=0.8)
    ax.plot(0, 0, "k+", ms=10)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.set_xlabel("Palmar - Dorsal axis stiffness [N/m]")
    ax.set_ylabel("Radial - Ulnar axis stiffness [N/m]")
    ax.set_title(f"Stiffness ellipse: max-stiffness direction rotates {rot_max:.0f}°\n"
                 f"permutation p={p_perm:.3f}, 95% CI [{lo:.0f}, {hi:.0f}]°", fontsize=11)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PNG, dpi=150)
    print(f"\nSaved plot: {PNG}")

    print("\n========== SUMMARY ==========")
    print(f"Ellipse fit: lib.fitting.fit_cartesian on per-angle mean (paper method).")
    print(f"Max-stiffness angle: Finger {fit['Finger']['max']:.1f}° vs "
          f"Combined {fit['Combined']['max']:.1f}°  ->  rotation {rot_max:.1f}°")
    print(f"Permutation p = {p_perm:.4g}  ->  "
          f"{'SIGNIFICANT' if p_perm < 0.05 else 'n.s.'} at alpha=0.05")


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:
        # regenerate only the null-distribution figure from the cached .npz
        d = np.load(PNG_NULL.replace(".png", ".npz"))
        plot_nulldist(d["null"], float(d["observed"]), float(d["p"]), N_PERM, PNG_NULL)
        print(f"Replotted from cache: {PNG_NULL}")
    else:
        main()
