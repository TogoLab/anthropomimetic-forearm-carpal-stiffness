"""
論文用の3つの棒グラフ（英語ラベル）を生成する専用プログラム。

  1. Relative translational [mm]  (scaphoid--lunate / capitate--lunate)
  2. Relative rotation [deg]       (scaphoid--lunate / capitate--lunate)
  3. Wrist joint stiffness [N/m]

既存の剛性解析パイプライン（main_with_stiffness.py）を visualize=False で再利用し、
解析結果のみ取得して論文用グラフだけを描画する。
"""

from main_with_stiffness import main_enhanced_analysis_with_translation_and_stiffness
from lib.carpal_analysis.publication_bar_charts import plot_all_publication_figures


def main():
    analysis_results, translation_results, stiffness_results = \
        main_enhanced_analysis_with_translation_and_stiffness(
            middle_plot=False,
            apply_smoothing=True,
            apply_advanced_filtering=True,
            analysis_delay_seconds=0.5,  # main_with_stiffness.py の __main__ と一致（目標図と同条件）
            visualize=False,
        )

    if not analysis_results:
        print("解析結果が得られませんでした")
        return

    plot_all_publication_figures(analysis_results, translation_results, stiffness_results)


if __name__ == "__main__":
    main()
