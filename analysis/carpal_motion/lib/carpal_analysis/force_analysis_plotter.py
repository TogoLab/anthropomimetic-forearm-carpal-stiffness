"""
Force Analysis中間プロット機能（整理版）
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

def plot_force_analysis_middle(force_time, force_data, displacement_data, 
                              contact_index, end_index, 
                              velocity_data=None, peak_index=None,
                              subject_id="", condition="", save_dir="force_analysis_plots"):
    """Force解析の中間結果をプロット"""
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
    
    # 3. 力-変位曲線（解析区間）
    analysis_force = force_data[contact_index:end_index+1]
    analysis_disp = displacement_data[contact_index:end_index+1]
    
    axes[2].scatter(analysis_disp, analysis_force, c='b', alpha=0.6, s=20)
    axes[2].plot(analysis_disp, analysis_force, 'b-', alpha=0.3)
    
    # 開始点と終了点をマーク
    axes[2].scatter(analysis_disp[0], analysis_force[0], c='g', s=100, marker='o', 
                   label='Start', zorder=5)
    axes[2].scatter(analysis_disp[-1], analysis_force[-1], c='k', s=100, marker='s', 
                   label='End', zorder=5)
    
    axes[2].set_xlabel('Displacement [mm]')
    axes[2].set_ylabel('Force [N]')
    axes[2].set_title('Force vs Displacement (Analysis Region)')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    # タイトル設定
    fig.suptitle(f'Force Analysis: {condition} - {subject_id}', fontsize=14)
    
    plt.tight_layout()
    
    # 保存
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{save_dir}/{condition}_{subject_id}_force_analysis.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.close()