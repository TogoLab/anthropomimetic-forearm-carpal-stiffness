"""
解析区間データによる可視化システム（整理版）
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import japanize_matplotlib

def calculate_standard_error(values):
    """標準誤差を計算する関数"""
    if len(values) == 0:
        return 0.0
    return np.std(values) / np.sqrt(len(values))

def reinterpolate_to_clean_measurement_distance(force_displacement, data_array, measurement_distance):
    """
    設定されたmeasurement_distanceに基づいて再補間する関数
    
    Parameters:
    -----------
    force_displacement : array-like
        実際のForceGage変位データ
    data_array : array-like
        補間対象のデータ（角度または並進変位）
    measurement_distance : float
        設定されたmeasurement_distance
        
    Returns:
    --------
    tuple : (clean_force_axis, interpolated_data)
    """
    try:
        if len(force_displacement) != len(data_array):
            return None, None
        
        if len(force_displacement) < 2:
            return None, None
        
        # 設定値ベースのForceGage変位軸を作成
        clean_force_axis = np.linspace(0.0, measurement_distance, 100)
        
        # 実データが設定値の範囲をカバーしているかチェック
        data_max = np.max(force_displacement)
        if data_max < measurement_distance * 0.8:  # 80%未満の場合は不十分
            return None, None
        
        # 補間関数を作成（設定値範囲内で）
        interp_func = interp1d(force_displacement, data_array, 
                             kind='linear', bounds_error=False, fill_value='extrapolate')
        
        # 軸に補間
        interpolated_data = interp_func(clean_force_axis)
        
        return clean_force_axis, interpolated_data
        
    except Exception:
        return None, None

def plot_angles_vs_clean_force_displacement(analysis_results, bone_names=['Scafoid', 'Capitate'], 
                                          reference_bone='Lunate', measurement_distance=3.0):
    """解析区間での角度解析グラフ（角度ノルム含む）"""
    conditions = list(analysis_results.keys())
    axis_names = ['X', 'Y', 'Z']
    axis_names_jp = ['X軸回転角度', 'Y軸回転角度', 'Z軸回転角度']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    print(f"角度解析グラフ: 解析区間 0-{measurement_distance}mm")
    
    for bone_name in bone_names:
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'{bone_name} vs {reference_bone} - ForceGage変位に対する相対角度変化 (解析区間: 0-{measurement_distance}mm)', fontsize=16)
        
        # XYZ軸別の相対角度（左上、右上、左下）
        for axis_idx in range(3):
            ax = axes[axis_idx//2, axis_idx%2] if axis_idx < 2 else axes[1, 0]
            axis_name = axis_names[axis_idx]
            axis_name_jp = axis_names_jp[axis_idx]
            
            stats_text = []
            
            for condition_idx, condition in enumerate(conditions):
                if condition in analysis_results and bone_name in analysis_results[condition]:
                    bone_data = analysis_results[condition][bone_name]
                    
                    valid_subjects = []
                    for result in bone_data:
                        if result.get('force_gage_displacement') is not None and result.get('used_enhanced_method', False):
                            valid_subjects.append(result)
                    
                    if valid_subjects:
                        print(f"  {condition} - {bone_name}: {len(valid_subjects)}名のデータを解析区間で再補間")
                        
                        clean_interpolated_angles = []
                        
                        for result in valid_subjects:
                            fg_disp = result['force_gage_displacement']
                            angles = result['relative_angles']
                            
                            if len(fg_disp) == len(angles) and len(fg_disp) > 1:
                                # 設定値ベースの軸で再補間
                                clean_force_axis, interpolated_angle = reinterpolate_to_clean_measurement_distance(
                                    fg_disp, angles[:, axis_idx], measurement_distance
                                )
                                
                                if clean_force_axis is not None and interpolated_angle is not None:
                                    clean_interpolated_angles.append(interpolated_angle)
                        
                        if clean_interpolated_angles:
                            clean_interpolated_angles = np.array(clean_interpolated_angles)
                            mean_angles = np.mean(clean_interpolated_angles, axis=0)
                            se_angles = np.array([calculate_standard_error(clean_interpolated_angles[:, i]) 
                                                for i in range(len(clean_force_axis))])
                            
                            color = colors[condition_idx % len(colors)]
                            linestyle_options = ['-', '--', '-.', ':']
                            linestyle = linestyle_options[condition_idx % len(linestyle_options)]
                            
                            # データでプロット
                            ax.plot(clean_force_axis, mean_angles,
                                   label=f'{condition} (n={len(clean_interpolated_angles)})',
                                   linewidth=3, color=color, linestyle=linestyle)
                            
                            ax.fill_between(clean_force_axis,
                                           mean_angles - se_angles,
                                           mean_angles + se_angles,
                                           alpha=0.2, color=color)
                            
                            max_angle = np.max(np.abs(mean_angles))
                            final_angle = mean_angles[-1]
                            stats_text.append(f'{condition}: 最大={max_angle:.2f}°, 最終={final_angle:.2f}°')
            
            ax.set_title(f'{axis_name_jp} vs ForceGage変位', fontsize=14)
            if axis_idx == 2:
                ax.set_xlabel(f'ForceGage変位 (mm)', fontsize=12)
            ax.set_ylabel(f'{axis_name}軸相対角度 (°)', fontsize=12)
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
            ax.set_ylim(-2, 2)
            
            # 軸範囲を設定
            ax.set_xlim(0.0, measurement_distance)
            
            if stats_text:
                stats_str = '\n'.join(stats_text)
                ax.text(0.02, 0.98, stats_str, transform=ax.transAxes,
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.8))
        
        # **角度ノルム（総回転量）プロット（右下）- エラーハンドリング付き**
        ax = axes[1, 1]
        
        norm_stats_text = []
        
        try:
            for condition_idx, condition in enumerate(conditions):
                if condition in analysis_results and bone_name in analysis_results[condition]:
                    bone_data = analysis_results[condition][bone_name]
                    
                    valid_subjects = []
                    for result in bone_data:
                        if result.get('force_gage_displacement') is not None and result.get('used_enhanced_method', False):
                            valid_subjects.append(result)
                    
                    if valid_subjects:
                        clean_interpolated_norms = []
                        
                        for result in valid_subjects:
                            fg_disp = result['force_gage_displacement']
                            angles = result['relative_angles']
                            
                            if len(fg_disp) == len(angles) and len(fg_disp) > 1:
                                try:
                                    # 角度ノルム（総回転量）を計算
                                    angle_norms = np.linalg.norm(angles, axis=1)
                                    
                                    # 設定値ベースの軸で再補間
                                    clean_force_axis, interpolated_norm = reinterpolate_to_clean_measurement_distance(
                                        fg_disp, angle_norms, measurement_distance
                                    )
                                    
                                    if clean_force_axis is not None and interpolated_norm is not None:
                                        clean_interpolated_norms.append(interpolated_norm)
                                except Exception as e:
                                    print(f"    角度ノルム計算エラー: {e}")
                                    continue
                        
                        if clean_interpolated_norms:
                            clean_interpolated_norms = np.array(clean_interpolated_norms)
                            mean_norms = np.mean(clean_interpolated_norms, axis=0)
                            se_norms = np.array([calculate_standard_error(clean_interpolated_norms[:, i]) 
                                               for i in range(len(clean_force_axis))])
                            
                            color = colors[condition_idx % len(colors)]
                            linestyle_options = ['-', '--', '-.', ':']
                            linestyle = linestyle_options[condition_idx % len(linestyle_options)]
                            
                            ax.plot(clean_force_axis, mean_norms,
                                   label=f'{condition} (n={len(clean_interpolated_norms)})',
                                   linewidth=3, color=color, linestyle=linestyle)
                            
                            ax.fill_between(clean_force_axis,
                                           mean_norms - se_norms,
                                           mean_norms + se_norms,
                                           alpha=0.2, color=color)
                            
                            max_norm = np.max(mean_norms)
                            final_norm = mean_norms[-1]
                            norm_stats_text.append(f'{condition}: 最大={max_norm:.2f}°, 最終={final_norm:.2f}°')
            
            ax.set_title(f'総回転量（角度ノルム）vs ForceGage変位', fontsize=14)
            ax.set_xlabel(f'ForceGage変位 (mm)', fontsize=12)
            ax.set_ylabel('総回転量 (°)', fontsize=12)
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # 軸範囲を設定
            ax.set_xlim(0.0, measurement_distance)
            
            if norm_stats_text:
                stats_str = '\n'.join(norm_stats_text)
                ax.text(0.02, 0.98, stats_str, transform=ax.transAxes,
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcyan', alpha=0.8))
            
        except Exception as e:
            print(f"    角度ノルムプロット生成エラー: {e}")
            ax.text(0.5, 0.5, '角度ノルムデータ\n生成中にエラー', 
                   ha='center', va='center', transform=ax.transAxes,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.8))
        
        plt.tight_layout()
        filename = f'pngs/clean_angles_vs_force_{bone_name}_{measurement_distance}mm.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()
        
def plot_translation_vs_clean_force_displacement(translation_results, bone_names=['Capitate', 'Scafoid'], 
                                               reference_bone='Lunate', measurement_distance=3.0):
    """解析区間での並進解析グラフ"""
    conditions = list(translation_results.keys())
    axis_names = ['X', 'Y', 'Z']
    axis_names_jp = ['X軸相対変位', 'Y軸相対変位', 'Z軸相対変位']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    print(f"並進解析グラフ: 解析区間 0-{measurement_distance}mm")
    
    for bone_name in bone_names:
        if bone_name == reference_bone:
            continue
            
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{bone_name} vs {reference_bone} - ForceGage変位に対する相対並進変位 (解析区間: 0-{measurement_distance}mm)', fontsize=16)
        
        # XYZ軸別の相対変位
        for axis_idx in range(3):
            ax = axes[axis_idx//2, axis_idx%2] if axis_idx < 2 else axes[1, 0]
            axis_name = axis_names[axis_idx]
            axis_name_jp = axis_names_jp[axis_idx]
            
            stats_text = []
            
            for condition_idx, condition in enumerate(conditions):
                if condition in translation_results and bone_name in translation_results[condition]:
                    bone_data = translation_results[condition][bone_name]
                    
                    valid_subjects = []
                    for result in bone_data:
                        if result.get('force_gage_displacement') is not None:
                            valid_subjects.append(result)
                    
                    if valid_subjects:
                        print(f"  {condition} - {bone_name}: {len(valid_subjects)}名のデータを解析区間で再補間")
                        
                        clean_interpolated_displacements = []
                        
                        for result in valid_subjects:
                            fg_disp = result['force_gage_displacement']
                            relative_disp = result.get('relative_displacement', result.get('displacement'))
                            
                            if relative_disp is not None and len(fg_disp) == len(relative_disp) and len(fg_disp) > 1:
                                # 設定値ベースの軸で再補間
                                clean_force_axis, interpolated_disp = reinterpolate_to_clean_measurement_distance(
                                    fg_disp, relative_disp[:, axis_idx], measurement_distance
                                )
                                
                                if clean_force_axis is not None and interpolated_disp is not None:
                                    clean_interpolated_displacements.append(interpolated_disp)
                        
                        if clean_interpolated_displacements:
                            clean_interpolated_displacements = np.array(clean_interpolated_displacements)
                            mean_displacements = np.mean(clean_interpolated_displacements, axis=0)
                            se_displacements = np.array([calculate_standard_error(clean_interpolated_displacements[:, i]) 
                                                       for i in range(len(clean_force_axis))])
                            
                            color = colors[condition_idx % len(colors)]
                            linestyle_options = ['-', '--', '-.', ':']
                            linestyle = linestyle_options[condition_idx % len(linestyle_options)]
                            
                            # データでプロット
                            ax.plot(clean_force_axis, mean_displacements,
                                   label=f'{condition}',
                                   linewidth=3, color=color, linestyle=linestyle)
                            
                            ax.fill_between(clean_force_axis,
                                           mean_displacements - se_displacements,
                                           mean_displacements + se_displacements,
                                           alpha=0.2, color=color)
                            
                            max_disp = np.max(np.abs(mean_displacements))
                            final_disp = mean_displacements[-1]
                            stats_text.append(f'{condition}: 最大={max_disp:.2f}mm, 最終={final_disp:.2f}mm')
            
            ax.set_title(f'{axis_name_jp} vs ForceGage変位', fontsize=14)
            ax.set_xlabel(f'ForceGage変位 (mm)', fontsize=12)
            ax.set_ylabel(f'{axis_name}軸相対変位 (mm)', fontsize=12)
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
            
            # 軸範囲を設定
            ax.set_xlim(0.0, measurement_distance)
            
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
                    clean_interpolated_magnitudes = []
                    
                    for result in valid_subjects:
                        fg_disp = result['force_gage_displacement']
                        magnitude = result.get('relative_displacement_magnitude', result.get('displacement_magnitude'))
                        
                        if magnitude is not None and len(fg_disp) == len(magnitude) and len(fg_disp) > 1:
                            # 設定値ベースの軸で再補間
                            clean_force_axis, interpolated_mag = reinterpolate_to_clean_measurement_distance(
                                fg_disp, magnitude, measurement_distance
                            )
                            
                            if clean_force_axis is not None and interpolated_mag is not None:
                                clean_interpolated_magnitudes.append(interpolated_mag)
                    
                    if clean_interpolated_magnitudes:
                        clean_interpolated_magnitudes = np.array(clean_interpolated_magnitudes)
                        mean_magnitudes = np.mean(clean_interpolated_magnitudes, axis=0)
                        se_magnitudes = np.array([calculate_standard_error(clean_interpolated_magnitudes[:, i]) 
                                                for i in range(len(clean_force_axis))])
                        
                        color = colors[condition_idx % len(colors)]
                        linestyle_options = ['-', '--', '-.', ':']
                        linestyle = linestyle_options[condition_idx % len(linestyle_options)]
                        
                        ax.plot(clean_force_axis, mean_magnitudes,
                               label=f'{condition}',
                               linewidth=3, color=color, linestyle=linestyle)
                        
                        ax.fill_between(clean_force_axis,
                                       mean_magnitudes - se_magnitudes,
                                       mean_magnitudes + se_magnitudes,
                                       alpha=0.2, color=color)
                        
                        max_mag = np.max(mean_magnitudes)
                        final_mag = mean_magnitudes[-1]
                        magnitude_stats_text.append(f'{condition}: 最大={max_mag:.2f}mm, 最終={final_mag:.2f}mm')
        
        ax.set_title(f'3次元相対変位の大きさ vs ForceGage変位', fontsize=14)
        ax.set_xlabel(f'ForceGage変位 (mm)', fontsize=12)
        ax.set_ylabel('3次元相対変位の大きさ (mm)', fontsize=12)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 軸範囲を設定
        ax.set_xlim(0.0, measurement_distance)
        
        if magnitude_stats_text:
            stats_str = '\n'.join(magnitude_stats_text)
            ax.text(0.02, 0.98, stats_str, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8))
        
        plt.tight_layout()
        filename = f'pngs/clean_translation_vs_force_{bone_name}_{measurement_distance}mm.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()

def plot_clean_comparison_bar_charts(analysis_results, translation_results, bone_names=['Scafoid', 'Capitate'], 
                                   reference_bone='Lunate', measurement_distance=3.0):
    """解析区間での統計比較棒グラフ"""
    conditions = list(analysis_results.keys())
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for bone_name in bone_names:
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'{bone_name} vs {reference_bone} - 統計比較 (解析区間: 0-{measurement_distance}mm)', fontsize=16)
        
        # 角度解析統計（上段）
        # 角度解析統計（上段）- 安全なキーアクセス
        base_angle_metrics = ['max_abs', 'rms', 'std']
        base_angle_labels = ['最大絶対角度', 'RMS角度', '標準偏差角度']

        # max_total_rotationが利用可能かチェック
        has_total_rotation = False
        if bone_name in analysis_results.get(conditions[0], {}):
            sample_data = analysis_results[conditions[0]][bone_name]
            if sample_data and len(sample_data) > 0:
                has_total_rotation = 'max_total_rotation' in sample_data[0].get('statistics', {})

        if has_total_rotation:
            angle_metrics = ['max_abs', 'rms', 'max_total_rotation']
            angle_labels = ['最大絶対角度', 'RMS角度', '最大総回転量']
            print(f"  {bone_name}: 総回転量統計が利用可能")
        else:
            angle_metrics = base_angle_metrics
            angle_labels = base_angle_labels
            print(f"  {bone_name}: 従来統計のみ使用")

        for metric_idx, (metric, label) in enumerate(zip(angle_metrics, angle_labels)):
            ax = axes[0, metric_idx]
            ax.set_axisbelow(True)
            ax.grid(True, alpha=0.3)

            
            if metric == 'max_total_rotation' and has_total_rotation:
                # 総回転量の場合は1つの値のみ
                condition_means = []
                condition_ses = []
                
                for condition in conditions:
                    if bone_name in analysis_results[condition]:
                        bone_data = analysis_results[condition][bone_name]
                        if bone_data:
                            values = []
                            for r in bone_data:
                                if 'statistics' in r and metric in r['statistics']:
                                    values.append(r['statistics'][metric])
                            
                            if values:
                                condition_means.append(np.mean(values))
                                condition_ses.append(calculate_standard_error(values))
                            else:
                                condition_means.append(0)
                                condition_ses.append(0)
                        else:
                            condition_means.append(0)
                            condition_ses.append(0)
                    else:
                        condition_means.append(0)
                        condition_ses.append(0)
                
                bars = ax.bar(conditions, condition_means, yerr=condition_ses, 
                            alpha=0.8, color=colors[:len(conditions)])
                ax.set_ylabel('総回転量 (度)')
                
            else:
                # XYZ軸別の統計（従来版）
                axis_names = ['X', 'Y', 'Z']
                
                for axis_idx, axis_name in enumerate(axis_names):
                    condition_means = []
                    condition_ses = []
                    
                    for condition in conditions:
                        if bone_name in analysis_results[condition]:
                            bone_data = analysis_results[condition][bone_name]
                            if bone_data:
                                values = []
                                for r in bone_data:
                                    if ('statistics' in r and metric in r['statistics'] and 
                                        isinstance(r['statistics'][metric], (list, np.ndarray)) and 
                                        len(r['statistics'][metric]) > axis_idx):
                                        values.append(r['statistics'][metric][axis_idx])
                                
                                if values:
                                    condition_means.append(np.mean(values))
                                    condition_ses.append(calculate_standard_error(values))
                                else:
                                    condition_means.append(0)
                                    condition_ses.append(0)
                            else:
                                condition_means.append(0)
                                condition_ses.append(0)
                        else:
                            condition_means.append(0)
                            condition_ses.append(0)
                    
                    x_pos = np.arange(len(conditions)) + axis_idx * 0.25
                    ax.bar(x_pos, condition_means, yerr=condition_ses, width=0.25, 
                        label=f'{axis_name}軸', alpha=0.8, 
                        color=colors[axis_idx])
                
                ax.set_xticks(np.arange(len(conditions)) + 0.25)
                ax.set_ylabel('角度 (度)')
                ax.legend()
            
            ax.set_title(f'{label} (±SE)')
            ax.set_ylim(0, 2.0)
            ax.set_xticklabels(conditions, rotation=45)
        # 並進解析統計（下段）
        if bone_name != reference_bone and bone_name in translation_results.get(conditions[0], {}):
            trans_metrics = ['max_displacement', 'final_displacement', 'mean_displacement']
            trans_labels = ['最大3D相対変位', '最終3D相対変位', '平均3D相対変位']
            
            for metric_idx, (metric, label) in enumerate(zip(trans_metrics, trans_labels)):
                ax = axes[1, metric_idx]
                ax.set_axisbelow(True)
                ax.grid(True, alpha=0.3)
                
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

        else:
            # 並進データがない場合
            for i in range(3):
                axes[1, i].axis('off')
                axes[1, i].text(0.5, 0.5, f'{bone_name}の並進データなし', 
                               ha='center', va='center', transform=axes[1, i].transAxes)
        
        plt.tight_layout()
        filename = f'pngs/clean_bar_charts_{bone_name}_{measurement_distance}mm.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()

def plot_xyz_axis_comparison_bar_charts(analysis_results, translation_results, bone_names=['Scafoid', 'Capitate'], 
                                       reference_bone='Lunate', measurement_distance=3.0):
    """XYZ軸別の最大相対角度・最大相対変位比較棒グラフ（各軸での条件比較）"""
    conditions = list(analysis_results.keys())
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'各軸での条件比較: 最大相対角度・最大相対変位 (解析区間: 0-{measurement_distance}mm)', fontsize=16)
    
    # 上段：角度解析 - 各軸での条件比較
    axis_names = ['X軸', 'Y軸', 'Z軸']
    
    for axis_idx, axis_name in enumerate(axis_names):
        ax = axes[0, axis_idx]
        ax.set_title(f'{axis_name} 最大絶対相対角度の条件比較', fontsize=14)
        ax.set_axisbelow(True)
        ax.grid(True, alpha=0.3)

        x_pos = np.arange(len(bone_names))
        width = 0.8 / len(conditions)
        
        for cond_idx, condition in enumerate(conditions):
            means = []
            ses = []
            
            for bone_name in bone_names:
                if bone_name in analysis_results[condition]:
                    bone_data = analysis_results[condition][bone_name]
                    if bone_data:
                        values = [r['statistics']['max_abs'][axis_idx] for r in bone_data]
                        means.append(np.mean(values))
                        ses.append(calculate_standard_error(values))
                    else:
                        means.append(0)
                        ses.append(0)
                else:
                    means.append(0)
                    ses.append(0)
            
            offset = (cond_idx - (len(conditions) - 1) / 2) * width
            bars = ax.bar(x_pos + offset, means, yerr=ses, width=width, 
                         label=condition, alpha=0.8, 
                         color=colors[cond_idx % len(colors)])
            
        
        ax.set_ylabel('最大絶対角度 (度)')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(bone_names)
        ax.set_ylim(0, 1.8)
        ax.legend(title='条件', fontsize=9)

    # 下段：並進解析 - 各軸での条件比較
    plot_bone_names = [name for name in bone_names if name != reference_bone]
    
    if plot_bone_names:
        for axis_idx, axis_name in enumerate(axis_names):
            ax = axes[1, axis_idx]
            ax.set_title(f'{axis_name} 最大絶対相対変位の条件比較', fontsize=14)
            ax.set_axisbelow(True)
            ax.grid(True, alpha=0.3)

            x_pos = np.arange(len(plot_bone_names))
            width = 0.8 / len(conditions)
            
            for cond_idx, condition in enumerate(conditions):
                means = []
                ses = []
                
                for bone_name in plot_bone_names:
                    if bone_name in translation_results[condition]:
                        bone_data = translation_results[condition][bone_name]
                        if bone_data:
                            metric_name = f'max_abs_{["x", "y", "z"][axis_idx]}'
                            values = [r['statistics'][metric_name] for r in bone_data]
                            means.append(np.mean(values))
                            ses.append(calculate_standard_error(values))
                        else:
                            means.append(0)
                            ses.append(0)
                    else:
                        means.append(0)
                        ses.append(0)
                
                offset = (cond_idx - (len(conditions) - 1) / 2) * width
                bars = ax.bar(x_pos + offset, means, yerr=ses, width=width, 
                             label=condition, alpha=0.8, 
                             color=colors[cond_idx % len(colors)])
                
            ax.set_ylabel('最大絶対相対変位 (mm)')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(plot_bone_names)
            ax.set_ylim(0, 0.8)
            ax.legend(title='条件', fontsize=9)
    else:
        # 並進データがない場合
        for axis_idx in range(3):
            axes[1, axis_idx].axis('off')
            axes[1, axis_idx].text(0.5, 0.5, '並進データなし', 
                                  ha='center', va='center', transform=axes[1, axis_idx].transAxes)
    
    plt.tight_layout()
    filename = f'pngs/xyz_axis_condition_comparison_{measurement_distance}mm.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()

def run_clean_unified_visualization(analysis_results, translation_results, measurement_distance=3.0):
    """解析区間での統一可視化実行"""
    print("=== 解析区間データによる統一可視化システム ===")
    print(f"解析区間: 0-{measurement_distance}mm (設定値基準)")
    print("特徴: 警告なし、データ、正確な比較")
    print("="*50)
    
    bone_names = ['Scafoid', 'Capitate']
    reference_bone = 'Lunate'
    
    # 1. 角度解析グラフ
    print("\n1. 角度解析（解析区間）")
    plot_angles_vs_clean_force_displacement(analysis_results, bone_names, reference_bone, measurement_distance)
    
    # 2. 並進解析グラフ
    print("\n2. 並進解析（解析区間）")
    plot_translation_vs_clean_force_displacement(translation_results, bone_names, reference_bone, measurement_distance)
    
    # 3. 統計比較棒グラフ
    print("\n3. 統計比較棒グラフ（解析区間）")
    plot_clean_comparison_bar_charts(analysis_results, translation_results, bone_names, reference_bone, measurement_distance)
    
    # 4. XYZ軸別比較棒グラフ
    print("\n4. XYZ軸別最大値比較棒グラフ（解析区間）")
    plot_xyz_axis_comparison_bar_charts(analysis_results, translation_results, bone_names, reference_bone, measurement_distance)
    
    print("\n解析区間データによる統一可視化完了!")

if __name__ == "__main__":
    print("=== 解析区間データによる可視化システム ===")
    print("使用方法:")
    print("run_clean_unified_visualization(analysis_results, translation_results, measurement_distance=3.0)")