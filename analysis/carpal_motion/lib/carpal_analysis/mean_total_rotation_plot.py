"""
平均総回転量（3軸合成絶対相対角度の平均, mean_total_rotation）の条件比較棒グラフ

各骨について、被験者ごとの mean_total_rotation を条件平均±標準誤差で棒グラフ化する。
縦軸は3軸（X/Y/Z）を合成した相対角度ノルムの時間平均で、軸別ではない。
"""

import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib  # noqa: F401  日本語フォント


def calculate_standard_error(values):
    """標準誤差を計算する関数"""
    if len(values) == 0:
        return 0.0
    return np.std(values) / np.sqrt(len(values))


# 条件名 → 日本語ラベル
CONDITION_LABELS = {
    'Wrist_Contraction': '手首収縮',
    'Finger_Contraction': '指収縮',
    'Finger_Wrist_Contraction': '指・手首収縮',
}


def plot_mean_total_rotation_comparison(analysis_results,
                                        bone_names=['Scafoid', 'Capitate'],
                                        reference_bone='Lunate',
                                        measurement_distance=3.0,
                                        metric='mean_total_rotation',
                                        save_dir='pngs'):
    """平均総回転量の条件比較棒グラフ（骨ごとに1枚）

    Parameters
    ----------
    analysis_results : dict
        {condition: {bone_name: [ {'statistics': {...}}, ... ]}}
    bone_names : list[str]
        描画対象の骨
    reference_bone : str
        基準骨（タイトル表示用）
    measurement_distance : float
        解析区間（タイトル表示用）
    metric : str
        統計量キー。既定は 'mean_total_rotation'（3軸合成の平均）
    save_dir : str
        png 保存先ディレクトリ
    """
    import os

    conditions = list(analysis_results.keys())
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    for bone_name in bone_names:
        condition_means = []
        condition_ses = []
        condition_ns = []

        for condition in conditions:
            values = []
            bone_data = analysis_results.get(condition, {}).get(bone_name, [])
            for r in bone_data:
                stats = r.get('statistics', {})
                if metric in stats:
                    values.append(float(stats[metric]))

            if values:
                condition_means.append(np.mean(values))
                condition_ses.append(calculate_standard_error(values))
                condition_ns.append(len(values))
            else:
                condition_means.append(0.0)
                condition_ses.append(0.0)
                condition_ns.append(0)

        if not any(condition_ns):
            print(f"{bone_name}: 平均総回転量データがありません（metric='{metric}'）")
            continue

        labels = [CONDITION_LABELS.get(c, c) for c in conditions]

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_axisbelow(True)
        ax.grid(True, alpha=0.3)

        bars = ax.bar(labels, condition_means, yerr=condition_ses,
                      capsize=5, alpha=0.85, color=colors[:len(conditions)])

        # 各棒に平均値と n を表示
        for bar, mean, se, n in zip(bars, condition_means, condition_ses, condition_ns):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + se,
                    f'{mean:.2f}°\n(n={n})',
                    ha='center', va='bottom', fontsize=10)

        ax.set_title(f'{bone_name} vs {reference_bone} - 平均総回転量（3軸合成絶対相対角度の平均）'
                     f'\n解析区間: 0-{measurement_distance}mm, ±SE', fontsize=13)
        ax.set_ylabel('平均総回転量 (度)', fontsize=12)
        ax.set_xlabel('収縮条件', fontsize=12)

        plt.tight_layout()
        os.makedirs(save_dir, exist_ok=True)
        filename = f'{save_dir}/mean_total_rotation_{bone_name}_{measurement_distance}mm.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"  保存: {filename}")
        plt.show()
