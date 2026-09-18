"""
手根骨モーションキャプチャー - データ読み込みモジュール（改良版）
平滑化・高度フィルタリング機能付き
"""

import pandas as pd
import numpy as np
from pathlib import Path
from io import StringIO
from scipy.signal import butter, lfilter

def kalman_filter_1d(data, process_variance=1e-4, measurement_variance=1e-1, initial_estimate=None):
    """1次元カルマンフィルター"""
    n = len(data)
    filtered_data = np.zeros(n)
    
    if initial_estimate is None:
        estimate = data[0]
    else:
        estimate = initial_estimate
    error_covariance = 1.0
    
    for i in range(n):
        predicted_estimate = estimate
        predicted_error_covariance = error_covariance + process_variance
        
        kalman_gain = predicted_error_covariance / (predicted_error_covariance + measurement_variance)
        estimate = predicted_estimate + kalman_gain * (data[i] - predicted_estimate)
        error_covariance = (1 - kalman_gain) * predicted_error_covariance
        
        filtered_data[i] = estimate
    
    return filtered_data

def butter_lowpass_filter(data, cutoff, fs, order=4):
    """バターワースローパスフィルター"""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    filtered_data = lfilter(b, a, data)
    return filtered_data

def load_motion_capture_data(csv_file, apply_smoothing=True, smoothing_window=11):
    """
    モーションキャプチャーCSVファイルを読み込む（平滑化オプション付き）
    
    Parameters:
    -----------
    csv_file : str
        CSVファイルのパス
    apply_smoothing : bool
        移動平均による平滑化を適用するかどうか
    smoothing_window : int
        移動平均のウィンドウサイズ
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data_lines = lines[6:]
    data_text = ''.join(data_lines)
    df = pd.read_csv(StringIO(data_text))
    
    if apply_smoothing:
        df_smoothed = df.dropna(how="all").rolling(
            window=smoothing_window,
            center=True,
            min_periods=1
        ).mean()
        df = df_smoothed.reset_index(drop=True)
        # print(f"平滑化適用: window={smoothing_window}")
    
    name_row = lines[3].strip().split(',')[2:]
    type_row = lines[5].strip().split(',')[2:]
    
    bone_structure = {}
    column_names = df.columns.tolist()[2:]
    
    for i, (bone_name, data_type) in enumerate(zip(name_row, type_row)):
        bone_name = bone_name.strip().replace('\r', '').replace('\n', '')
        data_type = data_type.strip().replace('\r', '').replace('\n', '')
        
        if bone_name and bone_name != 'Name' and bone_name != '':
            if bone_name not in bone_structure:
                bone_structure[bone_name] = {'rotation': [], 'position': []}
            
            if i < len(column_names):
                col_name = column_names[i]
                if data_type == 'Rotation':
                    bone_structure[bone_name]['rotation'].append(col_name)
                elif data_type == 'Position':
                    bone_structure[bone_name]['position'].append(col_name)
    
    return df, bone_structure

def extract_bone_data(df, bone_structure, bone_name, handle_missing='interpolate', 
                     apply_advanced_filtering=False, use_kalman=True):
    """
    特定の骨のデータを抽出する（高度フィルタリングオプション付き）
    
    Parameters:
    -----------
    df : pandas.DataFrame
        モーションキャプチャーデータ
    bone_structure : dict
        骨の構造情報
    bone_name : str
        骨の名前
    handle_missing : str
        欠損値の処理方法
    apply_advanced_filtering : bool
        カルマン/バターワースフィルターを適用するかどうか
    use_kalman : bool
        True: カルマンフィルター, False: バターワースフィルター
    """
    if bone_name not in bone_structure:
        raise ValueError(f"Bone '{bone_name}' not found in data")
    
    structure = bone_structure[bone_name]
    time = df['Time (Seconds)'].values
    
    # 位置データ
    pos_cols = structure['position']
    available_pos_cols = [col for col in pos_cols if col in df.columns]
    
    if len(available_pos_cols) >= 3:
        position = df[available_pos_cols[:3]].values
    elif len(available_pos_cols) > 0:
        temp_pos = df[available_pos_cols].values
        position = np.zeros((len(df), 3))
        position[:, :temp_pos.shape[1]] = temp_pos
    else:
        position = np.zeros((len(df), 3))
    
    # 回転データ
    rot_cols = structure['rotation']
    available_rot_cols = [col for col in rot_cols if col in df.columns]
    
    if len(available_rot_cols) >= 4:
        quaternion = df[available_rot_cols[:4]].values
    elif len(available_rot_cols) > 0:
        temp_rot = df[available_rot_cols].values
        quaternion = np.zeros((len(df), 4))
        quaternion[:, :temp_rot.shape[1]] = temp_rot
        if temp_rot.shape[1] == 3:
            quaternion[:, 3] = 1.0
    else:
        quaternion = np.zeros((len(df), 4))
        quaternion[:, 3] = 1.0
    
    # 欠損値処理
    invalid_mask = np.zeros(len(df), dtype=bool)
    
    time_invalid = np.isnan(time) | np.isinf(time) | (time <= 0)
    invalid_mask |= time_invalid
    
    pos_invalid = np.isnan(position).any(axis=1) | np.isinf(position).any(axis=1)
    invalid_mask |= pos_invalid
    
    quat_invalid = np.isnan(quaternion).any(axis=1) | np.isinf(quaternion).any(axis=1)
    quat_norms = np.linalg.norm(quaternion, axis=1)
    quat_zero_norm = quat_norms < 1e-6
    invalid_mask |= quat_invalid | quat_zero_norm
    
    invalid_count = np.sum(invalid_mask)
    
    if handle_missing == 'remove' and invalid_count > 0:
        valid_mask = ~invalid_mask
        if np.sum(valid_mask) < 10:
            raise ValueError(f"Too few valid frames: {np.sum(valid_mask)}")
        
        time = time[valid_mask]
        position = position[valid_mask]
        quaternion = quaternion[valid_mask]
        
        if len(time) > 1 and np.any(np.diff(time) <= 0):
            raise ValueError("Non-monotonic time data after removing invalid frames")
        
    elif handle_missing == 'forward_fill' and invalid_count > 0:
        for i in range(1, len(quaternion)):
            if invalid_mask[i] and not invalid_mask[i-1]:
                time[i] = time[i-1] + (time[i-1] - time[max(0, i-2)]) if i > 1 else time[i-1] + 0.01
                position[i] = position[i-1]
                quaternion[i] = quaternion[i-1]
        
        if invalid_mask[0]:
            first_valid = np.where(~invalid_mask)[0]
            if len(first_valid) > 0:
                time[0] = max(0.0, time[first_valid[0]] - 0.01)
                position[0] = position[first_valid[0]]
                quaternion[0] = quaternion[first_valid[0]]
            else:
                time[0] = 0.0
                position[0] = [0, 0, 0]
                quaternion[0] = [0, 0, 0, 1]
                
    else:
        if np.any(time_invalid):
            valid_time_indices = np.where(~time_invalid)[0]
            if len(valid_time_indices) > 1:
                time = np.interp(np.arange(len(time)), valid_time_indices, time[valid_time_indices])
            else:
                time = np.arange(len(time)) * 0.01
        
        position = np.nan_to_num(position, nan=0.0, posinf=0.0, neginf=0.0)
        quaternion = np.nan_to_num(quaternion, nan=0.0, posinf=0.0, neginf=0.0)
        
        for i in range(len(quaternion)):
            quat = quaternion[i]
            norm = np.linalg.norm(quat)
            if norm < 1e-6:
                quaternion[i] = [0, 0, 0, 1]
            else:
                quaternion[i] = quat / norm
    
    # 高度フィルタリングの適用（オプション）
    if apply_advanced_filtering and len(time) > 10:
        print(f"  {bone_name}: 高度フィルタリング適用（{'カルマン' if use_kalman else 'バターワース'}）")
        
        # サンプリング周波数の推定
        fs = 1.0 / np.mean(np.diff(time))
        
        # 位置データのフィルタリング
        position_filtered = np.zeros_like(position)
        for axis in range(3):
            if use_kalman:
                position_filtered[:, axis] = kalman_filter_1d(
                    position[:, axis],
                    process_variance=1e-5,
                    measurement_variance=1e-3
                )
            else:
                cutoff = 2.0
                position_filtered[:, axis] = butter_lowpass_filter(
                    position[:, axis], cutoff, fs, order=4
                )
        position = position_filtered
        
        # クォータニオンのフィルタリング
        quaternion_filtered = np.zeros_like(quaternion)
        for axis in range(4):
            if use_kalman:
                quaternion_filtered[:, axis] = kalman_filter_1d(
                    quaternion[:, axis],
                    process_variance=1e-6,
                    measurement_variance=1e-3
                )
            else:
                cutoff = 1.0
                quaternion_filtered[:, axis] = butter_lowpass_filter(
                    quaternion[:, axis], cutoff, fs, order=4
                )
        
        # フィルタリング後のクォータニオン正規化
        for i in range(len(quaternion_filtered)):
            norm = np.linalg.norm(quaternion_filtered[i])
            if norm > 1e-6:
                quaternion_filtered[i] /= norm
            else:
                quaternion_filtered[i] = [0, 0, 0, 1]
        
        quaternion = quaternion_filtered
    
    return time, position, quaternion

def load_dataset_from_directory(directory_path, apply_smoothing=True, smoothing_window=11):
    """ディレクトリ内の全CSVファイルを読み込み（平滑化オプション付き）"""
    directory = Path(directory_path)
    dataset = {}
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    csv_files = list(directory.glob("*.csv"))
    
    if not csv_files:
        raise ValueError(f"No CSV files found in directory: {directory_path}")
    
    for csv_file in csv_files:
        try:
            df, bone_structure = load_motion_capture_data(
                csv_file, 
                apply_smoothing=apply_smoothing,
                smoothing_window=smoothing_window
            )
            dataset[csv_file.stem] = {
                'data': df,
                'bone_structure': bone_structure,
                'file_path': csv_file
            }
        except Exception as e:
            print(f"Error loading {csv_file.name}: {e}")
    
    return dataset

def print_dataset_summary(dataset, dataset_name):
    """データセットの基本情報を表示"""
    print(f"Dataset: {dataset_name}")
    
    for file_name, file_data in dataset.items():
        df = file_data['data']
        bone_structure = file_data['bone_structure']
        
        print(f"  {file_name}: {len(df)} frames, {df['Time (Seconds)'].max():.1f}s, {list(bone_structure.keys())}")

# 既存コードとの互換性を保つための関数
def load_motion_capture_data_legacy(csv_file):
    """既存コードとの互換性のための関数"""
    return load_motion_capture_data(csv_file, apply_smoothing=False)

def extract_bone_data_legacy(df, bone_structure, bone_name, handle_missing='interpolate'):
    """既存コードとの互換性のための関数"""
    return extract_bone_data(df, bone_structure, bone_name, handle_missing, 
                           apply_advanced_filtering=False)