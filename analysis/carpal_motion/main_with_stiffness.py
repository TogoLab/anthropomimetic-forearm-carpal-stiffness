"""
並進運動量解析・手首剛性解析を統合した手根骨モーション解析（統合版）
"""

import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.signal import find_peaks, butter, lfilter
from pathlib import Path

from lib.carpal_analysis.carpal_data_loader import (
    load_dataset_from_directory, print_dataset_summary, extract_bone_data,
    load_motion_capture_data, kalman_filter_1d, butter_lowpass_filter
)
from lib.carpal_analysis.carpal_angle_calculator import calculate_angle_statistics
from lib.carpal_analysis.force_displacement_visualization import run_clean_unified_visualization
from lib.carpal_analysis.carpal_translation_analyzer import (
    calculate_translation_motion, 
    calculate_relative_translation_motion
)
from lib.carpal_analysis.wrist_stiffness_analyzer import (
    calculate_wrist_stiffness, run_wrist_stiffness_analysis
)
from scipy.spatial.transform import Rotation as R

def calculate_standard_error(values):
    """標準誤差を計算する関数"""
    if len(values) == 0:
        return 0.0
    return np.std(values) / np.sqrt(len(values))

def get_force_sensor_headers():
    """Force sensorのヘッダー定義"""
    headers = ['timestamp']
    for i in range(1, 23):
        headers.extend([f'cur_{i}', f'pos_{i}'])
    headers.append('force_gage')
    return headers

def calculate_velocity(displacement, time):
    """中心差分法による速度計算"""
    if isinstance(displacement, pd.Series):
        displacement = displacement.values
    if isinstance(time, pd.Series):
        time = time.values
        
    velocity = np.zeros_like(displacement)
    velocity[1:-1] = (displacement[2:] - displacement[:-2]) / (time[2:] - time[:-2])
    
    velocity[0] = (displacement[1] - displacement[0]) / (time[1] - time[0])
    velocity[-1] = (displacement[-1] - displacement[-2]) / (time[-1] - time[-2])
    
    return velocity

def detect_contact_with_analysis_delay(velocity_filtered, force_data, force_time, 
                                     skip_index=0, min_force=1.0, max_time_seconds=2.0,
                                     analysis_delay_seconds=0.5):
    """力優先ピーク検出 + 接触判定後0.5秒から解析区間開始"""
    
    if len(velocity_filtered) <= skip_index + 10:
        return skip_index, skip_index, 0.0
    
    time_mask = force_time <= max_time_seconds
    if not np.any(time_mask):
        search_end = len(force_time) - 1
    else:
        search_end = min(np.where(time_mask)[0][-1], len(velocity_filtered) - 1)
    
    print(f"    検索範囲: index {skip_index} - {search_end} (時間: 0 - {max_time_seconds}s)")
    
    force_valid_mask = force_data[skip_index:search_end + 1] >= min_force
    
    if not np.any(force_valid_mask):
        print(f"    警告: 力が{min_force}N以上の区間が見つかりません")
        contact_index = skip_index + np.argmax(velocity_filtered[skip_index:search_end + 1])
        peak_velocity = velocity_filtered[contact_index]
    else:
        valid_velocities = velocity_filtered[skip_index:search_end + 1].copy()
        valid_velocities[~force_valid_mask] = -np.inf
        
        max_vel_relative_idx = np.argmax(valid_velocities)
        contact_index = skip_index + max_vel_relative_idx
        peak_velocity = velocity_filtered[contact_index]
        
        print(f"    接触判定（ピーク）: index={contact_index}, 時刻={force_time[contact_index]:.3f}s, 速度={peak_velocity:.2f}mm/s, 力={force_data[contact_index]:.2f}N")
    
    contact_time = force_time[contact_index]
    analysis_start_time = contact_time + analysis_delay_seconds
    
    time_diff = np.abs(force_time - analysis_start_time)
    analysis_start_index = np.argmin(time_diff)
    
    if analysis_start_index >= len(force_time):
        analysis_start_index = len(force_time) - 1
        print(f"    警告: 解析開始点がデータ範囲を超えたため、最終点を使用")
    
    actual_delay = force_time[analysis_start_index] - contact_time
    
    print(f"    解析開始点: index={analysis_start_index}, 時刻={force_time[analysis_start_index]:.3f}s")
    print(f"    実際の遅延時間: {actual_delay:.3f}s (目標: {analysis_delay_seconds}s)")
    
    return analysis_start_index, contact_index, peak_velocity

def analyze_with_enhanced_force_detection_and_translation_v3(motion_csv, force_csv, 
                                                           target_bones=['Lunate', 'Capitate', 'Scafoid'],
                                                           start_force=1.0,
                                                           measurement_distance=5.0,
                                                           use_kalman=True,
                                                           apply_smoothing=True,
                                                           apply_advanced_filtering=False,
                                                           middle_plot=False,
                                                           subject_id="",
                                                           condition="",
                                                           analysis_delay_seconds=0.5):
    """Force解析・並進運動量解析・手首剛性解析を統合"""
    
    motion_df, bone_structure = load_motion_capture_data(
        motion_csv, 
        apply_smoothing=apply_smoothing,
        smoothing_window=11
    )
    force_df = load_and_process_force_sensor_data(force_csv)
    
    force_time = force_df['timestamp'].values * 0.001
    force_data = force_df['force_gage'].values
    
    if use_kalman:
        force_data_filtered = kalman_filter_1d(
            force_data, 
            process_variance=1e-5,
            measurement_variance=1e-2
        )
    else:
        fs = 1.0 / ((force_time.max() - force_time.min()) / len(force_data))
        cutoff = 2.0
        order = 4
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        force_data_filtered = lfilter(b, a, force_data)
    
    motion_time = motion_df['Time (Seconds)'].values
    analysis_start_index = 0
    end_index = len(force_time) - 1
    force_gage_displacement = None
    wrist_stiffness_data = None
    
    # Force Gage解析
    if 'ForceGage' in bone_structure:
        fg_time, fg_position, _ = extract_bone_data(
            motion_df, bone_structure, 'ForceGage',
            apply_advanced_filtering=apply_advanced_filtering,
            use_kalman=use_kalman
        )
        
        initial_pos = fg_position[0]
        displacement_3d = np.sqrt(np.sum((fg_position - initial_pos)**2, axis=1))
        
        interpolator = interp1d(fg_time, displacement_3d, kind='linear', bounds_error=False)
        displacement_resampled = interpolator(force_time)
        displacement_resampled = np.nan_to_num(displacement_resampled, nan=0.0)
        
        if use_kalman:
            displacement_filtered = kalman_filter_1d(displacement_resampled)
        else:
            displacement_filtered = lfilter(b, a, displacement_resampled)
        
        velocity = calculate_velocity(displacement_filtered, force_time)
        if use_kalman:
            velocity_filtered = kalman_filter_1d(velocity)
        else:
            velocity_filtered = lfilter(b, a, velocity)
        
        skip_index = int(len(velocity_filtered) * 0.05)
        
        analysis_start_index, contact_index, peak_velocity = detect_contact_with_analysis_delay(
            velocity_filtered, force_data_filtered, force_time,
            skip_index=skip_index, 
            min_force=start_force, 
            max_time_seconds=1.5,
            analysis_delay_seconds=analysis_delay_seconds
        )
        
        target_displacement = displacement_filtered[analysis_start_index] + measurement_distance
        displacement_after_start = displacement_filtered[analysis_start_index:]
        end_indices = np.where(displacement_after_start > target_displacement)[0]
        
        if len(end_indices) > 0:
            end_index = analysis_start_index + end_indices[0]
        else:
            end_index = min(len(displacement_filtered) - 1, 
                          analysis_start_index + int(len(displacement_filtered) * 0.2))
        
        # 解析区間のデータを抽出
        analysis_force = force_data_filtered[analysis_start_index:end_index+1]
        analysis_displacement = displacement_filtered[analysis_start_index:end_index+1] - displacement_filtered[analysis_start_index]
        
        # 手首剛性計算
        print(f"  {subject_id}: 手首剛性計算中...")
        wrist_stiffness_data = calculate_wrist_stiffness(
            analysis_force, analysis_displacement, subject_id, condition
        )
        
        # 実際の変位データから設定値基準での補間を実行
        raw_force_gage_displacement = analysis_displacement
        
        if middle_plot:
            # import lib.carpal_analysis.force_analysis_plotter as plotter
            import lib.carpal_analysis.force_analysis_plotter_with_regression as plotter
            plotter.plot_force_analysis_middle(
                force_time, force_data_filtered, displacement_filtered,
                analysis_start_index, end_index, 
                velocity_data=velocity_filtered, peak_index=contact_index,
                subject_id=subject_id, condition=condition
            )
        
        contact_time = force_time[contact_index]
        analysis_start_time = force_time[analysis_start_index]
        end_time = force_time[end_index]
        
        print(f"  解析区間: index {analysis_start_index}-{end_index} (time: {analysis_start_time:.3f}-{end_time:.3f}s)")
        
        # 設定値基準でのForceGage変位軸を作成（解析段階でも統一）
        normalized_force_displacement = np.linspace(0.0, measurement_distance, 100)
        
        # 各骨データを補間してforce_timeに合わせ、その後設定値基準で再補間
        interpolated_motion_data = {}
        
        for bone_name in target_bones:
            if bone_name in bone_structure:
                try:
                    bone_time, bone_position, bone_quaternion = extract_bone_data(
                        motion_df, bone_structure, bone_name,
                        apply_advanced_filtering=apply_advanced_filtering,
                        use_kalman=use_kalman
                    )
                    
                    # 位置データを補間（XYZ軸別）
                    interpolated_position = np.zeros((len(force_time), 3))
                    for axis in range(3):
                        if bone_position.shape[1] > axis:
                            pos_interpolator = interp1d(bone_time, bone_position[:, axis], 
                                                      kind='linear', bounds_error=False, fill_value=0.0)
                            interpolated_position[:, axis] = pos_interpolator(force_time)
                    
                    # クォータニオンデータを補間（XYZW軸別）
                    interpolated_quaternion = np.zeros((len(force_time), 4))
                    for axis in range(4):
                        if bone_quaternion.shape[1] > axis:
                            quat_interpolator = interp1d(bone_time, bone_quaternion[:, axis], 
                                                       kind='linear', bounds_error=False, fill_value=0.0)
                            interpolated_quaternion[:, axis] = quat_interpolator(force_time)
                    
                    # クォータニオンの正規化
                    for i in range(len(interpolated_quaternion)):
                        norm = np.linalg.norm(interpolated_quaternion[i])
                        if norm > 1e-6:
                            interpolated_quaternion[i] /= norm
                        else:
                            interpolated_quaternion[i] = [0, 0, 0, 1]
                    
                    # 解析区間のデータを抽出
                    analysis_position_raw = interpolated_position[analysis_start_index:end_index+1]
                    analysis_quaternion_raw = interpolated_quaternion[analysis_start_index:end_index+1]
                    
                    # 設定値基準での再補間（位置データ）
                    if len(raw_force_gage_displacement) == len(analysis_position_raw) and len(raw_force_gage_displacement) > 1:
                        normalized_position = np.zeros((len(normalized_force_displacement), 3))
                        for axis in range(3):
                            try:
                                interp_func = interp1d(raw_force_gage_displacement, analysis_position_raw[:, axis], 
                                                     kind='linear', bounds_error=False, fill_value='extrapolate')
                                normalized_position[:, axis] = interp_func(normalized_force_displacement)
                            except:
                                normalized_position[:, axis] = analysis_position_raw[0, axis]
                        
                        # 設定値基準での再補間（クォータニオンデータ）
                        normalized_quaternion = np.zeros((len(normalized_force_displacement), 4))
                        for axis in range(4):
                            try:
                                interp_func = interp1d(raw_force_gage_displacement, analysis_quaternion_raw[:, axis], 
                                                     kind='linear', bounds_error=False, fill_value='extrapolate')
                                normalized_quaternion[:, axis] = interp_func(normalized_force_displacement)
                            except:
                                normalized_quaternion[:, axis] = analysis_quaternion_raw[0, axis]
                        
                        # クォータニオンの再正規化
                        for i in range(len(normalized_quaternion)):
                            norm = np.linalg.norm(normalized_quaternion[i])
                            if norm > 1e-6:
                                normalized_quaternion[i] /= norm
                            else:
                                normalized_quaternion[i] = [0, 0, 0, 1]
                        
                        # 設定値基準での時間軸を作成
                        normalized_time = np.linspace(analysis_start_time, 
                                                    analysis_start_time + (end_time - analysis_start_time), 
                                                    len(normalized_force_displacement))
                        
                        interpolated_motion_data[bone_name] = {
                            'time': normalized_time,
                            'position': normalized_position,
                            'quaternion': normalized_quaternion
                        }
                        
                        print(f"  {bone_name}: 設定値基準補間完了 (データ長: {len(normalized_time)})")
                    
                    else:
                        print(f"  {bone_name}: データ長不一致のため補間スキップ")
                    
                except Exception as e:
                    print(f"  {bone_name}: 補間エラー - {e}")
        
        # 設定値基準のForceGage変位データを保存
        force_gage_displacement = normalized_force_displacement
        
        analysis_info = {
            'contact_time': contact_time,
            'analysis_start_time': analysis_start_time,
            'end_time': end_time,
            'contact_force': force_data_filtered[contact_index],
            'analysis_start_force': force_data_filtered[analysis_start_index],
            'end_force': force_data_filtered[end_index],
            'displacement_range': measurement_distance,
            'peak_velocity': peak_velocity,
            'analysis_delay_seconds': analysis_delay_seconds,
            'contact_index': contact_index,
            'analysis_method': 'enhanced_force_detection_with_interpolation_v3'
        }
        
    else:
        interpolated_motion_data = {}
        analysis_info = {
            'analysis_method': 'full_data',
            'contact_time': motion_time[0],
            'end_time': motion_time[-1]
        }
    
    # 並進運動量解析（設定値基準補間済みデータを使用）
    translation_data = {}
    for bone_name in target_bones:
        if bone_name in interpolated_motion_data:
            try:
                if 'Lunate' in interpolated_motion_data:
                    lunate_data = interpolated_motion_data['Lunate']
                    bone_data = interpolated_motion_data[bone_name]
                    
                    # Lunateに対する相対位置を計算（設定値基準データで）
                    relative_position = bone_data['position'] - lunate_data['position']
                    
                    # 初期相対位置を基準とした相対変位
                    initial_relative_position = relative_position[0]
                    relative_displacement = relative_position - initial_relative_position
                    
                    # 3次元相対変位の大きさ
                    relative_displacement_magnitude = np.sqrt(np.sum(relative_displacement**2, axis=1))
                    
                    # 統計情報計算（設定値基準データで計算）
                    stats = {
                        'max_displacement': np.max(relative_displacement_magnitude),
                        'final_displacement': relative_displacement_magnitude[-1],
                        'mean_displacement': np.mean(relative_displacement_magnitude),
                        'std_displacement': np.std(relative_displacement_magnitude),
                        'max_abs_x': np.max(np.abs(relative_displacement[:, 0])),
                        'max_abs_y': np.max(np.abs(relative_displacement[:, 1])),
                        'max_abs_z': np.max(np.abs(relative_displacement[:, 2])),
                        'range_x': np.max(relative_displacement[:, 0]) - np.min(relative_displacement[:, 0]),
                        'range_y': np.max(relative_displacement[:, 1]) - np.min(relative_displacement[:, 1]),
                        'range_z': np.max(relative_displacement[:, 2]) - np.min(relative_displacement[:, 2]),
                        'final_x': relative_displacement[-1, 0],
                        'final_y': relative_displacement[-1, 1],
                        'final_z': relative_displacement[-1, 2],
                        'coordinate_frame': 'relative_to_Lunate_normalized',
                        'reference_bone': 'Lunate',
                        'measurement_distance': measurement_distance,
                        'normalization_method': 'force_displacement_based'
                    }
                    
                    translation_data[bone_name] = {
                        'time': bone_data['time'],
                        'relative_displacement': relative_displacement,
                        'displacement': relative_displacement,
                        'relative_displacement_magnitude': relative_displacement_magnitude,
                        'displacement_magnitude': relative_displacement_magnitude,
                        'bone_name': bone_name,
                        'reference_bone': 'Lunate',
                        'statistics': stats,
                        'data_length': len(bone_data['time'])
                    }
                    
                    print(f"  {subject_id} {bone_name}: 設定値基準Lunate相対並進解析完了 (データ長: {len(bone_data['time'])})")
                
            except Exception as e:
                print(f"  {subject_id} {bone_name}: 並進解析エラー - {e}")
    
    return {
        'motion_data': None,
        'bone_structure': bone_structure,
        'analysis_info': analysis_info,
        'translation_data': translation_data,
        'interpolated_motion_data': interpolated_motion_data,
        'wrist_stiffness_data': wrist_stiffness_data,  # 手首剛性データを追加
        'force_data': {
            'time': force_time,
            'force': force_data_filtered,
            'contact_index': contact_index,
            'analysis_start_index': analysis_start_index,
            'end_index': end_index,
            'peak_velocity': peak_velocity
        },
        'force_gage_displacement': force_gage_displacement
    }

def load_and_process_force_sensor_data(force_csv_path):
    """Force sensorデータの読み込みと処理"""
    headers = get_force_sensor_headers()
    
    try:
        df = pd.read_csv(force_csv_path, names=headers)
    except:
        df = pd.read_csv(force_csv_path)
        if 'force_gage' not in df.columns:
            raise ValueError("force_gage column not found")
    
    valid_mask = np.isfinite(df['timestamp']) & np.isfinite(df['force_gage'])
    df_clean = df[valid_mask].reset_index(drop=True)
    
    if len(df_clean) < 10:
        raise ValueError("Too few valid data points")
    
    return df_clean

def enhanced_carpal_analysis_with_translation_and_stiffness(datasets, angle_bone_names, translation_bone_names, 
                                                          reference_bone='Lunate', force_sensor_dir=None, 
                                                          middle_plot=False, apply_smoothing=True, 
                                                          apply_advanced_filtering=False, 
                                                          analysis_delay_seconds=0.5, **analysis_params):
    """角度解析・並進運動量解析・手首剛性解析を統合したメイン関数"""
    print("Enhanced carpal analysis with translation and wrist stiffness")
    if apply_smoothing:
        print("移動平均平滑化: 有効")
    if apply_advanced_filtering:
        print("高度フィルタリング: 有効")
    print(f"接触判定後遅延: {analysis_delay_seconds}秒")
    
    analysis_results = {}
    translation_results = {}
    stiffness_results = {}  # 手首剛性結果を追加
    
    for condition_name, dataset in datasets.items():
        print(f"Condition: {condition_name}")
        condition_angle_results = {}
        condition_translation_results = {}
        condition_stiffness_results = []  # 条件別手首剛性結果
        
        for subject_id, file_data in dataset.items():
            try:
                df = file_data['data']
                bone_structure = file_data['bone_structure']
                
                force_gage_displacement = None
                interpolated_motion_data = None
                translation_data = {}
                wrist_stiffness_data = None
                
                if force_sensor_dir:
                    motion_csv_path = file_data['file_path']
                    force_csv_name = motion_csv_path.stem + '.csv'
                    force_csv_path = Path(force_sensor_dir) / force_csv_name
                    
                    if force_csv_path.exists():
                        enhanced_result = analyze_with_enhanced_force_detection_and_translation_v3(
                            motion_csv_path, force_csv_path,
                            target_bones=translation_bone_names + [reference_bone],
                            apply_smoothing=apply_smoothing,
                            apply_advanced_filtering=apply_advanced_filtering,
                            middle_plot=middle_plot,
                            subject_id=subject_id,
                            condition=condition_name,
                            analysis_delay_seconds=analysis_delay_seconds,
                            **analysis_params
                        )
                        interval_info = enhanced_result['analysis_info']
                        translation_data = enhanced_result['translation_data']
                        interpolated_motion_data = enhanced_result['interpolated_motion_data']
                        wrist_stiffness_data = enhanced_result['wrist_stiffness_data']  # 手首剛性データ取得
                        
                        if 'force_gage_displacement' in enhanced_result:
                            force_gage_displacement = enhanced_result['force_gage_displacement']
                    else:
                        print(f"  {subject_id}: Force sensor file not found")
                        interval_info = None
                        translation_data = {}
                        wrist_stiffness_data = None
                else:
                    interval_info = None
                    translation_data = {}
                    wrist_stiffness_data = None
                
                # 手首剛性データの保存
                if wrist_stiffness_data is not None:
                    condition_stiffness_results.append(wrist_stiffness_data)
                
                # 並進運動データの保存（設定値基準データ）
                for trans_bone_name, trans_data in translation_data.items():
                    if trans_bone_name not in condition_translation_results:
                        condition_translation_results[trans_bone_name] = []
                    
                    condition_translation_results[trans_bone_name].append({
                        'subject_id': subject_id,
                        'time': trans_data['time'],
                        'displacement': trans_data.get('displacement', trans_data.get('relative_displacement')),
                        'relative_displacement': trans_data.get('relative_displacement', trans_data.get('displacement')),
                        'displacement_magnitude': trans_data.get('displacement_magnitude', trans_data.get('relative_displacement_magnitude')),
                        'relative_displacement_magnitude': trans_data.get('relative_displacement_magnitude', trans_data.get('displacement_magnitude')),
                        'statistics': trans_data['statistics'],
                        'force_gage_displacement': force_gage_displacement,  # 設定値基準の変位データ
                        'normalization_method': 'force_displacement_based'
                    })
                
                # 角度解析（設定値基準補間済みデータを使用）
                for bone_name in angle_bone_names:
                    if bone_name not in bone_structure or reference_bone not in bone_structure:
                        continue
                    
                    if bone_name not in condition_angle_results:
                        condition_angle_results[bone_name] = []
                    
                    # 角度解析（設定値基準補間済みデータを使用）
                    if interpolated_motion_data and bone_name in interpolated_motion_data and reference_bone in interpolated_motion_data:
                        bone_data = interpolated_motion_data[bone_name]
                        ref_data = interpolated_motion_data[reference_bone]
                        
                        # クォータニオンから相対角度を計算（設定値基準データで）
                        relative_quaternions = []
                        for i in range(len(bone_data['time'])):
                            q_lunate = R.from_quat(ref_data['quaternion'][i])
                            q_target = R.from_quat(bone_data['quaternion'][i])
                            
                            q_in_lunate_frame = q_lunate.inv() * q_target
                            relative_quaternions.append(q_in_lunate_frame.as_quat())
                        
                        relative_quaternions = np.array(relative_quaternions)
                        
                        # t=0での姿勢を基準として初期オフセットを除去
                        q_initial = R.from_quat(relative_quaternions[0])
                        
                        normalized_relative_quaternions = []
                        for i in range(len(relative_quaternions)):
                            q_current = R.from_quat(relative_quaternions[i])
                            q_change = q_initial.inv() * q_current
                            normalized_relative_quaternions.append(q_change.as_quat())
                        
                        normalized_relative_quaternions = np.array(normalized_relative_quaternions)
                        
                        # クォータニオンをオイラー角に変換
                        rotations = R.from_quat(normalized_relative_quaternions)
                        relative_euler_angles = rotations.as_euler('xyz', degrees=True)
                        
                        # 角度の連続性を保つ
                        for j in range(3):
                            relative_euler_angles[:, j] = np.unwrap(relative_euler_angles[:, j] * np.pi / 180) * 180 / np.pi
                        
                        # 統計情報計算（設定値基準データで計算）
                        statistics = calculate_angle_statistics(relative_euler_angles)
                        # 統計情報に設定値基準であることを記録
                        statistics['measurement_distance'] = analysis_params.get('measurement_distance', 3.0)
                        statistics['normalization_method'] = 'force_displacement_based'
                        
                        condition_angle_results[bone_name].append({
                            'subject_id': subject_id,
                            'time': bone_data['time'],
                            'relative_angles': relative_euler_angles,
                            'statistics': statistics,
                            'data_length': len(bone_data['time']),
                            'interval_info': interval_info,
                            'used_enhanced_method': interval_info is not None,
                            'used_smoothing': apply_smoothing,
                            'used_advanced_filtering': apply_advanced_filtering,
                            'analysis_delay_seconds': analysis_delay_seconds,
                            'force_gage_displacement': force_gage_displacement,
                            'normalization_method': 'force_displacement_based'
                        })
                        
                        print(f"  {subject_id} {bone_name}: 設定値基準補間データから角度解析完了 (データ長: {len(bone_data['time'])})")
                    
                    else:
                        # 従来の方法で角度解析（フォールバック）
                        from lib.carpal_analysis.carpal_angle_calculator import calculate_relative_angles_in_lunate_frame
                        
                        analysis_df = df
                        result = calculate_relative_angles_in_lunate_frame(
                            analysis_df, bone_structure, bone_name, reference_bone
                        )
                        
                        statistics = calculate_angle_statistics(result['relative_angles'])
                        
                        condition_angle_results[bone_name].append({
                            'subject_id': subject_id,
                            'time': result['time'],
                            'relative_angles': result['relative_angles'],
                            'statistics': statistics,
                            'data_length': result['data_length'],
                            'interval_info': interval_info,
                            'used_enhanced_method': False,
                            'used_smoothing': apply_smoothing,
                            'used_advanced_filtering': apply_advanced_filtering,
                            'analysis_delay_seconds': analysis_delay_seconds,
                            'force_gage_displacement': None
                        })
                        
                        print(f"  {subject_id} {bone_name}: 従来データから角度解析完了")
                
            except Exception as e:
                print(f"Error {subject_id}: {e}")
                import traceback
                traceback.print_exc()
        
        # 成功率の表示
        for bone_name in angle_bone_names:
            if bone_name in condition_angle_results:
                successful_analyses = len(condition_angle_results[bone_name])
                print(f"  {bone_name}: {successful_analyses}/{len(dataset)} successful")
        
        # 手首剛性の成功率表示
        print(f"  手首剛性: {len(condition_stiffness_results)}/{len(dataset)} successful")
        
        analysis_results[condition_name] = condition_angle_results
        translation_results[condition_name] = condition_translation_results
        stiffness_results[condition_name] = condition_stiffness_results  # 手首剛性結果を保存
    
    return analysis_results, translation_results, stiffness_results

def main_enhanced_analysis_with_translation_and_stiffness(middle_plot=False, apply_smoothing=True,
                                                         apply_advanced_filtering=False,
                                                         analysis_delay_seconds=0.3,
                                                         visualize=True):
    """統一ForceGage変位ベース解析・手首剛性解析メイン関数

    visualize=False のときは既存の統一可視化・剛性可視化をスキップし、
    解析結果 (analysis_results, translation_results, stiffness_results) のみ返す。
    """
    if middle_plot:
        print("Middle plot enabled")
    
    datasets_config = {
        'Wrist_Contraction': {
            'motion_dir': 'datas/carpal_motion/20250803/wrist_contraction/motion_capture/',
            'force_dir': 'datas/carpal_motion/20250803/wrist_contraction/force_gage'
        },
        'Finger_Contraction': {
            'motion_dir': 'datas/carpal_motion/20250803/finger_contraction/motion_capture/',
            'force_dir': 'datas/carpal_motion/20250803/finger_contraction/force_gage'
        },
        'Finger_Wrist_Contraction': {
            'motion_dir': 'datas/carpal_motion/20250803/finger_wrist_contraction/motion_capture/',
            'force_dir': 'datas/carpal_motion/20250803/finger_wrist_contraction/force_gage'
        }
    }
    
    datasets = {}
    
    for condition_name, paths in datasets_config.items():
        try:
            dataset = load_dataset_from_directory(
                paths['motion_dir'],
                apply_smoothing=apply_smoothing,
                smoothing_window=11
            )
            datasets[condition_name] = dataset
            # print_dataset_summary(dataset, condition_name)
        except Exception as e:
            print(f"Error loading {condition_name}: {e}")
    
    if not datasets:
        print("No datasets loaded successfully")
        return None, None, None
    
    angle_bone_names = ['Scafoid', 'Capitate']
    translation_bone_names = ['Capitate', 'Scafoid']
    reference_bone = 'Lunate'
    
    print(f"並進解析対象骨: {translation_bone_names} (基準骨: {reference_bone})")
    print(f"解析対象条件: {list(datasets.keys())}")
    
    analysis_params = {
        'start_force': 1.0,
        'measurement_distance': 3.0,
        'use_kalman': True,
        'analysis_delay_seconds': analysis_delay_seconds
    }
    
    analysis_results = {}
    translation_results = {}
    stiffness_results = {}
    
    for condition_name, dataset in datasets.items():
        # print(f"Analyzing condition: {condition_name}")
        force_sensor_dir = datasets_config[condition_name]['force_dir']
        
        angle_results, trans_results, stiff_results = enhanced_carpal_analysis_with_translation_and_stiffness(
            {condition_name: dataset}, angle_bone_names, translation_bone_names, 
            reference_bone, force_sensor_dir=force_sensor_dir,
            middle_plot=middle_plot, apply_smoothing=apply_smoothing,
            apply_advanced_filtering=apply_advanced_filtering, **analysis_params
        )
        
        analysis_results.update(angle_results)
        translation_results.update(trans_results)
        stiffness_results.update(stiff_results)
    
    print("Enhanced analysis with relative translation and wrist stiffness completed")
    
    # print(f"\n=== 解析結果サマリー（{len(analysis_results)}条件）===")
    # for condition_name, condition_data in analysis_results.items():
    #     total_files = sum(len(bone_data) for bone_data in condition_data.values())
    #     enhanced_used = sum(1 for bone_data in condition_data.values() 
    #                       for result in bone_data if result.get('used_enhanced_method', False))
    #     stiffness_count = len(stiffness_results.get(condition_name, []))
    #     print(f"  {condition_name}: 総ファイル={total_files}, Enhanced解析={enhanced_used}, 手首剛性={stiffness_count}")
    
    if visualize:
        try:
            print("\n統一ForceGage変位ベース可視化（メイン）")

            run_clean_unified_visualization(
                analysis_results,
                translation_results,
                measurement_distance=analysis_params['measurement_distance']
            )

            print("\n手首剛性解析実行")
            run_wrist_stiffness_analysis(stiffness_results)

            print("\nAll unified visualizations completed successfully")

        except ImportError:
            print("統一可視化モジュールが利用できません")
        except Exception as e:
            print(f"統一可視化エラー: {e}")
            import traceback
            traceback.print_exc()

    return analysis_results, translation_results, stiffness_results

if __name__ == "__main__":
    print("解析スタート（手首剛性統合版）")
    main_enhanced_analysis_with_translation_and_stiffness(
        middle_plot=False,
        apply_smoothing=True,
        apply_advanced_filtering=True,
        analysis_delay_seconds=0.5
    )
