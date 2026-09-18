# Wrist Stiffness & Carpal Motion — Experimental Data and Analysis Code

Experimental data and analysis programs for the figures reported in the paper on
adaptive wrist stiffness modulation of a tendon-driven musculoskeletal hand.

Everything here is a verbatim copy of the working repository, restricted to the
data and code actually used for the published figures. Source files are
unmodified; console output and inline comments are in Japanese.

---

## 1. Contents

```
analysis/
├── README.md
├── requirements.txt
│
├── stiffness_ellipse/                   # Wrist stiffness ellipse experiment
│   ├── all_ellipse_fitting_stiffnes.py  #   main program
│   ├── lib/
│   │   ├── analyze.py                   #   force/displacement -> stiffness per push direction
│   │   ├── fitting.py                   #   least-squares ellipse fit (Cartesian form)
│   │   └── utils.py                      #   measurement angles, CSV column layout
│   ├── direction_ellipse_rotation_repo.py        # STATS: permutation test (paper result)
│   ├── direction_anova_finger_vs_combined.py     # STATS: two-way ANOVA + long-data builder
│   ├── direction_harmonic_finger_vs_combined.py  # STATS: harmonic nested-F test
│   ├── direction_statistics_methods.md           # STATS: methods write-up (Japanese)
│   ├── datas/
│   │   ├── normal/0202/                  #   (1) Normal skeleton
│   │   ├── fixed_bone/0220/              #   (2) Fused proximal row
│   │   └── ellipse_carpal/0223/          #   (3) Geometric ellipsoidal skeleton
│   ├── results/
│   │   ├── direction_anova_long_data.csv #   cached per-trial stiffness (input to the stats)
│   │   └── ellipse/                      #   output (empty; created on run)
│   └── pngs/force_distance/              #   per-trial debug plots (middle_plot=True)
│
├── carpal_motion/                       # Intra-carpal motion experiment
│   ├── main_publication_figures.py       #   main program (figures for the paper)
│   ├── main_with_stiffness.py            #   analysis pipeline it drives
│   ├── lib/carpal_analysis/              #   loaders, angle/translation/stiffness analysis
│   │   └── publication_bar_charts.py     #   STATS: one-way ANOVA + Tukey HSD, plotting
│   ├── datas/carpal_motion/20250803/     #   measurement session used in the paper
│   └── pngs/                             #   output (empty; created on run)
│
└── figures_in_paper/                    # reference outputs, for comparison
    ├── result_normal.png
    ├── result_fixed_carpal.png
    ├── result_ellipsoidal_carpal.png
    ├── carpal_relative_rotation.png
    ├── carpal_relative_translational_motion.png
    ├── wrist_stiffness.png
    └── fullres_ellipse/                  #   full-resolution PNG/SVG of the ellipse plots
```

Total size ≈ 194 MB (2,424 CSV files).

## 2. Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`japanize-matplotlib` is required only because the plotting helpers import it;
it does not affect the English figure labels.

---

## 3. Experiment 1 — Wrist stiffness ellipse

The hand was pushed by a force gauge from 12 directions in the transverse plane
(0°–330°, every 30°) under four muscle activation conditions. Stiffness per
direction is estimated from the force–displacement slope, and an ellipse is
fitted to the resulting polar stiffness profile.

### Run

```bash
cd stiffness_ellipse
python all_ellipse_fitting_stiffnes.py
```

The skeleton type is selected by the `data_dir` variable at
[all_ellipse_fitting_stiffnes.py:17-19](stiffness_ellipse/all_ellipse_fitting_stiffnes.py#L17-L19).
Uncomment the one you want:

| `data_dir`                    | Skeleton                         | Paper figure                   |
| ----------------------------- | -------------------------------- | ------------------------------ |
| `./datas/normal/0202/`        | Normal (8 mobile carpal bones)   | `result_normal.png`            |
| `./datas/fixed_bone/0220/`    | Fused proximal row               | `result_fixed_carpal.png`      |
| `./datas/ellipse_carpal/0223/`| Geometric ellipsoidal skeleton   | `result_ellipsoidal_carpal.png`|

Analysis parameters are identical for all three skeletons:
`start_force = [0.15, 0.2, 0.6, 0.7]` N (per condition, in the order
low / high / finger / super_high) and `measurement_distance = 3` mm.

### Output

- `results/ellipse/ellipse_cartesian_<skeleton>.png` / `.svg` — the fitted ellipses
- `results/ellipse/mean_and_std/<skeleton>_<condition>.png` — mean ± SD bar chart per direction
- `results/ellipse/param/<skeleton>_error_files.txt` — trials rejected by contact detection
- `pngs/force_distance/…` — per-trial force–displacement plots (`middle_plot=True`; ~2,300 PNGs, a few hundred MB)

The script ends with an interactive `plt.show(block=True)` using the `TkAgg`
backend. The figures in the paper were captured from that window, which is why
the axis range there is ±300 N/m rather than the ±600 N/m of the saved PNG; the
ellipses themselves are identical. On a headless machine, change
`matplotlib.use('TkAgg')` on line 5 to `matplotlib.use('Agg')` and the saved
files are still produced.

### Conditions

| Directory              | Label in figures           | Activation                         |
| ---------------------- | -------------------------- | ---------------------------------- |
| `low_contraction`      | Relax                      | no activation                      |
| `high_contraction`     | Wrist Muscle               | wrist muscles only                 |
| `finger_contraction`   | Finger Muscle              | finger muscles only                |
| `super_high_contraction`| Wrist and Finger Muscles  | wrist + finger muscles             |

Each condition holds `force_gage/` and `motion_capture/`, 8 trials × 12
directions (`push_<angle>_deg_<trial>.csv` and `Push_<angle>_deg_<nnn>.csv`).

---

## 4. Experiment 2 — Intra-carpal motion

Optical markers on the radius, lunate, scaphoid and capitate were tracked while
the wrist was pushed, under three activation conditions. Scaphoid and capitate
motion is expressed relative to the lunate frame.

### Run

```bash
cd carpal_motion
python main_publication_figures.py
```

No arguments; the measurement session is fixed to `datas/carpal_motion/20250803/`
at [main_with_stiffness.py:648-661](carpal_motion/main_with_stiffness.py#L648-L661).
Runtime is a few minutes.

### Output

| File                        | Paper figure                                |
| --------------------------- | ------------------------------------------- |
| `pngs/relative_rotation.png`| `carpal_relative_rotation.png`              |
| `pngs/relative_translational.png` | `carpal_relative_translational_motion.png` |
| `pngs/wrist_joint_stiffness.png`  | `wrist_stiffness.png`                 |

These three reproduce byte-for-byte (verified by MD5) against the copies in
`figures_in_paper/`. One-way ANOVA and Tukey HSD (`scipy.stats.tukey_hsd`) are
computed and annotated on each panel; the test statistics are printed to stdout.

### Conditions

| Directory                  | Label in figures     | Files            |
| -------------------------- | -------------------- | ---------------- |
| `wrist_contraction`        | Wrist muscles        | `Wrist_*.csv`    |
| `finger_contraction`       | Finger muscles       | `Finger_*.csv`   |
| `finger_wrist_contraction` | Combined activation  | `FingerWrist_*.csv` |

20 trials per condition, in `force_gage/` and `motion_capture/`.

---

## 5. Statistical tests

Two statistical results are reported in the paper, produced by two different
programs.

### 5.1 Ellipse reorientation — stratified permutation test

*Section "Analysis Method"; Results: "Δθ_max = 48.2°, exceeded all but 18 of
5000 label-shuffled null rotations (p = 0.0038)".*

```bash
cd stiffness_ellipse
MPLBACKEND=Agg python direction_ellipse_rotation_repo.py
```

Tests whether the maximum-stiffness direction θ_max of the normal skeleton
really differs between finger-muscle and combined activation, or whether the
shift is trial-to-trial noise. Per-trial stiffness values are pooled across the
two conditions and the condition label is shuffled **within each of the 12
loading directions** (5000 times, `SEED = 20250620`), refitting the ellipse with
the same `lib.fitting.fit_cartesian` used for the paper figures and recomputing
the circular difference in θ_max each time. Trials below 5 N/m are dropped, as
in the main analysis. A bootstrap 95 % CI (3000 resamples) is also printed.

Expected output — reproduced exactly on a fresh run:

```
Finger   : max-stiffness angle =  254.0 deg, min-stiffness angle =  151.7 deg
Combined : max-stiffness angle =  302.2 deg, min-stiffness angle =  197.9 deg
Observed rotation: Δmax = 48.2 deg, Δmin = 46.3 deg
[Permutation] p(Δmax >= observed) = 0.003799  (null median 16.6, 95th 37.5 deg)
[Bootstrap]   Δmax = 48.2 deg, 95% CI [23.8, 176.3]
```

The four angles match the normal-skeleton rows of Table "Stiffness ellipse
parameters for normal skeleton" (finger and combined conditions). p = 0.003799
is (18 + 1) / (5000 + 1), reported as p = 0.0038.

Outputs `results/direction_ellipse_rotation_repo.png` (the two ellipses with
their max-stiffness directions), `results/direction_ellipse_rotation_nulldist.png`
(the null distribution) and the matching `.npz` cache; rerunning with
`--replot` redraws the null-distribution figure from that cache.

Input is `results/direction_anova_long_data.csv` — per-trial stiffness in long
format (`stiffness, condition, angle, rep`), shipped here so the test runs in
about a minute. To rebuild it from the raw CSVs instead (slow), run
`direction_anova_finger_vs_combined.py`, which writes the same file.

### 5.2 Carpal motion — one-way ANOVA + Tukey HSD

*Results: "F = 6.69, p = 0.0025" for wrist joint stiffness, "F = 3.89,
p = 0.026" and "F = 5.92, p = 0.0046" for proximal row relative rotation and
translation, with the Tukey HSD pairwise p-values.*

These are computed inside
[publication_bar_charts.py](carpal_motion/lib/carpal_analysis/publication_bar_charts.py)
(`scipy.stats.f_oneway` and `scipy.stats.tukey_hsd`) and annotated directly onto
the bars, so they come out of the `main_publication_figures.py` run in Section 4;
the statistics are also printed to stdout:

```
[Wrist joint stiffness] 1-way ANOVA: F=6.694, p=0.002447
    Tukey Wrist muscles vs Combined activation: p=0.001632  *
[Relative rotation [deg] / Scafoid] 1-way ANOVA: F=3.886, p=0.02619
[Relative translational [mm] / Scafoid] 1-way ANOVA: F=5.918, p=0.004621
```

### 5.3 Supporting tests (not reported in the paper)

[direction_statistics_methods.md](stiffness_ellipse/direction_statistics_methods.md)
documents the three direction tests that were run during the analysis, of which
only the third became the reported result. The other two are included here for
completeness:

| Script | Test | Status |
| ------ | ---- | ------ |
| `direction_anova_finger_vs_combined.py` | Two-way ANOVA, condition × angle interaction (Type II SS, scale-normalized) | not reported; also builds the cached long-format CSV |
| `direction_harmonic_finger_vs_combined.py` | Harmonic (circular) model, nested F test on the 1st/2nd order terms | not reported |
| `direction_ellipse_rotation_repo.py` | Stratified permutation test on Δθ_max | **reported (Section 5.1)** |

Both supporting scripts require `statsmodels`; the reported permutation test
does not.

---

## 6. Data formats

### `motion_capture/*.csv` — OptiTrack Motive export

Standard Motive CSV, version 1.24. 100 Hz, millimetres, quaternion rotation.
Rows 1–7 are the header block (take metadata, rigid-body names, IDs, the
Rotation/Position channel labels, and the column names
`Frame, Time (Seconds), X, Y, Z, W, X, Y, Z, …` repeating per rigid body);
measurement rows start at row 8.

- Experiment 1: a single rigid body on the hand.
- Experiment 2: `Lunate`, `Scafoid`, `ForceGage`, `Radius`, `Capitate`.
  (`Scafoid` is the spelling used throughout the code and the raw data.)

### `force_gage/*.csv` — motor state and force gauge, no header row

46 columns, defined in [utils.py](stiffness_ellipse/lib/utils.py):

| Column   | Meaning                                        |
| -------- | ---------------------------------------------- |
| 1        | `timestamp` [ms]                               |
| 2–45     | `curr1, pos1, curr2, pos2, … curr22, pos22` — current and position of the 22 tendon-driving motors |
| 46       | `Force` [N] — force gauge reading              |

---

## 7. Notes for reuse

- Both programs use relative paths and must be run from their own directory
  (`stiffness_ellipse/` and `carpal_motion/` respectively).
- No absolute paths are embedded anywhere in the code.
- All CSV files are bit-identical to the originals used for the paper
  (verified by MD5 over all 2,424 files).
- Trials listed in `results/ellipse/param/*_error_files.txt` are automatically
  excluded by the contact-detection step in `lib/analyze.py`; they are still
  shipped here so the rejection can be re-examined.
