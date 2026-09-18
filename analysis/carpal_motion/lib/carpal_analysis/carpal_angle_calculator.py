"""
手根骨モーションキャプチャー - 角度計算モジュール
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
from lib.carpal_analysis.carpal_data_loader import extract_bone_data

def quaternion_to_euler(quaternions):
    """クォータニオンをオイラー角（度）に変換"""
    cleaned_quaternions = []
    
    for i, quat in enumerate(quaternions):
        norm = np.linalg.norm(quat)
        
        if norm < 1e-6:
            cleaned_quaternions.append([0, 0, 0, 1])
        else:
            normalized_quat = quat / norm
            cleaned_quaternions.append(normalized_quat)
    
    cleaned_quaternions = np.array(cleaned_quaternions)
    
    try:
        rotations = R.from_quat(cleaned_quaternions)
        euler_angles = rotations.as_euler('xyz', degrees=True)
        return euler_angles
    except Exception as e:
        print(f"Warning: Error in quaternion conversion: {e}")
        return np.zeros((len(quaternions), 3))

def calculate_relative_angles_in_lunate_frame(df, bone_structure, target_bone, reference_bone='Lunate'):
    """
    Lunate座標系を基準とした相対角度変化を計算
    
    Parameters:
    -----------
    df : pandas.DataFrame
        モーションキャプチャーデータ
    bone_structure : dict
        骨の構造情報
    target_bone : str
        目標骨の名前
    reference_bone : str
        基準骨の名前（デフォルト: 'Lunate'）
        
    Returns:
    --------
    dict : 相対角度データ
    """
    try:
        print(f"  処理中（Lunate座標系）: {target_bone} vs {reference_bone}")
        
        # 基準骨（Lunate）のデータを取得
        ref_time, _, ref_quaternion = extract_bone_data(df, bone_structure, reference_bone)
        
        # 目標骨のデータを取得
        time, _, target_quaternion = extract_bone_data(df, bone_structure, target_bone)
        
        # データの長さを統一
        min_len = min(len(ref_time), len(time))
        ref_time = ref_time[:min_len]
        time = time[:min_len]
        ref_quaternion = ref_quaternion[:min_len]
        target_quaternion = target_quaternion[:min_len]
        
        print(f"    データ長: {min_len}, 基準骨: {reference_bone}, 目標骨: {target_bone}")
        
        # 各時刻でのLunate座標系における目標骨の姿勢を計算
        relative_quaternions = []
        
        for i in range(len(time)):
            q_lunate = R.from_quat(ref_quaternion[i])
            q_target = R.from_quat(target_quaternion[i])
            
            # Lunate座標系での目標骨の姿勢
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
        
        # 正規化されたクォータニオンをオイラー角に変換
        relative_euler_angles = quaternion_to_euler(normalized_relative_quaternions)
        
        # 角度の連続性を保つ
        for j in range(3):
            relative_euler_angles[:, j] = np.unwrap(relative_euler_angles[:, j] * np.pi / 180) * 180 / np.pi
        
        # 初期オフセット除去の検証
        initial_check = np.max(np.abs(relative_euler_angles[0]))
        if initial_check > 1e-3:
            print(f"    警告: 初期角度が完全に0になっていません (最大偏差: {initial_check:.6f}度)")
        
        # 異常値のチェックと修正
        if np.any(np.isnan(relative_euler_angles)) or np.any(np.isinf(relative_euler_angles)):
            print(f"    警告: 無効な値を検出 {target_bone} vs {reference_bone}")
            relative_euler_angles = np.nan_to_num(relative_euler_angles, nan=0.0, posinf=0.0, neginf=0.0)
        
        # 統計情報を計算
        angle_stats = {
            'max_abs': np.max(np.abs(relative_euler_angles), axis=0),
            'rms': np.sqrt(np.mean(relative_euler_angles**2, axis=0)),
            'range': np.max(relative_euler_angles, axis=0) - np.min(relative_euler_angles, axis=0)
        }
        
        print(f"    最大絶対角度: X={angle_stats['max_abs'][0]:.2f}°, Y={angle_stats['max_abs'][1]:.2f}°, Z={angle_stats['max_abs'][2]:.2f}°")
        
        return {
            'time': time,
            'relative_angles': relative_euler_angles,
            'relative_quaternions': normalized_relative_quaternions,
            'target_bone': target_bone,
            'reference_bone': reference_bone,
            'coordinate_frame': 'true_lunate_frame',
            'data_length': len(time),
            'statistics': angle_stats,
            'algorithm_version': 'improved_v2.0'
        }
        
    except Exception as e:
        raise ValueError(f"Error calculating relative angles in Lunate frame for {target_bone} vs {reference_bone}: {str(e)}")

def verify_lunate_algorithm(result_dict):
    """Lunateアルゴリズムの結果を検証する関数"""
    angles = result_dict['relative_angles']
    
    verification = {
        'algorithm_version': result_dict.get('algorithm_version', 'unknown'),
        'coordinate_frame': result_dict.get('coordinate_frame', 'unknown'),
        
        # 初期角度の検証
        'initial_angles': angles[0],
        'initial_max_deviation': np.max(np.abs(angles[0])),
        'is_properly_initialized': np.max(np.abs(angles[0])) < 1e-3,
        
        # データ品質の検証
        'has_nan': np.any(np.isnan(angles)),
        'has_inf': np.any(np.isinf(angles)),
        'data_length': len(angles),
        
        # 統計情報
        'angle_ranges': np.max(angles, axis=0) - np.min(angles, axis=0),
        'max_absolute_angles': np.max(np.abs(angles), axis=0),
        
        # 推奨事項
        'recommendations': []
    }
    
    # 推奨事項の生成
    if not verification['is_properly_initialized']:
        verification['recommendations'].append("初期角度の正規化に問題があります")
    
    if verification['has_nan'] or verification['has_inf']:
        verification['recommendations'].append("データに無効値が含まれています")
    
    if np.any(verification['max_absolute_angles'] > 90):
        verification['recommendations'].append("90度を超える大きな角度変化が検出されました")
    
    if verification['data_length'] < 100:
        verification['recommendations'].append("データ点数が少なすぎる可能性があります")
    
    return verification

def test_improved_algorithm(df, bone_structure):
    """改善版アルゴリズムのテスト実行"""
    print("\n=== 改善版Lunateアルゴリズムのテスト ===")
    
    target_bones = ['Scafoid', 'Capitate']
    reference_bone = 'Lunate'
    
    for target_bone in target_bones:
        try:
            result = calculate_relative_angles_in_lunate_frame(
                df, bone_structure, target_bone, reference_bone
            )
            
            verification = verify_lunate_algorithm(result)
            
            print(f"\n{target_bone}の検証結果:")
            print(f"  - アルゴリズム: {verification['algorithm_version']}")
            print(f"  - 座標系: {verification['coordinate_frame']}")
            print(f"  - 初期化: {'✅ 正常' if verification['is_properly_initialized'] else '❌ 問題あり'}")
            print(f"  - データ品質: {'✅ 正常' if not (verification['has_nan'] or verification['has_inf']) else '❌ 無効値あり'}")
            print(f"  - 最大角度: X={verification['max_absolute_angles'][0]:.2f}°, Y={verification['max_absolute_angles'][1]:.2f}°, Z={verification['max_absolute_angles'][2]:.2f}°")
            
            if verification['recommendations']:
                print("  - 推奨事項:")
                for rec in verification['recommendations']:
                    print(f"    • {rec}")
            
        except Exception as e:
            print(f"  ❌ {target_bone}の処理中にエラー: {e}")
    
    print("\n=== テスト完了 ===")

def calculate_angle_statistics(relative_angles):
    """
    相対角度の統計情報を計算
    
    Parameters:
    -----------
    relative_angles : numpy.ndarray
        相対角度データ (N x 3)
        
    Returns:
    --------
    dict : 統計情報
    """
        # 角度ノルム（総回転量）を計算
    angle_norms = np.linalg.norm(relative_angles, axis=1)
    return {
        'max_abs': np.max(np.abs(relative_angles), axis=0),
        'rms': np.sqrt(np.mean(relative_angles**2, axis=0)),
        'std': np.std(relative_angles, axis=0),
        'mean': np.mean(relative_angles, axis=0),
        'final': relative_angles[-1],
        'range': np.max(relative_angles, axis=0) - np.min(relative_angles, axis=0),
        'angle_norm': angle_norms,
        'max_total_rotation': np.max(angle_norms),
        'mean_total_rotation': np.mean(angle_norms),
        'final_total_rotation': angle_norms[-1],
        'rms_total_rotation': np.sqrt(np.mean(angle_norms**2)),
        'total_rotation_range': np.max(angle_norms) - np.min(angle_norms)
    }