"""
Force Analysis中間プロット機能（回帰直線付き）
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
from scipy.stats import linregress

def plot_force_analysis_middle_with_regression(force_time, force_data, displacement_data, 
                                             contact_index, end_index, 
                                             velocity_data=None, peak_index=None,
                                             subject_id="", condition="", save_dir="force_analysis_plots"):
    """Force解析の中間結果をプロット（回帰直線付き）"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # 1. 力と変位の時間変化（2軸）
    ax1_force = axes[0]
    ax1_disp = ax1_force.twinx()
    
    ax1_force.plot(force_time, force_data, 'b-', label='Force', linewidth=2)
    ax1_disp.plot(force_time, displacement_data, 'r-', label='Displacement', linewidth=2)
    
    # 接触点と終了点の表示
    ax1_force.axvline(x=force_time[contact_index], color='g', linestyle='--', 
                     label=f'Contact (t={force_time[contact_index]:.3f}s)')
    ax1_force.axvline(x=force_time[end_index], color='k', linestyle='--', 
                     label=f'End (t={force_time[end_index]:.3f}s)')
    
    ax1_force.set_xlabel('Time [s]')
    ax1_force.set_ylabel('Force [N]', color='b')
    ax1_force.tick_params(axis='y', labelcolor='b')
    ax1_disp.set_ylabel('Displacement [mm]', color='r')
    ax1_disp.tick_params(axis='y', labelcolor='r')
    
    # 凡例の結合
    lines_1 = ax1_force.get_lines() + ax1_disp.get_lines()
    labels_1 = [l.get_label() for l in lines_1]
    ax1_force.legend(lines_1, labels_1, loc='upper left')
    ax1_force.grid(True, alpha=0.3)
    ax1_force.set_title('Force & Displacement vs Time')
    
    # 2. 速度プロット（あれば）
    if velocity_data is not None:
        axes[1].plot(force_time, velocity_data, 'g-', label='Velocity', linewidth=2)
        
        if peak_index is not None and peak_index < len(force_time):
            axes[1].plot(force_time[peak_index], velocity_data[peak_index], 'ro', 
                        markersize=8, label='Peak')
        
        axes[1].axvline(x=force_time[contact_index], color='g', linestyle='--', alpha=0.7)
        axes[1].axvline(x=force_time[end_index], color='k', linestyle='--', alpha=0.7)
        
        axes[1].set_xlabel('Time [s]')
        axes[1].set_ylabel('Velocity [mm/s]')
        axes[1].set_title('Velocity vs Time')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
    else:
        axes[1].axis('off')
        axes[1].text(0.5, 0.5, 'Velocity data\nnot available', 
                    ha='center', va='center', transform=axes[1].transAxes)
    
    # 3. 力-変位曲線（解析区間）+ 回帰直線
    analysis_force = force_data[contact_index:end_index+1]
    analysis_disp = displacement_data[contact_index:end_index+1]
    
    # 相対変位に変換（開始点を0にする）
    analysis_disp_relative = analysis_disp - analysis_disp[0]
    
    axes[2].scatter(analysis_disp_relative, analysis_force, c='b', alpha=0.6, s=20, label='Data points')
    axes[2].plot(analysis_disp_relative, analysis_force, 'b-', alpha=0.3)
    
    # 開始点と終了点をマーク
    axes[2].scatter(analysis_disp_relative[0], analysis_force[0], c='g', s=100, marker='o', 
                   label='Start', zorder=5)
    axes[2].scatter(analysis_disp_relative[-1], analysis_force[-1], c='k', s=100, marker='s', 
                   label='End', zorder=5)
    
    # 最小二乗法による回帰直線の計算と描画
    try:
        if len(analysis_disp_relative) >= 3:
            # 有効なデータ点のみを使用
            valid_mask = np.isfinite(analysis_force) & np.isfinite(analysis_disp_relative)
            
            if np.sum(valid_mask) >= 3:
                force_valid = analysis_force[valid_mask]
                disp_valid = analysis_disp_relative[valid_mask]
                
                # 回帰分析
                slope, intercept, r_value, p_value, std_err = linregress(disp_valid, force_valid)
                r_squared = r_value**2
                
                # 回帰直線の描画
                disp_range = np.linspace(np.min(disp_valid), np.max(disp_valid), 100)
                regression_line = slope * disp_range + intercept
                
                axes[2].plot(disp_range, regression_line, 'r-', linewidth=3, 
                            label=f'Regression Line', zorder=4)
                
                # 回帰情報をテキストボックスで表示
                regression_text = f'Stiffness: {slope:.2f} N/mm\n'
                regression_text += f'R²: {r_squared:.3f}\n'
                regression_text += f'Equation: y = {slope:.2f}x + {intercept:.2f}'
                
                # テキストボックスの位置を動的に決定
                x_text_pos = 0.05 if slope > 0 else 0.95
                text_ha = 'left' if slope > 0 else 'right'
                
                axes[2].text(x_text_pos, 0.95, regression_text, 
                           transform=axes[2].transAxes,
                           fontsize=10, verticalalignment='top', horizontalalignment=text_ha,
                           bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8))
                
                print(f"    Regression: 手首剛性={slope:.2f} N/mm, R²={r_squared:.3f}")
                
            else:
                print(f"    Warning: 有効データ不足（{np.sum(valid_mask)}点）")
        else:
            print(f"    Warning: データ点数不足（{len(analysis_disp_relative)}点）")
            
    except Exception as e:
        print(f"    Error: 回帰分析失敗 - {e}")
    
    axes[2].set_xlabel('Displacement [mm]')
    axes[2].set_ylabel('Force [N]')
    axes[2].set_title('Force vs Displacement (Analysis Region)')
    axes[2].legend(loc='best')
    axes[2].grid(True, alpha=0.3)
    
    # タイトル設定
    fig.suptitle(f'Force Analysis with Regression: {condition} - {subject_id}', fontsize=14)
    
    plt.tight_layout()
    
    # 保存
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{save_dir}/{condition}_{subject_id}_force_analysis_regression.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.close()

def plot_force_analysis_middle(force_time, force_data, displacement_data, 
                              contact_index, end_index, 
                              velocity_data=None, peak_index=None,
                              subject_id="", condition="", save_dir="force_analysis_plots"):
    """
    従来版との互換性を保つためのラッパー関数
    新版（回帰直線付き）を呼び出す
    """
    return plot_force_analysis_middle_with_regression(
        force_time, force_data, displacement_data, 
        contact_index, end_index, 
        velocity_data=velocity_data, peak_index=peak_index,
        subject_id=subject_id, condition=condition, save_dir=save_dir
    )

def plot_force_analysis_comparison(analysis_results_list, max_subjects=6):
    """
    複数被験者の力-変位関係と回帰直線を比較表示
    
    Parameters:
    -----------
    analysis_results_list : list
        各被験者の解析結果辞書のリスト
    max_subjects : int
        最大表示被験者数
    """
    print(f"複数被験者力-変位比較（最大{max_subjects}名）")
    
    if not analysis_results_list:
        print("比較対象データがありません")
        return
    
    # 表示する被験者数を制限
    plot_results = analysis_results_list[:max_subjects]
    n_subjects = len(plot_results)
    
    # グリッド計算
    cols = 3
    rows = (n_subjects + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(15, 5*rows))
    if rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()
    
    colors = {'Wrist_Contraction': '#1f77b4', 'Finger_Contraction': '#ff7f0e', 'Finger_Wrist_Contraction': '#2ca02c'}
    
    for i, result in enumerate(plot_results):
        ax = axes[i]
        
        # データ抽出
        force_time = result['force_time']
        force_data = result['force_data']
        displacement_data = result['displacement_data']
        contact_index = result['contact_index']
        end_index = result['end_index']
        subject_id = result.get('subject_id', f'Subject_{i+1}')
        condition = result.get('condition', 'Unknown')
        
        # 解析区間データ
        analysis_force = force_data[contact_index:end_index+1]
        analysis_disp = displacement_data[contact_index:end_index+1] - displacement_data[contact_index]
        
        # 散布図
        color = colors.get(condition, '#666666')
        ax.scatter(analysis_disp, analysis_force, alpha=0.6, color=color, s=30, 
                  edgecolors='black', linewidth=0.5)
        
        # 回帰直線
        try:
            if len(analysis_disp) >= 3:
                valid_mask = np.isfinite(analysis_force) & np.isfinite(analysis_disp)
                if np.sum(valid_mask) >= 3:
                    force_valid = analysis_force[valid_mask]
                    disp_valid = analysis_disp[valid_mask]
                    
                    slope, intercept, r_value, p_value, std_err = linregress(disp_valid, force_valid)
                    r_squared = r_value**2
                    
                    disp_range = np.linspace(np.min(disp_valid), np.max(disp_valid), 100)
                    regression_line = slope * disp_range + intercept
                    
                    ax.plot(disp_range, regression_line, 'r-', linewidth=2)
                    
                    # 条件名を日本語に変換
                    condition_jp = {'Wrist_Contraction': '手首収縮', 'Finger_Contraction': '指収縮', 
                                   'Finger_Wrist_Contraction': '指・手首収縮'}.get(condition, condition)
                    
                    ax.set_title(f'{subject_id} ({condition_jp})\n剛性={slope:.1f} N/mm, R²={r_squared:.3f}', 
                               fontsize=10)
                    
        except Exception as e:
            ax.set_title(f'{subject_id}\n回帰分析失敗', fontsize=10)
        
        ax.set_xlabel('Displacement [mm]')
        ax.set_ylabel('Force [N]')
        ax.grid(True, alpha=0.3)
    
    # 余ったサブプロットを非表示
    for i in range(n_subjects, len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.savefig('force_displacement_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
