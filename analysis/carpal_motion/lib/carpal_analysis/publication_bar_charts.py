"""
論文用の清書棒グラフ（英語ラベル）。

3種類の図を生成する:
  1. Relative translational [mm]  : Proximal carpal row (scaphoid--lunate) / Midcarpal joint (capitate--lunate)
  2. Relative rotation [deg]      : 同上
  3. Wrist joint stiffness [N/m]  : 3条件比較

条件: Wrist muscles / Finger muscles / Combined activation
  = Wrist_Contraction / Finger_Contraction / Finger_Wrist_Contraction
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import f_oneway, tukey_hsd

# 条件の並び順と英語ラベル
CONDITION_ORDER = ['Wrist_Contraction', 'Finger_Contraction', 'Finger_Wrist_Contraction']
CONDITION_LABELS = ['Wrist muscles', 'Finger muscles', 'Combined activation']
# x軸目盛りラベル用（大フォントでも重ならないよう2行に折り返す）
CONDITION_LABELS_WRAPPED = ['Wrist\nmuscles', 'Finger\nmuscles', 'Combined\nactivation']
BAR_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c']  # 青・橙・緑

# 骨ごとのパネル設定 (関節名と相対関係の表記)
BONE_PANELS = {
    'Scafoid': {'joint_translation': 'Proximal carpal row relative translational',
                'joint_rotation': 'Proximal carpal row relative rotation',
                'pair': '(scaphoid--lunate)'},
    'Capitate': {'joint_translation': 'Midcarpal joint relative translational',
                 'joint_rotation': 'Midcarpal joint relative  rotation',
                 'pair': '(capitate--lunate)'},
}


def _standard_error(values):
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return 0.0
    return np.std(values) / np.sqrt(values.size)


def _condition_value_lists(results, bone_name, metric):
    """条件ごとの被験者値リスト（np.array）を CONDITION_ORDER 順で返す。"""
    groups = []
    for condition in CONDITION_ORDER:
        vals = [r['statistics'][metric]
                for r in results.get(condition, {}).get(bone_name, [])
                if metric in r.get('statistics', {})]
        groups.append(np.asarray(vals, dtype=float))
    return groups


def _condition_mean_se(results, bone_name, metric):
    """results[condition][bone] の statistics[metric] を条件ごとに平均±SEで返す。"""
    groups = _condition_value_lists(results, bone_name, metric)
    means = [float(np.mean(g)) if g.size else 0.0 for g in groups]
    ses = [_standard_error(g) if g.size else 0.0 for g in groups]
    return means, ses


def _stars(p):
    """p値を有意差記号に変換。"""
    if p < 0.001:
        return '*** (p < 0.001)'
    if p < 0.01:
        return '** (p < 0.01)'
    if p < 0.05:
        return '* (p < 0.05)'
    return 'n.s.'


def _annotate_anova_tukey(ax, groups, means, ses, ylim_top, tag=''):
    """各パネルに 1元ANOVA の結果を表示し、有意なら Tukey HSD のペア比較ブラケットを描く。

    ANOVA注記テキストは常に最上部のブラケットより上に来るよう、必要な余白を
    先に計算してから y 軸上限を決める（テキストとブラケットの重なりを防止）。

    返り値: ブラケットとANOVA注記を収めるのに必要な y 軸上限（ylim_top 以上）。
    """
    valid = [g for g in groups if g.size >= 2]
    if len(valid) < 2:
        return ylim_top

    F, p = f_oneway(*groups)
    print(f"  [{tag}] 1-way ANOVA: F={F:.3f}, p={p:.4g}")

    base = max(m + s for m, s in zip(means, ses))
    step = ylim_top * 0.09
    tick = ylim_top * 0.02
    top_used = base

    sig_brackets = []
    if p < 0.05:
        # 事後検定 Tukey HSD（全ペア）
        res = tukey_hsd(*groups)
        pairs = sorted([(0, 1), (0, 2), (1, 2)], key=lambda ij: abs(ij[0] - ij[1]))
        level = 0
        for i, j in pairs:
            pij = float(res.pvalue[i, j])
            sig = pij < 0.05
            print(f"      Tukey {CONDITION_LABELS[i]} vs {CONDITION_LABELS[j]}: "
                  f"p={pij:.4g}{'  *' if sig else ''}")
            if sig:
                y = base + step * (level + 1)
                sig_brackets.append((i, j, y, pij))
                level += 1
                top_used = max(top_used, y + tick)

    # ANOVA注記（2行、大フォント）のための余白をブラケット上部に確保
    anova_gap = ylim_top * 0.34
    final_top = max(ylim_top, top_used + anova_gap)

    ax.text(0.03, 0.99, f'1-way ANOVA\nF = {F:.2f}, p = {p:.3g}',
            transform=ax.transAxes, va='top', ha='left', fontsize=34)

    for i, j, y, pij in sig_brackets:
        ax.plot([i, i, j, j], [y, y + tick, y + tick, y], lw=2.6, c='k')
        ax.text((i + j) / 2, y + tick, _stars(pij),
                ha='center', va='bottom', fontsize=32)

    return final_top


def _two_panel_bar(results, metric, ylabel, ylim, title_key, save_path):
    """Scafoid / Capitate の2パネル棒グラフを描く共通処理。

    論文では height=6cm で縮小表示されるため（元図の高さ7inに対し縮小率
    約0.34倍）、印刷後も本文と同程度に読めるようフォントを大きめに設定。
    """
    bones = ['Scafoid', 'Capitate']
    # constrained_layout の方が tight_layout より巨大フォントのはみ出しに強く、
    # savefig 時のテキスト欠け（切れ）を防げる。
    fig, axes = plt.subplots(1, 2, figsize=(19, 7.5), constrained_layout=True)

    for ax, bone in zip(axes, bones):
        groups = _condition_value_lists(results, bone, metric)
        means = [float(np.mean(g)) if g.size else 0.0 for g in groups]
        ses = [_standard_error(g) if g.size else 0.0 for g in groups]
        ax.set_axisbelow(True)
        ax.grid(True, axis='y', alpha=0.3)
        ax.bar(CONDITION_LABELS, means, yerr=ses, capsize=8,
               color=BAR_COLORS, edgecolor='black', linewidth=0.5)
        ax.set_xticks(range(len(CONDITION_LABELS)))
        ax.set_xticklabels(CONDITION_LABELS_WRAPPED)
        ax.set_ylabel(ylabel, fontsize=36)
        panel = BONE_PANELS[bone]
        ax.set_xlabel(f"{panel[title_key]}\n{panel['pair']}", fontsize=30, labelpad=14)
        ax.tick_params(axis='y', labelsize=30)
        ax.tick_params(axis='x', labelsize=25)
        # 1元ANOVA + Tukey事後検定
        new_top = _annotate_anova_tukey(ax, groups, means, ses, ylim[1],
                                        tag=f'{ylabel} / {bone}')
        ax.set_ylim(ylim[0], new_top)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
    print(f"  保存: {save_path}")
    plt.show()


def plot_relative_translation(translation_results, save_dir='pngs'):
    """1. Relative translational [mm]（最大3D相対変位）"""
    _two_panel_bar(
        translation_results,
        metric='max_displacement',
        ylabel='Relative translational [mm]',
        ylim=(0, 0.7),
        title_key='joint_translation',
        save_path=f'{save_dir}/relative_translational.png',
    )


def plot_relative_rotation(analysis_results, save_dir='pngs'):
    """2. Relative rotation [deg]（3軸合成の最大相対回転量）"""
    _two_panel_bar(
        analysis_results,
        metric='max_total_rotation',
        ylabel='Relative rotation [deg]',
        ylim=(0, 2.0),
        title_key='joint_rotation',
        save_path=f'{save_dir}/relative_rotation.png',
    )


def plot_wrist_joint_stiffness(stiffness_results, save_dir='pngs'):
    """3. Wrist joint stiffness [N/m]（条件比較）"""
    groups = []
    for condition in CONDITION_ORDER:
        vals = [r['stiffness'] * 1000  # N/mm -> N/m
                for r in stiffness_results.get(condition, [])
                if r is not None and 'stiffness' in r]
        groups.append(np.asarray(vals, dtype=float))
    means = [float(np.mean(g)) if g.size else 0.0 for g in groups]
    ses = [_standard_error(g) if g.size else 0.0 for g in groups]

    fig, ax = plt.subplots(figsize=(10.5, 8), constrained_layout=True)
    ax.set_axisbelow(True)
    ax.grid(True, axis='y', alpha=0.3)
    ax.bar(CONDITION_LABELS, means, yerr=ses, capsize=8,
           color=BAR_COLORS, edgecolor='black', linewidth=0.5)
    ax.set_xticks(range(len(CONDITION_LABELS)))
    ax.set_xticklabels(CONDITION_LABELS_WRAPPED)
    ax.set_ylabel('Wrist joint stiffness [N/m]', fontsize=36)
    ax.tick_params(axis='y', labelsize=30)
    ax.tick_params(axis='x', labelsize=25)
    # 1元ANOVA + Tukey事後検定
    new_top = _annotate_anova_tukey(ax, groups, means, ses, 70,
                                    tag='Wrist joint stiffness')
    ax.set_ylim(0, new_top)

    os.makedirs(save_dir, exist_ok=True)
    save_path = f'{save_dir}/wrist_joint_stiffness.png'
    fig.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
    print(f"  保存: {save_path}")
    plt.show()


def plot_all_publication_figures(analysis_results, translation_results, stiffness_results,
                                 save_dir='pngs'):
    """3図すべてを生成。"""
    print("=== 論文用棒グラフ生成 ===")
    plot_relative_translation(translation_results, save_dir=save_dir)
    plot_relative_rotation(analysis_results, save_dir=save_dir)
    plot_wrist_joint_stiffness(stiffness_results, save_dir=save_dir)
    print("論文用棒グラフを生成しました")
