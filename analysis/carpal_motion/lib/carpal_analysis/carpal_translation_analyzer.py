"""
手根骨モーションキャプチャー - 並進運動量解析モジュール（Lunate相対座標系対応）
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from lib.carpal_analysis.carpal_data_loader import extract_bone_data

def calculate_standard_error(values):
    """標準誤差を計算する関数"""
    if len(values) == 0:
        return 0.0
    return np.std(values) / np.sqrt(len(values))

def calculate_relative_translation_motion(df, bone_structure, bone_name, reference_bone='Lunate', handle_missing='interpolate'):
    """
    Lunateに対する相対座標系におけるマーカーの並進運動量を計算
    
    Parameters:
    -----------
    df : pandas.DataFrame
        モーションキャプチャーデータ
    bone_structure : dict
        骨の構造情報
    bone_name : str
        対象骨の名前
    reference_bone : str
        基準骨の名前（デフォルト: 'Lunate'）
    handle_missing : str
        欠損値の処理方法
        
    Returns:
    --------
    dict : 相対並進運動データ
    """
    try:
        # 対象骨のデータを取得
        time, position, _ = extract_bone_data(df, bone_structure, bone_name, handle_missing)
        
        # 基準骨（Lunate）のデータを取得
        ref_time, ref_position, _ = extract_bone_data(df, bone_structure, reference_bone, handle_missing)
        
        # データ長を統一
        min_len = min(len(time), len(ref_time))
        time = time[:min_len]
        position = position[:min_len]
        ref_time = ref_time[:min_len]
        ref_position = ref_position[:min_len]
        
        # Lunateに対する相対位置を計算
        relative_position = position - ref_position
        
        # 初期相対位置を基準とした相対変位を計算
        initial_relative_position = relative_position[0]
        relative_displacement = relative_position - initial_relative_position
        
        # 3次元相対変位の大きさ
        relative_displacement_magnitude = np.sqrt(np.sum(relative_displacement**2, axis=1))
        
        # 統計情報（Lunate相対座標系版）
        stats = {
            # 3次元相対変位の大きさに関する統計
            'max_displacement': np.max(relative_displacement_magnitude),
            'final_displacement': relative_displacement_magnitude[-1],
            'mean_displacement': np.mean(relative_displacement_magnitude),
            'std_displacement': np.std(relative_displacement_magnitude),
            
            # 各軸での相対変位統計（符号付き）
            'max_x_positive': np.max(relative_displacement[:, 0]),
            'max_x_negative': np.min(relative_displacement[:, 0]),
            'max_y_positive': np.max(relative_displacement[:, 1]),
            'max_y_negative': np.min(relative_displacement[:, 1]),
            'max_z_positive': np.max(relative_displacement[:, 2]),
            'max_z_negative': np.min(relative_displacement[:, 2]),
            
            # 各軸での相対変位幅（レンジ）
            'range_x': np.max(relative_displacement[:, 0]) - np.min(relative_displacement[:, 0]),
            'range_y': np.max(relative_displacement[:, 1]) - np.min(relative_displacement[:, 1]),
            'range_z': np.max(relative_displacement[:, 2]) - np.min(relative_displacement[:, 2]),
            
            # 各軸での最大絶対相対変位
            'max_abs_x': np.max(np.abs(relative_displacement[:, 0])),
            'max_abs_y': np.max(np.abs(relative_displacement[:, 1])),
            'max_abs_z': np.max(np.abs(relative_displacement[:, 2])),
            
            # 最終時点での各軸相対変位
            'final_x': relative_displacement[-1, 0],
            'final_y': relative_displacement[-1, 1],
            'final_z': relative_displacement[-1, 2],
            
            # データ品質指標
            'position_unit': 'mm' if np.max(np.abs(position)) >= 1.0 else 'm',
            'initial_relative_position': initial_relative_position.copy(),
            'coordinate_frame': f'relative_to_{reference_bone}',
            'reference_bone': reference_bone
        }
        
        print(f"  {bone_name} vs {reference_bone}: 最大3次元相対変位={stats['max_displacement']:.2f}mm, 最終相対変位={stats['final_displacement']:.2f}mm")
        
        return {
            'time': time,
            'absolute_position': position,
            'reference_position': ref_position,
            'relative_position': relative_position,
            'relative_displacement': relative_displacement,
            'displacement': relative_displacement,  # 後方互換性のため
            'relative_displacement_magnitude': relative_displacement_magnitude,
            'displacement_magnitude': relative_displacement_magnitude,  # 後方互換性のため
            'bone_name': bone_name,
            'reference_bone': reference_bone,
            'statistics': stats,
            'data_length': len(time)
        }
        
    except Exception as e:
        raise ValueError(f"Error calculating relative translation motion for {bone_name} vs {reference_bone}: {str(e)}")

def calculate_translation_motion(df, bone_structure, bone_name, handle_missing='interpolate'):
    """Lunateに対する相対座標系における並進運動量を計算（後方互換性のため）"""
    return calculate_relative_translation_motion(df, bone_structure, bone_name, 'Lunate', handle_missing)

def create_translation_summary_table_with_se(translation_results, bone_names=['Capitate', 'Scafoid'], reference_bone='Lunate'):
    """Lunateに対する相対並進運動量の統計テーブル表示（標準誤差対応版）"""
    conditions = list(translation_results.keys())
    plot_bone_names = [name for name in bone_names if name != reference_bone]
    
    print(f"\n{reference_bone}に対する相対並進運動量統計サマリー (mm) - 標準誤差表示")
    print("算出方法:")
    print(f"- 最大相対変位: {reference_bone}に対する初期相対位置からの3次元相対変位の最大値 √(x²+y²+z²)")
    print(f"- 最終相対変位: 最後のフレームでの{reference_bone}に対する3次元相対変位の大きさ")
    print(f"- 各軸相対変位幅: 各軸での{reference_bone}に対する相対変位の最大値-最小値")
    print(f"- 絶対値最大: 各軸での{reference_bone}に対する相対変位絶対値の最大値")
    
    for bone_name in plot_bone_names:
        print(f"\n{bone_name} vs {reference_bone}:")
        print("-"*50)
        
        # フィルタリング情報の表示
        if bone_name in translation_results.get(conditions[0], {}):
            bone_data = translation_results[conditions[0]][bone_name]
            if bone_data and len(bone_data) > 0:
                sample_stats = bone_data[0]['statistics']
                if 'filtering_applied' in sample_stats:
                    filter_info = f"高度フィルタリング: {'適用' if sample_stats['filtering_applied'] else '未適用'}"
                    if sample_stats['filtering_applied']:
                        filter_info += f" ({sample_stats.get('filter_type', 'unknown')})"
                    print(f"  {filter_info}")
                
                print(f"  座標系: {sample_stats.get('coordinate_frame', 'unknown')}")
        
        # 3次元相対変位統計（標準誤差使用）
        metrics = ['max_displacement', 'final_displacement', 'mean_displacement']
        metric_names = ['最大3D相対変位', '最終3D相対変位', '平均3D相対変位']
        
        for metric, name in zip(metrics, metric_names):
            row = f"  {name}: "
            
            for condition in conditions:
                if bone_name in translation_results[condition]:
                    bone_data = translation_results[condition][bone_name]
                    if bone_data:
                        values = [result['statistics'][metric] for result in bone_data]
                        mean_val = np.mean(values)
                        se_val = calculate_standard_error(values)
                        row += f"{mean_val:.2f}±{se_val:.2f}  "
                    else:
                        row += "N/A  "
                else:
                    row += "N/A  "
            
            print(row)
        
        # 各軸の相対変位幅（標準誤差使用）
        print("  各軸相対変位幅:")
        axis_metrics = ['range_x', 'range_y', 'range_z']
        axis_names = ['X軸幅', 'Y軸幅', 'Z軸幅']
        
        for metric, name in zip(axis_metrics, axis_names):
            row = f"    {name}: "
            
            for condition in conditions:
                if bone_name in translation_results[condition]:
                    bone_data = translation_results[condition][bone_name]
                    if bone_data:
                        values = [result['statistics'][metric] for result in bone_data]
                        mean_val = np.mean(values)
                        se_val = calculate_standard_error(values)
                        row += f"{mean_val:.2f}±{se_val:.2f}  "
                    else:
                        row += "N/A  "
                else:
                    row += "N/A  "
            
            print(row)
        
        # 絶対値最大相対変位（標準誤差使用）
        print("  絶対値最大相対変位:")
        abs_metrics = ['max_abs_x', 'max_abs_y', 'max_abs_z']
        abs_names = ['X軸絶対最大', 'Y軸絶対最大', 'Z軸絶対最大']
        
        for metric, name in zip(abs_metrics, abs_names):
            row = f"    {name}: "
            
            for condition in conditions:
                if bone_name in translation_results[condition]:
                    bone_data = translation_results[condition][bone_name]
                    if bone_data:
                        values = [result['statistics'][metric] for result in bone_data]
                        mean_val = np.mean(values)
                        se_val = calculate_standard_error(values)
                        row += f"{mean_val:.2f}±{se_val:.2f}  "
                    else:
                        row += "N/A  "
                else:
                    row += "N/A  "
            
            print(row)

def plot_detailed_relative_translation_timeseries_force_based(translation_results, bone_names=['Capitate', 'Scafoid'], reference_bone='Lunate'):
    """ForceGage変位ベースの相対並進運動詳細時系列解析グラフ（標準誤差対応）"""
    try:
        conditions = list(translation_results.keys())
        axis_names = ['X', 'Y', 'Z']
        axis_names_jp = ['X軸相対変位', 'Y軸相対変位', 'Z軸相対変位']
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        print(f"ForceGage変位ベース並進時系列解析: {len(conditions)}条件, {len(bone_names)}骨")
        
        for bone_name in bone_names:
            if bone_name == reference_bone:
                continue
                
            fig, axes = plt.subplots(4, 1, figsize=(12, 16))
            fig.suptitle(f'{bone_name} vs {reference_bone} - ForceGage変位に対する相対並進運動の詳細時系列解析 ({len(conditions)}条件比較)', fontsize=16)
            
            # 共通のForceGage変位軸を作成（0〜5mmの範囲で100点）
            common_force_displacement = np.linspace(0, 5.0, 100)
            
            # XYZ軸別の相対変位（上部3つのサブプロット）
            for axis_idx, (axis_name, axis_name_jp) in enumerate(zip(axis_names, axis_names_jp)):
                ax = axes[axis_idx]
                
                stats_text = []
                
                for condition_idx, condition in enumerate(conditions):
                    if bone_name in translation_results[condition]:
                        bone_data = translation_results[condition][bone_name]
                        
                        # ForceGage変位データがある被験者のみ処理
                        valid_subjects = []
                        for result in bone_data:
                            if result.get('force_gage_displacement') is not None:
                                valid_subjects.append(result)
                        
                        if valid_subjects:
                            print(f"  {condition} - {bone_name}: {len(valid_subjects)}名のForceGage変位データ使用")
                            
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
                                            interpolated_disp = interp_func(common_force_displacement)
                                            interpolated_displacements.append(interpolated_disp)
                                        except Exception as e:
                                            print(f"    補間エラー: {e}")
                            
                            if interpolated_displacements:
                                interpolated_displacements = np.array(interpolated_displacements)
                                mean_displacement = np.mean(interpolated_displacements, axis=0)
                                se_displacement = np.array([calculate_standard_error(interpolated_displacements[:, i]) 
                                                          for i in range(len(common_force_displacement))])
                                
                                color = colors[condition_idx % len(colors)]
                                linestyle = ['-', '--', '-.', ':'][condition_idx % 4]
                                
                                # 平均線をプロット
                                ax.plot(common_force_displacement, mean_displacement, 
                                       label=f'{condition}', 
                                       linewidth=3, color=color, linestyle=linestyle)
                                
                                # 標準誤差の帯
                                ax.fill_between(common_force_displacement, 
                                               mean_displacement - se_displacement,
                                               mean_displacement + se_displacement,
                                               alpha=0.2, color=color)
                                
                                # 統計情報を計算
                                max_disp = np.max(np.abs(mean_displacement))
                                final_disp = mean_displacement[-1]
                                range_disp = np.max(mean_displacement) - np.min(mean_displacement)
                                
                                stats_text.append(f'{condition}: Max={max_disp:.2f}mm, Final={final_disp:.2f}mm, Range={range_disp:.2f}mm')
                
                # グラフ設定
                ax.set_title(f'{axis_name_jp} vs ForceGage変位', fontsize=14)
                if axis_idx == 2:
                    ax.set_xlabel('ForceGage変位 (mm)', fontsize=12)
                ax.set_ylabel(f'{axis_name}軸相対変位 (mm)', fontsize=12)
                ax.legend(loc='best', fontsize=9)
                ax.grid(True, alpha=0.3)
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
                
                ax.set_ylim(-0.5, 0.5)
                
                # 統計情報をテキストボックスで表示
                if stats_text:
                    stats_str = '\n'.join(stats_text)
                    ax.text(0.02, 0.98, stats_str, transform=ax.transAxes,
                           fontsize=9, verticalalignment='top',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.8))
            
            # 3次元相対変位の大きさ（最下段）
            ax = axes[3]
            
            magnitude_stats_text = []
            
            for condition_idx, condition in enumerate(conditions):
                if bone_name in translation_results[condition]:
                    bone_data = translation_results[condition][bone_name]
                    
                    valid_subjects = []
                    for result in bone_data:
                        if result.get('force_gage_displacement') is not None:
                            valid_subjects.append(result)
                    
                    if valid_subjects:
                        interpolated_magnitudes = []
                        
                        for result in valid_subjects:
                            fg_disp = result['force_gage_displacement']
                            magnitude = result.get('relative_displacement_magnitude', result.get('displacement_magnitude'))
                            
                            if magnitude is not None and len(fg_disp) == len(magnitude):
                                if len(fg_disp) > 1:
                                    try:
                                        interp_func = interp1d(fg_disp, magnitude, 
                                                             kind='linear', bounds_error=False, fill_value='extrapolate')
                                        interpolated_mag = interp_func(common_force_displacement)
                                        interpolated_magnitudes.append(interpolated_mag)
                                    except Exception as e:
                                        print(f"    3D変位補間エラー: {e}")
                        
                        if interpolated_magnitudes:
                            interpolated_magnitudes = np.array(interpolated_magnitudes)
                            mean_magnitude = np.mean(interpolated_magnitudes, axis=0)
                            se_magnitude = np.array([calculate_standard_error(interpolated_magnitudes[:, i]) 
                                                   for i in range(len(common_force_displacement))])
                            
                            color = colors[condition_idx % len(colors)]
                            linestyle = ['-', '--', '-.', ':'][condition_idx % 4]
                            
                            ax.plot(common_force_displacement, mean_magnitude, 
                                   label=f'{condition}', 
                                   linewidth=3, color=color, linestyle=linestyle)
                            
                            ax.fill_between(common_force_displacement, 
                                           mean_magnitude - se_magnitude,
                                           mean_magnitude + se_magnitude,
                                           alpha=0.2, color=color)
                            
                            # 統計情報
                            max_mag = np.max(mean_magnitude)
                            final_mag = mean_magnitude[-1]
                            magnitude_stats_text.append(f'{condition}: Max={max_mag:.2f}mm, Final={final_mag:.2f}mm')
            
            ax.set_title(f'3次元相対変位の大きさ vs ForceGage変位', fontsize=14)
            ax.set_xlabel('ForceGage変位 (mm)', fontsize=12)
            ax.set_ylabel('3次元相対変位の大きさ (mm)', fontsize=12)
            ax.legend(loc='best', fontsize=9)
            ax.grid(True, alpha=0.3)
            
            # 統計情報をテキストボックスで表示
            if magnitude_stats_text:
                stats_str = '\n'.join(magnitude_stats_text)
                ax.text(0.02, 0.98, stats_str, transform=ax.transAxes,
                       fontsize=9, verticalalignment='top',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8))
            
            plt.tight_layout()
            plt.savefig(f'detailed_translation_vs_force_gage_{bone_name}_{len(conditions)}conditions.png', dpi=300, bbox_inches='tight')
            plt.show()
            
    except Exception as e:
        print(f"Error in plot_detailed_relative_translation_timeseries_force_based: {e}")
        import traceback
        traceback.print_exc()

def plot_translation_statistics(translation_results, bone_names=['Capitate', 'Scafoid'], reference_bone='Lunate'):
    """Lunateに対する相対並進運動の統計比較棒グラフ（3条件対応版）"""
    conditions = list(translation_results.keys())
    plot_bone_names = [name for name in bone_names if name != reference_bone]
    
    metrics = ['max_displacement', 'final_displacement', 'mean_displacement']
    metric_labels = ['最大相対変位', '最終相対変位', '平均相対変位']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{reference_bone}に対する相対並進運動量統計比較 ({len(conditions)}条件)', fontsize=16)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    # メトリック別の比較
    for metric_idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
        if metric_idx >= 3:
            break
            
        ax = axes[metric_idx//2, metric_idx%2]
        
        x_pos = np.arange(len(plot_bone_names))
        width = 0.8 / len(conditions)
        
        for cond_idx, condition in enumerate(conditions):
            values = []
            errors = []
            
            for bone_name in plot_bone_names:
                if bone_name in translation_results[condition]:
                    bone_data = translation_results[condition][bone_name]
                    if bone_data:
                        metric_values = [result['statistics'][metric] for result in bone_data]
                        values.append(np.mean(metric_values))
                        errors.append(np.std(metric_values))
                    else:
                        values.append(0)
                        errors.append(0)
                else:
                    values.append(0)
                    errors.append(0)
            
            offset = (cond_idx - (len(conditions) - 1) / 2) * width
            ax.bar(x_pos + offset, values, width, 
                   yerr=errors, label=condition, alpha=0.8, 
                   color=colors[cond_idx % len(colors)])
        
        ax.set_title(f'{label}（vs {reference_bone}）')
        ax.set_ylabel('相対変位 (mm)')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(plot_bone_names)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    # XYZ軸別の最大相対変位（3条件対応レイアウト調整）
    ax = axes[1, 1]
    axis_names = ['X', 'Y', 'Z']
    
    bar_width = 0.15
    bone_spacing = 1.0
    
    for bone_idx, bone_name in enumerate(plot_bone_names):
        for cond_idx, condition in enumerate(conditions):
            if bone_name in translation_results[condition]:
                bone_data = translation_results[condition][bone_name]
                if bone_data:
                    x_vals = [result['statistics']['max_abs_x'] for result in bone_data]
                    y_vals = [result['statistics']['max_abs_y'] for result in bone_data]
                    z_vals = [result['statistics']['max_abs_z'] for result in bone_data]
                    
                    xyz_means = [np.mean(x_vals), np.mean(y_vals), np.mean(z_vals)]
                    xyz_stds = [np.std(x_vals), np.std(y_vals), np.std(z_vals)]
                    
                    base_x = bone_idx * bone_spacing * len(conditions) + cond_idx * bone_spacing
                    x_positions = [base_x + i * bar_width for i in range(3)]
                    
                    bars = ax.bar(x_positions, xyz_means, yerr=xyz_stds, width=bar_width, 
                                 alpha=0.8, color=colors[cond_idx % len(colors)],
                                 label=f'{bone_name}-{condition}' if bone_idx == 0 else "")
                    
                    for i, bar in enumerate(bars):
                        if i == 1:
                            bar.set_hatch('//')
                        elif i == 2:
                            bar.set_hatch('xxx')
    
    ax.set_title(f'XYZ軸別最大相対変位（vs {reference_bone}）')
    ax.set_ylabel('最大相対変位 (mm)')
    
    tick_positions = []
    tick_labels = []
    for bone_idx, bone_name in enumerate(plot_bone_names):
        center_pos = bone_idx * bone_spacing * len(conditions) + (len(conditions) - 1) * bone_spacing / 2
        tick_positions.append(center_pos + bar_width)
        tick_labels.append(bone_name)
    
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)
    ax.grid(True, alpha=0.3)
    
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles[:len(conditions)], [f'{cond}' for cond in conditions], 
                 title='条件', loc='upper right')
    
    plt.tight_layout()
    plt.savefig(f'relative_translation_statistics_vs_{reference_bone}_{len(conditions)}conditions.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_translation_trajectory_3d(translation_results, bone_names=['Capitate', 'Scafoid'], reference_bone='Lunate'):
    """3次元軌跡プロット（Lunate相対座標系）"""
    from mpl_toolkits.mplot3d import Axes3D
    
    conditions = list(translation_results.keys())
    
    for bone_name in bone_names:
        if bone_name == reference_bone:
            continue
            
        fig = plt.figure(figsize=(15, 6))
        
        for condition_idx, condition in enumerate(conditions):
            ax = fig.add_subplot(1, len(conditions), condition_idx + 1, projection='3d')
            
            if bone_name in translation_results[condition]:
                bone_data = translation_results[condition][bone_name]
                if bone_data:
                    colors = plt.cm.viridis(np.linspace(0, 1, len(bone_data)))
                    
                    for subject_idx, result in enumerate(bone_data):
                        displacement = result.get('relative_displacement', result.get('displacement', None))
                        if displacement is not None:
                            # 軌跡をプロット
                            ax.plot(displacement[:, 0], displacement[:, 1], displacement[:, 2], 
                                   color=colors[subject_idx], alpha=0.7, linewidth=1.5,
                                   label=f"Subject {subject_idx+1}")
                            
                            # 開始点と終了点をマーク
                            ax.scatter(displacement[0, 0], displacement[0, 1], displacement[0, 2], 
                                     color=colors[subject_idx], s=50, marker='o')
                            ax.scatter(displacement[-1, 0], displacement[-1, 1], displacement[-1, 2], 
                                     color=colors[subject_idx], s=50, marker='s')
            
            ax.set_title(f'{bone_name} vs {reference_bone}\n{condition}', fontsize=12)
            ax.set_xlabel('X軸相対変位 (mm)')
            ax.set_ylabel('Y軸相対変位 (mm)')
            ax.set_zlabel('Z軸相対変位 (mm)')
            ax.grid(True, alpha=0.3)
            
            # 原点を明示
            ax.scatter([0], [0], [0], color='red', s=100, marker='*', label='Origin')
        
        plt.suptitle(f'{bone_name} - 3次元相対変位軌跡 (vs {reference_bone})', fontsize=16)
        plt.tight_layout()
        plt.savefig(f'3d_trajectory_{bone_name}_vs_{reference_bone}.png', dpi=300, bbox_inches='tight')
        plt.show()