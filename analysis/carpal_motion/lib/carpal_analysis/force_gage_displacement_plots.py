"""
ForceGage変位を横軸とした可視化関数（整理版）
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def calculate_standard_error(values):
    """標準誤差を計算する関数"""
    if len(values) == 0:
        return 0.0
    return np.std(values) / np.sqrt(len(values))

def plot_angles_vs_force_gage_displacement(analysis_results, bone_names=['Scafoid', 'Capitate'], reference_bone='Lunate'):
    """ForceGage変位を横軸とした相対角度変化のプロット（標準誤差対応版）"""
    try:
        conditions = list(analysis_results.keys())
        axis_names = ['X', 'Y', 'Z']
        axis_names_jp = ['X軸回転角度', 'Y軸回転角度', 'Z軸回転角度']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        print(f"ForceGage変位ベース角度解析: {len(conditions)}条件, {len(bone_names)}骨")
        

        for bone_name in bone_names:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'{bone_name} vs {reference_bone} - ForceGage変位に対する相対角度変化（標準誤差表示）', fontsize=16)
            
            # XYZ軸別の相対角度（左上、右上、左下）
            for axis_idx in range(3):
                ax = axes[axis_idx//2, axis_idx%2] if axis_idx < 2 else axes[1, 0]
                axis_name = axis_names[axis_idx]
                axis_name_jp = axis_names_jp[axis_idx]
                
                stats_text = []
                
                for condition_idx, condition in enumerate(conditions):
                    if condition in analysis_results and bone_name in analysis_results[condition]:
                        bone_data = analysis_results[condition][bone_name]
                        
                        # ForceGage変位データがある被験者のみ処理
                        valid_subjects = []
                        for result in bone_data:
                            if result.get('force_gage_displacement') is not None and result.get('used_enhanced_method', False):
                                valid_subjects.append(result)
                        
                        if valid_subjects:
                            print(f"  {condition} - {bone_name}: {len(valid_subjects)}名のForceGage変位データ使用")
                            
                            # 共通のForceGage変位軸を作成
                            common_displacement = np.linspace(0, 5.0, 100)
                            
                            interpolated_angles = []
                            
                            for result in valid_subjects:
                                fg_disp = result['force_gage_displacement']
                                angles = result['relative_angles']
                                
                                if len(fg_disp) == len(angles):
                                    if len(fg_disp) > 1:
                                        try:
                                            # ForceGage変位に対して角度を補間
                                            interp_func = interp1d(fg_disp, angles[:, axis_idx], 
                                                                 kind='linear', bounds_error=False, fill_value='extrapolate')
                                            interpolated_angle = interp_func(common_displacement)
                                            interpolated_angles.append(interpolated_angle)
                                        except Exception as e:
                                            print(f"    補間エラー: {e}")
                                else:
                                    print(f"    データ長不一致: ForceGage={len(fg_disp)}, Angles={len(angles)}")
                            
                            if interpolated_angles:
                                interpolated_angles = np.array(interpolated_angles)
                                mean_angles = np.mean(interpolated_angles, axis=0)
                                se_angles = np.array([calculate_standard_error(interpolated_angles[:, i]) 
                                                    for i in range(len(common_displacement))])
                                
                                color = colors[condition_idx % len(colors)]
                                linestyle_options = ['-', '--', '-.', ':']
                                linestyle = linestyle_options[condition_idx % len(linestyle_options)]
                                
                                # 平均線をプロット
                                ax.plot(common_displacement, mean_angles,
                                       label=f'{condition} (n={len(interpolated_angles)})',
                                       linewidth=3, color=color, linestyle=linestyle)
                                
                                # 標準誤差の帯
                                ax.fill_between(common_displacement,
                                               mean_angles - se_angles,
                                               mean_angles + se_angles,
                                               alpha=0.2, color=color)
                                
                                # 統計情報
                                max_angle = np.max(np.abs(mean_angles))
                                final_angle = mean_angles[-1]
                                stats_text.append(f'{condition}: 最大={max_angle:.2f}°, 最終={final_angle:.2f}°')
                
                # グラフ設定
                ax.set_title(f'{axis_name_jp} vs ForceGage変位', fontsize=14)
                ax.set_xlabel('ForceGage変位 (mm)', fontsize=12)
                ax.set_ylabel(f'{axis_name}軸相対角度 (°)', fontsize=12)
                ax.legend(loc='best', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
                
                # 統計情報表示
                if stats_text:
                    stats_str = '\n'.join(stats_text)
                    ax.text(0.02, 0.98, stats_str, transform=ax.transAxes,
                           fontsize=10, verticalalignment='top',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.8))
            
            # **NEW: 角度ノルム（総回転量）プロット（右下）**
            ax = axes[1, 1]
            
            norm_stats_text = []
            
            for condition_idx, condition in enumerate(conditions):
                if condition in analysis_results and bone_name in analysis_results[condition]:
                    bone_data = analysis_results[condition][bone_name]
                    
                    valid_subjects = []
                    for result in bone_data:
                        if result.get('force_gage_displacement') is not None and result.get('used_enhanced_method', False):
                            valid_subjects.append(result)
                    
                    if valid_subjects:
                        common_displacement = np.linspace(0, 5.0, 100)
                        interpolated_norms = []
                        
                        for result in valid_subjects:
                            fg_disp = result['force_gage_displacement']
                            angles = result['relative_angles']
                            
                            if len(fg_disp) == len(angles):
                                if len(fg_disp) > 1:
                                    try:
                                        # 角度ノルム（総回転量）を計算
                                        angle_norms = np.linalg.norm(angles, axis=1)
                                        
                                        # ForceGage変位に対して総回転量を補間
                                        interp_func = interp1d(fg_disp, angle_norms, 
                                                             kind='linear', bounds_error=False, fill_value='extrapolate')
                                        interpolated_norm = interp_func(common_displacement)
                                        interpolated_norms.append(interpolated_norm)
                                    except Exception as e:
                                        print(f"    総回転量補間エラー: {e}")
                        
                        if interpolated_norms:
                            interpolated_norms = np.array(interpolated_norms)
                            mean_norms = np.mean(interpolated_norms, axis=0)
                            se_norms = np.array([calculate_standard_error(interpolated_norms[:, i]) 
                                               for i in range(len(common_displacement))])
                            
                            color = colors[condition_idx % len(colors)]
                            linestyle_options = ['-', '--', '-.', ':']
                            linestyle = linestyle_options[condition_idx % len(linestyle_options)]
                            
                            ax.plot(common_displacement, mean_norms,
                                   label=f'{condition} (n={len(interpolated_norms)})',
                                   linewidth=3, color=color, linestyle=linestyle)
                            
                            ax.fill_between(common_displacement,
                                           mean_norms - se_norms,
                                           mean_norms + se_norms,
                                           alpha=0.2, color=color)
                            
                            # 統計情報
                            max_norm = np.max(mean_norms)
                            final_norm = mean_norms[-1]
                            norm_stats_text.append(f'{condition}: 最大={max_norm:.2f}°, 最終={final_norm:.2f}°')
            
            ax.set_title(f'総回転量（角度ノルム）vs ForceGage変位', fontsize=14)
            ax.set_xlabel('ForceGage変位 (mm)', fontsize=12)
            ax.set_ylabel('総回転量 (°)', fontsize=12)
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # 統計情報表示
            if norm_stats_text:
                stats_str = '\n'.join(norm_stats_text)
                ax.text(0.02, 0.98, stats_str, transform=ax.transAxes,
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcyan', alpha=0.8))
            
            plt.tight_layout()
            plt.savefig(f'angles_vs_force_gage_displacement_{bone_name}_SE.png', dpi=300, bbox_inches='tight')
            plt.show()
            
    except Exception as e:
        print(f"Error in plot_angles_vs_force_gage_displacement: {e}")
        import traceback
        traceback.print_exc()

def plot_translation_vs_force_gage_displacement(translation_results, bone_names=['Capitate', 'Scafoid'], reference_bone='Lunate'):
    """ForceGage変位を横軸とした相対並進変位のプロット（標準誤差対応版）"""
    try:
        conditions = list(translation_results.keys())
        axis_names = ['X', 'Y', 'Z']
        axis_names_jp = ['X軸相対変位', 'Y軸相対変位', 'Z軸相対変位']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        print(f"ForceGage変位ベース並進解析: {len(conditions)}条件, {len(bone_names)}骨")
        
        for bone_name in bone_names:
            if bone_name == reference_bone:
                continue
                
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'{bone_name} vs {reference_bone} - ForceGage変位に対する相対並進変位（標準誤差表示）', fontsize=16)
            
            # XYZ軸別の相対変位
            for axis_idx in range(3):
                ax = axes[axis_idx//2, axis_idx%2] if axis_idx < 2 else axes[1, 0]
                axis_name = axis_names[axis_idx]
                axis_name_jp = axis_names_jp[axis_idx]
                
                stats_text = []
                
                for condition_idx, condition in enumerate(conditions):
                    if condition in translation_results and bone_name in translation_results[condition]:
                        bone_data = translation_results[condition][bone_name]
                        
                        # ForceGage変位データがある被験者のみ処理
                        valid_subjects = []
                        for result in bone_data:
                            if result.get('force_gage_displacement') is not None:
                                valid_subjects.append(result)
                        
                        if valid_subjects:
                            print(f"  {condition} - {bone_name}: {len(valid_subjects)}名のForceGage変位データ使用")
                            
                            # 共通のForceGage変位軸を作成
                            common_displacement = np.linspace(0, 5.0, 100)
                            
                            interpolated_displacements = []
                            
                            for result in valid_subjects:
                                fg_disp = result['force_gage_displacement']
                                relative_disp = result.get('relative_displacement', result.get('displacement'))
                                
                                if relative_disp is not None and len(fg_disp) == len(relative_disp):
                                    if len(fg_disp) > 1:
                                        try:
                                            # ForceGage変位に対して相対変位を補間
                                            interp_func = interp1d(fg_disp, relative_disp[:, axis_idx], 
                                                                 kind='linear', bounds_error=False, fill_value='extrapolate')
                                            interpolated_disp = interp_func(common_displacement)
                                            interpolated_displacements.append(interpolated_disp)
                                        except Exception as e:
                                            print(f"    補間エラー: {e}")
                            
                            if interpolated_displacements:
                                interpolated_displacements = np.array(interpolated_displacements)
                                mean_displacements = np.mean(interpolated_displacements, axis=0)
                                se_displacements = np.array([calculate_standard_error(interpolated_displacements[:, i]) 
                                                           for i in range(len(common_displacement))])
                                
                                color = colors[condition_idx % len(colors)]
                                linestyle_options = ['-', '--', '-.', ':']
                                linestyle = linestyle_options[condition_idx % len(linestyle_options)]
                                
                                # 平均線をプロット
                                ax.plot(common_displacement, mean_displacements,
                                       label=f'{condition}',
                                       linewidth=3, color=color, linestyle=linestyle)
                                
                                # 標準誤差の帯
                                ax.fill_between(common_displacement,
                                               mean_displacements - se_displacements,
                                               mean_displacements + se_displacements,
                                               alpha=0.2, color=color)
                                
                                # 統計情報
                                max_disp = np.max(np.abs(mean_displacements))
                                final_disp = mean_displacements[-1]
                                stats_text.append(f'{condition}: 最大={max_disp:.2f}mm, 最終={final_disp:.2f}mm')
                
                # グラフ設定
                ax.set_title(f'{axis_name_jp} vs ForceGage変位', fontsize=14)
                ax.set_xlabel('ForceGage変位 (mm)', fontsize=12)
                ax.set_ylabel(f'{axis_name}軸相対変位 (mm)', fontsize=12)
                ax.legend(loc='best', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
                
                # 統計情報表示
                if stats_text:
                    stats_str = '\n'.join(stats_text)
                    ax.text(0.02, 0.98, stats_str, transform=ax.transAxes,
                           fontsize=10, verticalalignment='top',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.8))
            
            # 3次元相対変位の大きさ
            ax = axes[1, 1]
            
            magnitude_stats_text = []
            
            for condition_idx, condition in enumerate(conditions):
                if condition in translation_results and bone_name in translation_results[condition]:
                    bone_data = translation_results[condition][bone_name]
                    
                    valid_subjects = []
                    for result in bone_data:
                        if result.get('force_gage_displacement') is not None:
                            valid_subjects.append(result)
                    
                    if valid_subjects:
                        common_displacement = np.linspace(0, 5.0, 100)
                        interpolated_magnitudes = []
                        
                        for result in valid_subjects:
                            fg_disp = result['force_gage_displacement']
                            magnitude = result.get('relative_displacement_magnitude', result.get('displacement_magnitude'))
                            
                            if magnitude is not None and len(fg_disp) == len(magnitude):
                                if len(fg_disp) > 1:
                                    try:
                                        interp_func = interp1d(fg_disp, magnitude, 
                                                             kind='linear', bounds_error=False, fill_value='extrapolate')
                                        interpolated_mag = interp_func(common_displacement)
                                        interpolated_magnitudes.append(interpolated_mag)
                                    except Exception as e:
                                        print(f"    3D変位補間エラー: {e}")
                        
                        if interpolated_magnitudes:
                            interpolated_magnitudes = np.array(interpolated_magnitudes)
                            mean_magnitudes = np.mean(interpolated_magnitudes, axis=0)
                            se_magnitudes = np.array([calculate_standard_error(interpolated_magnitudes[:, i]) 
                                                    for i in range(len(common_displacement))])
                            
                            color = colors[condition_idx % len(colors)]
                            linestyle_options = ['-', '--', '-.', ':']
                            linestyle = linestyle_options[condition_idx % len(linestyle_options)]
                            
                            ax.plot(common_displacement, mean_magnitudes,
                                   label=f'{condition}',
                                   linewidth=3, color=color, linestyle=linestyle)
                            
                            ax.fill_between(common_displacement,
                                           mean_magnitudes - se_magnitudes,
                                           mean_magnitudes + se_magnitudes,
                                           alpha=0.2, color=color)
                            
                            # 統計情報
                            max_mag = np.max(mean_magnitudes)
                            final_mag = mean_magnitudes[-1]
                            magnitude_stats_text.append(f'{condition}: 最大={max_mag:.2f}mm, 最終={final_mag:.2f}mm')
            
            ax.set_title(f'3次元相対変位の大きさ vs ForceGage変位', fontsize=14)
            ax.set_xlabel('ForceGage変位 (mm)', fontsize=12)
            ax.set_ylabel('3次元相対変位の大きさ (mm)', fontsize=12)
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # 統計情報表示
            if magnitude_stats_text:
                stats_str = '\n'.join(magnitude_stats_text)
                ax.text(0.02, 0.98, stats_str, transform=ax.transAxes,
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8))
            
            plt.tight_layout()
            plt.savefig(f'translation_vs_force_gage_displacement_{bone_name}_SE.png', dpi=300, bbox_inches='tight')
            plt.show()
            
    except Exception as e:
        print(f"Error in plot_translation_vs_force_gage_displacement: {e}")
        import traceback
        traceback.print_exc()

def plot_unified_bar_charts(analysis_results, translation_results, bone_names=['Scafoid', 'Capitate'], reference_bone='Lunate'):
    """角度・並進解析の統一棒グラフ（標準誤差対応）"""
    conditions = list(analysis_results.keys())
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for bone_name in bone_names:
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'{bone_name} vs {reference_bone} - 統一統計比較（棒グラフ）', fontsize=16)
        
        # 角度解析統計（上段）
        # angle_metrics = ['max_abs', 'rms', 'std']
        angle_metrics = ['max_abs', 'rms', 'max_total_rotation']
        angle_labels = ['最大絶対角度', 'RMS角度', '標準偏差角度']
        
        for metric_idx, (metric, label) in enumerate(zip(angle_metrics, angle_labels)):
            ax = axes[0, metric_idx]
            axis_names = ['X', 'Y', 'Z']
            
            for axis_idx, axis_name in enumerate(axis_names):
                condition_means = []
                condition_ses = []
                
                for condition in conditions:
                    if bone_name in analysis_results[condition]:
                        bone_data = analysis_results[condition][bone_name]
                        if bone_data:
                            values = [r['statistics'][metric][axis_idx] for r in bone_data]
                            condition_means.append(np.mean(values))
                            condition_ses.append(calculate_standard_error(values))
                        else:
                            condition_means.append(0)
                            condition_ses.append(0)
                
                x_pos = np.arange(len(conditions)) + axis_idx * 0.25
                ax.bar(x_pos, condition_means, yerr=condition_ses, width=0.25, 
                       label=f'{axis_name}軸', alpha=0.8, 
                       color=colors[axis_idx])
            
            ax.set_title(f'{label} (±SE)')
            ax.set_ylabel('角度 (度)')
            ax.set_ylim(0, 1.8)
            ax.set_xticks(np.arange(len(conditions)) + 0.25)
            ax.set_xticklabels(conditions, rotation=45)
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # 並進解析統計（下段）
        if bone_name != reference_bone and bone_name in translation_results.get(conditions[0], {}):
            trans_metrics = ['max_displacement', 'final_displacement', 'mean_displacement']
            trans_labels = ['最大3D相対変位', '最終3D相対変位', '平均3D相対変位']
            
            for metric_idx, (metric, label) in enumerate(zip(trans_metrics, trans_labels)):
                ax = axes[1, metric_idx]
                
                condition_means = []
                condition_ses = []
                
                for condition in conditions:
                    if bone_name in translation_results[condition]:
                        bone_data = translation_results[condition][bone_name]
                        if bone_data:
                            values = [r['statistics'][metric] for r in bone_data]
                            condition_means.append(np.mean(values))
                            condition_ses.append(calculate_standard_error(values))
                        else:
                            condition_means.append(0)
                            condition_ses.append(0)
                    else:
                        condition_means.append(0)
                        condition_ses.append(0)
                
                bars = ax.bar(conditions, condition_means, yerr=condition_ses, 
                             alpha=0.8, color=colors[:len(conditions)])
                                
                ax.set_title(f'{label} (±SE)')
                ax.set_ylabel('相対変位 (mm)')
                ax.set_ylim(0, 0.7)
                ax.set_xticklabels(conditions, rotation=45)
                ax.grid(True, alpha=0.3)
        
        else:
            # 並進データがない場合は空のプロット
            for i in range(3):
                axes[1, i].axis('off')
                axes[1, i].text(0.5, 0.5, f'{bone_name}の並進データなし', 
                               ha='center', va='center', transform=axes[1, i].transAxes)
        
        plt.tight_layout()
        plt.savefig(f'unified_bar_charts_{bone_name}.png', dpi=300, bbox_inches='tight')
        plt.show()

def run_complete_unified_visualization(analysis_results, translation_results):
    """完全統一可視化システム実行"""
    print("=== 完全統一ForceGage変位ベース可視化システム ===")
    
    bone_names = ['Scafoid', 'Capitate']
    reference_bone = 'Lunate'
    
    # 1. ForceGage変位ベース時系列グラフ
    print("\n1. ForceGage変位ベース時系列グラフ")
    plot_angles_vs_force_gage_displacement(analysis_results, bone_names, reference_bone)
    plot_translation_vs_force_gage_displacement(translation_results, bone_names, reference_bone)
    
    # 2. 統一棒グラフ
    print("\n2. 統一統計比較棒グラフ")
    plot_unified_bar_charts(analysis_results, translation_results, bone_names, reference_bone)
    
    print("\n完全統一可視化システム完了!")