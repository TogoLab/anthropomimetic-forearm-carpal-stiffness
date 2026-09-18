import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from glob import glob 
from scipy import stats
from scipy.interpolate import interp1d
import lib.utils as utils
from scipy.signal import butter, lfilter

# バターワースフィルター関数の定義
def butter_lowpass(cutoff, fs, order=4):
    """
    バターワースローパスフィルターの設計
    
    Parameters:
    cutoff (float): カットオフ周波数 (Hz)
    fs (float): サンプリング周波数 (Hz)
    order (int): フィルターの次数
    
    Returns:
    b, a (tuple): フィルター係数
    """
    nyq = 0.5 * fs  # ナイキスト周波数
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=4):
    """
    バターワースローパスフィルターの適用
    
    Parameters:
    data (array): フィルターを適用するデータ
    cutoff (float): カットオフ周波数 (Hz)
    fs (float): サンプリング周波数 (Hz)
    order (int): フィルターの次数
    
    Returns:
    filtered_data (array): フィルタリング後のデータ
    """
    b, a = butter_lowpass(cutoff, fs, order=order)
    filtered_data = lfilter(b, a, data)
    return filtered_data
# 変位の速度を計算する関数
def calculate_velocity(displacement, time):
    """
    中心差分法による速度計算
    
    Parameters:
    displacement (array): 変位データ
    time (array): 時間データ
    
    Returns:
    velocity (array): 速度データ
    """
    # pandasのSeriesをnumpy配列に変換
    if isinstance(displacement, pd.Series):
        displacement = displacement.values
    if isinstance(time, pd.Series):
        time = time.values
        
    # 中心差分で速度を計算
    velocity = np.zeros_like(displacement)
    velocity[1:-1] = (displacement[2:] - displacement[:-2]) / (time[2:] - time[:-2])
    
    # 端点の処理（前方/後方差分）
    velocity[0] = (displacement[1] - displacement[0]) / (time[1] - time[0])
    velocity[-1] = (displacement[-1] - displacement[-2]) / (time[-1] - time[-2])
    
    return velocity
def kalman_filter_1d(data, process_variance=1e-4, measurement_variance=1e-1, initial_estimate=None):
    """
    1次元カルマンフィルターを適用
    
    Parameters:
    data (array): フィルタリングするデータ
    process_variance (float): プロセスノイズの分散
    measurement_variance (float): 測定ノイズの分散
    initial_estimate (float): 初期推定値（Noneの場合は最初のデータ点を使用）
    
    Returns:
    filtered_data (array): フィルタリング後のデータ
    """
    # データの長さを取得
    n = len(data)
    filtered_data = np.zeros(n)
    
    # 初期推定値とその共分散
    if initial_estimate is None:
        estimate = data[0]
    else:
        estimate = initial_estimate
    error_covariance = 1.0
    
    # カルマンフィルタリングの実行
    for i in range(n):
        # 予測ステップ
        predicted_estimate = estimate  # 簡単な1次元モデルでは状態が持続すると予測
        predicted_error_covariance = error_covariance + process_variance
        
        # 更新ステップ
        # カルマンゲインの計算
        kalman_gain = predicted_error_covariance / (predicted_error_covariance + measurement_variance)
        
        # 推定値の更新
        estimate = predicted_estimate + kalman_gain * (data[i] - predicted_estimate)
        
        # 誤差共分散の更新
        error_covariance = (1 - kalman_gain) * predicted_error_covariance
        
        # フィルタリング結果を格納
        filtered_data[i] = estimate
    
    return filtered_data

def kalman_filter_velocity_position(displacement, time, process_variance_q=1e-5, measurement_variance_r=1e-2):
    """
    変位と速度の同時推定のための2次元カルマンフィルター
    
    Parameters:
    displacement (array): 変位データ
    time (array): 時間データ
    process_variance_q (float): プロセスノイズの分散
    measurement_variance_r (float): 測定ノイズの分散
    
    Returns:
    filtered_displacement (array): フィルタリング後の変位データ
    filtered_velocity (array): フィルタリング後の速度データ
    """
    # pandasのSeriesをnumpy配列に変換
    if isinstance(displacement, pd.Series):
        displacement = displacement.values
    if isinstance(time, pd.Series):
        time = time.values
    
    # データの長さを取得
    n = len(displacement)
    
    # 状態ベクトル [位置, 速度]
    x = np.zeros((2, n))
    
    # 初期状態
    x[0, 0] = displacement[0]  # 初期位置
    if n > 1:
        x[1, 0] = (displacement[1] - displacement[0]) / (time[1] - time[0])  # 初期速度
    else:
        x[1, 0] = 0  # データが1点しかない場合
    
    # 状態遷移行列
    A = np.array([[1.0, 0.0], [0.0, 1.0]])
    
    # 測定行列 (位置のみ測定)
    H = np.array([[1.0, 0.0]])
    
    # プロセスノイズ共分散
    Q = np.array([[process_variance_q, 0], [0, process_variance_q]])
    
    # 測定ノイズ分散
    R = np.array([[measurement_variance_r]])
    
    # 推定誤差共分散の初期値
    P = np.array([[1.0, 0], [0, 1.0]])
    
    # カルマンフィルタリングの実行
    for i in range(1, n):
        dt = time[i] - time[i-1]  # 時間ステップ
        
        # 状態遷移行列の更新（時間ステップを考慮）
        A[0, 1] = dt
        
        # 予測ステップ
        x_pred = A @ x[:, i-1]
        P_pred = A @ P @ A.T + Q
        
        # 更新ステップ
        z = displacement[i]  # 測定値
        
        y = z - H @ x_pred  # 測定残差
        S = H @ P_pred @ H.T + R  # 残差共分散
        K = P_pred @ H.T @ np.linalg.inv(S)  # カルマンゲイン
        
        x[:, i] = x_pred + K @ y  # 状態の更新
        P = (np.eye(2) - K @ H) @ P_pred  # 共分散の更新
    
    # 結果の抽出
    filtered_displacement = x[0, :]
    filtered_velocity = x[1, :]
    
    return filtered_displacement, filtered_velocity

def detect_contact_after_peak(velocity_filtered, force_data, force_time, skip_index=0, min_force=0.05, max_time_seconds=4.0):
    """
    4秒以内の接触検出に制限したアルゴリズム
    
    Parameters:
    velocity_filtered (array): フィルタリング済みの速度データ
    force_data (array): フィルタリング済みの力データ
    force_time (array): 時間データ（秒単位）
    skip_index (int): 解析を開始するインデックス（初期データをスキップ）
    min_force (float): 力の最小閾値（接触判定の補助）
    max_time_seconds (float): 最大検索時間（秒）
    
    Returns:
    tuple: (contact_index, peak_index, threshold) - 接触開始点のインデックス、ピークのインデックス、使用した閾値
    """
    # データ検証
    if len(velocity_filtered) <= skip_index + 10:
        print("Warning: Data too short for analysis")
        return skip_index, skip_index, 0.0
    
    # 最大時間（4秒）以内のインデックスを見つける
    try:
        max_time_idx = np.where(force_time > max_time_seconds)[0][0]
    except (IndexError, ValueError):
        max_time_idx = len(force_time) - 1
    
    print(f"Limiting search to {max_time_seconds} seconds (index {max_time_idx})")
    
    # 検索範囲の設定（4秒以内かつデータ長の60%以内）
    data_length = len(velocity_filtered)
    search_end_60pct = min(data_length, int(data_length * 0.6))
    search_end = min(max_time_idx, search_end_60pct)
    
    # 有効な検索範囲を確保
    if search_end <= skip_index + 10:
        search_end = min(data_length, skip_index + 20)
    
    # スキップインデックス以降のデータで有意義なピークを見つける
    from scipy.signal import find_peaks
    
    try:
        # 移動平均でノイズを軽減
        window_size = min(5, max(1, (search_end - skip_index) // 4))  # データ長に応じて調整
        if skip_index >= search_end:
            velocity_smoothed = velocity_filtered[skip_index:min(skip_index+20, data_length)]
        else:
            velocity_smoothed = np.convolve(
                velocity_filtered[skip_index:search_end], 
                np.ones(window_size)/window_size, 
                mode='valid'
            )
        
        # データが空でないことを確認
        if len(velocity_smoothed) == 0:
            print("Warning: Empty velocity data after smoothing")
            return skip_index, skip_index, 0.0
        
        # 最小ピーク高さを動的に設定
        min_peak_height = max(2.0, np.percentile(velocity_smoothed, 75) * 0.5)
        
        # ピーク検出
        prominence_value = max(0.5, np.std(velocity_smoothed) * 0.5)  # データの変動に基づいて prominence を設定
        
        # 少なくとも1つのピークを検出する試み
        for attempt in range(3):
            peaks, peak_properties = find_peaks(
                velocity_smoothed, 
                height=min_peak_height / (attempt + 1),  # 徐々に基準を下げる
                distance=max(2, 10 // (attempt + 1)),  # 徐々に距離制約を緩める
                prominence=prominence_value / (attempt + 1)  # 徐々に突出度制約を緩める
            )
            
            if len(peaks) > 0:
                break
        
        # ピークが見つからない場合の対応
        if len(peaks) == 0:
            # 最大値の位置を代替ピークとして使用
            alt_peak_idx = np.argmax(velocity_smoothed)
            peaks = np.array([alt_peak_idx])
            print(f"No peaks found using find_peaks, using maximum value at index {alt_peak_idx + skip_index}")
    
    except Exception as e:
        print(f"Error during peak detection: {e}")
        # エラーが発生した場合、最大値位置をピークとして使用
        if skip_index < search_end:
            try:
                rel_max_idx = np.argmax(velocity_filtered[skip_index:search_end])
                max_idx = rel_max_idx + skip_index
                peaks = np.array([rel_max_idx])
                print(f"Using maximum velocity at index {max_idx} as fallback peak")
            except Exception as e2:
                print(f"Fallback peak detection failed: {e2}")
                return skip_index, skip_index, 0.0
        else:
            return skip_index, skip_index, 0.0
    
    # 最初のピークの実際のインデックスを計算
    # (mode='valid'のconvolveは (window_size - 1) / 2 のオフセットを生む)
    offset = (window_size - 1) // 2
    first_peak_index = skip_index + peaks[0] + offset
    
    # インデックス範囲チェック
    first_peak_index = min(first_peak_index, len(velocity_filtered) - 1)
    peak_velocity = velocity_filtered[first_peak_index]
    
    print(f"Selected peak at index {first_peak_index} with velocity {peak_velocity:.2f} (time: {force_time[first_peak_index]:.2f}s)")
    
    # 2. ピーク後の減速局面で接触を検出
    contact_found = False
    contact_index = first_peak_index
    
    # 速度閾値設定 (ピーク速度の40%)
    velocity_threshold = max(min_force, peak_velocity * 0.5)  # 最小閾値を設定
    
    try:
        # ピーク後の接触点探索（4秒以内に制限）
        for i in range(first_peak_index, min(search_end, len(velocity_filtered))):
            # 速度が閾値以下に減少し、力も一定以上の点を探す
            if (velocity_filtered[i] < velocity_threshold and force_data[i] > min_force):
                # 次の数ポイントも確認
                confirmed = True
                for j in range(i, min(i+3, len(velocity_filtered))):
                    if j < len(velocity_filtered) and velocity_filtered[j] > velocity_threshold:
                        confirmed = False
                        break
                
                if confirmed:
                    contact_index = i
                    contact_found = True
                    break
        
        # 接触点が見つからない場合は減速率で判定
        if not contact_found and first_peak_index < search_end - 5:
            max_decel_idx = first_peak_index
            max_decel_rate = 0
            
            for i in range(first_peak_index, min(search_end-5, len(velocity_filtered))):
                if velocity_filtered[i] <= 0:
                    continue
                
                future_idx = min(i+5, len(velocity_filtered)-1)
                decel_rate = (velocity_filtered[i] - velocity_filtered[future_idx]) / velocity_filtered[i]
                
                if decel_rate > max_decel_rate:
                    max_decel_rate = decel_rate
                    max_decel_idx = i
            
            contact_index = max_decel_idx
            print(f"Contact detected based on maximum deceleration at index {contact_index} (time: {force_time[contact_index]:.2f}s)")
    
    except Exception as e:
        print(f"Error during contact detection: {e}")
        # エラー時はピーク位置を接触点とみなす
        contact_index = first_peak_index
    
    print(f"Contact detected at index {contact_index} (time: {force_time[contact_index]:.2f}s) after velocity peak at index {first_peak_index} (time: {force_time[first_peak_index]:.2f}s)")
    return contact_index, first_peak_index, velocity_threshold

def calcurate_sttiffness(
                            parent_dir: str="",
                            force_file: str="", 
                            motion_file: str="", 
                            start_force=2, 
                            measurement_distance=7,
                            middle_plot: bool=False,
                            debug=False,
                            use_kalman=True  # カルマンフィルター使用フラグを追加
                        ):
    """剛性を算出する
    
    Args:
        start_force (float): 解析を始める際のフォースゲージの値
        measurement_distance (float): 解析を行う変位量
        middle_plot (bool, optional): 解析の中間グラフを保存するかどうか. Defaults to False.
        use_kalman (bool, optional): バターワースの代わりにカルマンフィルターを使用. Defaults to True.

    Returns:
        list: mean_stiffnes
        list: std_stiffnes
        list: all_stiffnes
    """
    # 結果を格納するリスト
    error_file = ""
    start_time = 0.0 * 1000 # sec * 1000
    stiffness_N_m = 0
    patern = 0
    try:
        # for f in glob(force_file):
        force_df = pd.read_csv(force_file, header=None, names=utils.headers)
        force_df_cut = force_df[force_df['timestamp'] >= start_time]
        
        force_time = force_df_cut['timestamp'] * 0.001  # ms から s に変換
        force_data = force_df_cut['Force']  # mN から N に変換
        
        # サンプリング周波数の計算
        fs = 1.0 / ((force_time.max() - force_time.min()) / len(force_data))
        print(f"Sampling frequency: {fs:.1f} Hz")

        force_time_reset = force_time.reset_index(drop=True)
        
        # カルマンフィルターまたはバターワースフィルターの適用
        if use_kalman:
            # 1次元カルマンフィルターで力データをフィルタリング
            # パラメータ調整: process_variance（小さいほど滑らか）, measurement_variance（大きいほど元データを信頼しない）
            force_data_reset = kalman_filter_1d(
                force_data.values, 
                process_variance=1e-5,  # 小さいほど滑らか
                measurement_variance=1e-2  # 大きいほどノイズを除去
            )
            print("Applied Kalman filter to force data")
        else:
            # バターワースフィルターを適用（従来のコード）
            cutoff = 2.0  # カットオフ周波数 (Hz)
            order = 4  # フィルターの次数
            filtered_force_data = butter_lowpass_filter(force_data, cutoff, fs, order)
            force_data_reset = filtered_force_data
            print("Applied Butterworth filter to force data")
        
        print(f"Filtered Force data length: {len(force_data_reset)}")
        print(f"Time data length {len(force_time_reset)}")
        print(force_data_reset[:10])

        # モーションキャプチャデータの読み込み
        patern = 1
        # for f in glob(motion_file):
        motion_df = pd.read_csv(motion_file, skiprows=6).dropna(how="all").rolling(
            window=11,
            center=True,  # ウィンドウの中心を基準に計算
            min_periods=1  # 端のデータも計算する
        ).mean()
        motion_df_reset = motion_df.reset_index(drop=True)
        motion_time = motion_df_reset['Time (Seconds)']
        # Position の X, Y, Z 列を取得し、数値型に変換
        position_x = motion_df_reset.iloc[:, -3]
        position_y = motion_df_reset.iloc[:, -2]
        position_z = motion_df_reset.iloc[:, -1]

        # 3次元変位の計算
        initial_x = position_x.iloc[0]
        initial_y = position_y.iloc[0]
        # initial_z = position_z.iloc[0]
        displacement_x = position_x - initial_x
        displacement_y = position_y - initial_y
        # displacement_z = position_z - initial_z
        # displacement_3d = np.sqrt(displacement_x**2 + displacement_y**2 + displacement_z**2)
        displacement_3d = np.sqrt(displacement_x**2 + displacement_y**2)

        # モーションキャプチャーデータを力センサーの時間に補間
        motion_interpolator = interp1d(motion_time, displacement_3d, kind='linear', bounds_error=False)
        displacement_3d_resampled = motion_interpolator(force_time_reset)
        
        threshold = force_data_reset.max() * 0.05
        print(f"threshold: {threshold}")
        if threshold < start_force:
            threshold = start_force
        print(f"start force: {start_force}")

        # NaNを除外
        displacement_3d_resampled_no_nan = np.nan_to_num(displacement_3d_resampled, nan=0.0)
        
        # カルマンフィルターまたはバターワースフィルターの適用（変位データ）
        if use_kalman:
            # カルマンフィルターを使用して変位と速度を同時に推定
            displacement_3d_filtered, velocity_filtered = kalman_filter_velocity_position(
                displacement_3d_resampled_no_nan, 
                force_time_reset,
                process_variance_q=1e-5,
                measurement_variance_r=1e-2
            )
            print("Applied Kalman filter to displacement and velocity data")
        else:
            # 従来のバターワースフィルターと速度計算
            cutoff = 2.0  # カットオフ周波数 (Hz)
            order = 4  # フィルターの次数
            displacement_3d_filtered = butter_lowpass_filter(displacement_3d_resampled_no_nan, cutoff, fs, order)
            # 変位の速度を計算
            velocity = calculate_velocity(displacement_3d_filtered, force_time_reset)
            # 速度データにもフィルタリングを適用してノイズを減らす
            velocity_filtered = butter_lowpass_filter(velocity, cutoff/2, fs, order)  # 速度はより低いカットオフ周波数
            print("Applied Butterworth filter to displacement and velocity data")

        # 速度閾値による接触検出
        initial_skip_ratio = 0.05  # 最初の5%のデータをスキップ
        skip_index = int(len(velocity_filtered) * initial_skip_ratio)

        # 速度の絶対値の移動平均を計算（プロット用）
        window_size = 15
        velocity_abs_smooth = np.abs(velocity_filtered)
        velocity_abs_ma = np.convolve(velocity_abs_smooth, np.ones(window_size)/window_size, mode='same')

        # ベースライン推定（プロット用）
        baseline_start_index = skip_index
        baseline_end_index = min(int(len(velocity_abs_ma) * 0.3), len(velocity_abs_ma) - 1)

        # 速度ピーク後の接触検出関数を呼び出し
        try:
            contact_index_velocity, detected_peak_index, velocity_threshold = detect_contact_after_peak(
                velocity_filtered, 
                force_data_reset,
                force_time_reset,  # 時間データを追加
                skip_index=skip_index,
                min_force=0.1,
                max_time_seconds=4.0  # 最大4秒に制限
            )
            
            # ピーク情報を保存
            peak_index = None
            peak_velocity = None
            if detected_peak_index < len(velocity_filtered):
                peak_index = detected_peak_index
                peak_velocity = velocity_filtered[peak_index]
            
            print(f"Contact detected at index {contact_index_velocity} (time: {force_time_reset[contact_index_velocity]:.2f}s)")
        except Exception as e:
            print(f"Error in contact detection: {e}")
            # エラー時のフォールバック
            contact_index_velocity = skip_index
            velocity_threshold = 0.0
            
        # 接触から測定距離のインデックスを見つける
        try:
            # 安全に five_displacement_index を見つける
            target_displacement = displacement_3d_filtered[contact_index_velocity] + measurement_distance
            displacement_after_contact = displacement_3d_filtered[contact_index_velocity:]
            indices_after_target = np.where(displacement_after_contact > target_displacement)[0]
            
            if len(indices_after_target) > 0:
                five_displacement_rel_idx = indices_after_target[0]
                five_displacement_index = contact_index_velocity + five_displacement_rel_idx
            else:
                # ターゲット変位に達するデータがない場合
                print("Warning: Could not find displacement index that reaches target displacement")
                five_displacement_index = min(len(displacement_3d_filtered) - 1, 
                                            contact_index_velocity + int(len(displacement_3d_filtered) * 0.2))
        except Exception as e:
            print(f"Error finding displacement index: {e}")
            # エラー時のフォールバック - データの20%を使用
            five_displacement_index = min(len(displacement_3d_filtered) - 1, 
                                        contact_index_velocity + int(len(displacement_3d_filtered) * 0.2))
        
        # 解析区間のデータを抽出
        force_analysis = force_data_reset[contact_index_velocity:five_displacement_index+1]
        displacement_analysis = displacement_3d_filtered[contact_index_velocity:five_displacement_index+1]

        # NaNを除去
        valid_indices = ~np.isnan(displacement_analysis)
        force_analysis = force_analysis[valid_indices]
        displacement_analysis = displacement_analysis[valid_indices]

        # 線形回帰
        slope, intercept, r_value, p_value, std_err = stats.linregress(displacement_analysis, force_analysis)
        # フィッティング曲線の計算
        fit_disp = displacement_analysis
        fit_force = slope * displacement_analysis + intercept
        fit_label = f'Linear Fit (Stiffness = {slope*1000:.0f} N/m, R² = {r_value**2:.3f})'
        stiffness_N_m = slope * 1000  # N/mm から N/m に変換
        
        # フィッティング結果を保存
        if stiffness_N_m < 0:
            raise ValueError("Stiffness is negative")
        
        # プロット
        if middle_plot:
            try:
                plot_middle_result(
                    parent_dir=parent_dir,
                    force_file=force_file,
                    deg=force_file.split("/")[-1].split("_")[1],
                    force_time=force_time_reset,
                    force_data=force_data_reset,
                    displacement_3d_resampled=displacement_3d_resampled,
                    displacement_3d_filtered=displacement_3d_filtered,
                    velocity_filtered=velocity_filtered if debug else None,
                    velocity_abs_ma=velocity_abs_ma if debug else None,
                    velocity_threshold=velocity_threshold if debug else None,
                    skip_index=skip_index if debug else None,
                    baseline_start_index=baseline_start_index if debug else None,
                    baseline_end_index=baseline_end_index if debug else None,
                    contact_index=contact_index_velocity,
                    five_displacement_index=five_displacement_index,
                    displacement_analysis=displacement_analysis,
                    force_analysis=force_analysis,
                    fit_disp=fit_disp,
                    fit_force=fit_force,
                    fit_label=fit_label,
                    ID=force_file.split("/")[-1].split("_")[-1].split(".")[0],
                    peak_index=peak_index,
                    peak_velocity=peak_velocity,
                    debug=debug
                )
            except Exception as e:
                print(f"Error in plotting: {e}")
                
    except FileNotFoundError:
        if (patern == 0):
            print(f'Warning: File {force_file} not found')
        else:
            print(f'Warning: File {motion_file} not found')
    except Exception as e:
        print(f"Error {e}")
        error_file = force_file
        
    return stiffness_N_m, error_file

def analyze_360deg(
            parent_dir: str="",
            force_dir: str="", 
            motion_dir: str="",
            start_force=2, 
            measurement_distance=7, 
            middle_plot: bool=False,
            use_kalman=True):  # カルマンフィルター使用オプションを追加
    """360度の剛性を算出する

    Args:
        start_force (float): 解析を始める際のフォースゲージの値
        measurement_distance (float): 解析を行う変位量
        middle_plot (bool, optional): 解析の中間グラフを保存するかどうか. Defaults to False.
        use_kalman (bool, optional): バターワースの代わりにカルマンフィルターを使用. Defaults to True.

    Returns:
        list: mean_stiffnes
        list: std_stiffnes
        list: all_stiffnes
    """
    # 結果を格納するリスト
    mean_stiffness = []
    std_stiffnesses = []
    all_stiffnes = []
    error_files = []
    
    # 使用するフィルターの表示
    filter_type = "Kalman filter" if use_kalman else "Butterworth filter"
    print(f"Using {filter_type} for analysis")
    
    for deg in utils.angles:
        stiffnesses = []
        for i in range(1, 9):
            if force_dir == "":
                force_file = f'{parent_dir}/{utils.type_name}/{utils.force_dir_name}/push_{deg}_deg_{i}.csv'
            else:
                force_file = f'./{force_dir}/push_{deg}_deg_{i}.csv'
            fill_num = str(i).zfill(3)
            if motion_dir == "":
                motion_file = f'{parent_dir}/{utils.type_name}/{utils.force_dir_name}/Push_{deg}_deg_{fill_num}.csv'
            else:
                motion_file = f'./{motion_dir}/Push_{deg}_deg_{fill_num}.csv'
            
            # 剛性計算にカルマンフィルターオプションを伝達
            stiffness_N_m, error_file = calcurate_sttiffness(
                parent_dir,
                force_file, 
                motion_file, 
                start_force, 
                measurement_distance, 
                middle_plot, 
                debug=False,
                use_kalman=use_kalman  # カルマンフィルターオプションを追加
            )

            if stiffness_N_m > 0:
                stiffnesses.append(stiffness_N_m)
                all_stiffnes.append(stiffness_N_m)
            if error_file != "":
                error_files.append(error_file)
            if middle_plot:
                print(f"push_{deg}_degree_{i} is done")
        
        if len(stiffnesses) > 0:
            mean_stiffness.append(np.mean(stiffnesses))
            std_stiffnesses.append(np.std(stiffnesses))
        else:
            print(f"Warning: No valid stiffness values for {deg} degrees")
            mean_stiffness.append(0)
            std_stiffnesses.append(0)
            
    return mean_stiffness, std_stiffnesses, all_stiffnes, error_files

# plot
def plot_middle_result(
        parent_dir,
        force_file,
        deg, 
        force_time, 
        force_data, 
        displacement_3d_resampled,
        displacement_3d_filtered=None,  
        velocity_filtered=None,         
        velocity_abs_ma=None,           
        velocity_threshold=None,        
        skip_index=None,                
        baseline_start_index=None,      
        baseline_end_index=None,        
        contact_index=None, 
        five_displacement_index=None, 
        displacement_analysis=None, 
        force_analysis=None, 
        fit_disp=None, 
        fit_force=None, 
        fit_label=None,
        ID=None,
        peak_index=None,  # 追加: 速度ピークのインデックス
        peak_velocity=None,  # 追加: ピーク時の速度
        debug=False):
    
    if debug and velocity_filtered is not None:
        # デバッグモード: 3つのグラフを表示
        fig = plt.figure(figsize=(15, 12))
        plt.rcParams.update({'font.size': 18})
        gs = fig.add_gridspec(2, 2)
        
        # 力と変位の時間変化
        ax1 = fig.add_subplot(gs[0, 0])
        ax1_force = ax1
        ax1_disp = ax1.twinx()
        ax1_force.plot(force_time, force_data, 'b-', label='Filtered Force (N)', fontsize=18)
        ax1_disp.plot(force_time, displacement_3d_filtered, 'r-', label='Filtered Displacement (mm)', fontsize=18)
        ax1_force.axvline(x=force_time[contact_index], color='g', linestyle='--', label='Contact Point', fontsize=18)
        ax1_force.axvline(x=force_time[five_displacement_index], color='k', linestyle='--', label='End Displacement', fontsize=18)
        ax1_force.set_xlabel('Time [s]', fontsize=18)
        ax1_force.set_ylabel('Force [N]', color='b', fontsize=18)
        ax1_force.tick_params(axis='y', labelcolor='b')
        # ax1.set_xlabel('Time [s]')
        # ax1.set_ylabel('Force [N] / Displacement [mm]')
        ax1_disp.set_ylabel('Displacement [mm]', color='r', fontsize=18)
        ax1_disp.tick_params(axis='y', labelcolor='r')
        lines_1 = ax1_force.get_lines() + ax1_disp.get_lines()
        labels_1 = [l.get_label() for l in lines_1]
        ax1.legend(lines_1, labels_1, loc='upper left')
        ax1.grid(True)
        
        # 速度と接触判定の表示
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(force_time, velocity_filtered, 'g-', label='Velocity (mm/s)', alpha=0.6)
        ax2.plot(force_time, velocity_abs_ma, 'b-', label='Abs Velocity (Moving Avg)')
        
        # ピーク検出と閾値表示
        if peak_index is not None and peak_index < len(force_time):
            ax2.plot(force_time[peak_index], velocity_filtered[peak_index], 'ro', 
                    markersize=8, label='Velocity Peak')
            
            # ピーク速度の40%を閾値として表示
            if peak_velocity is not None:
                peak_threshold = peak_velocity * 0.5
                ax2.axhline(y=peak_threshold, color='orange', linestyle='--', 
                           label=f'Peak Threshold ({peak_threshold:.1f} mm/s)')
        
        # 速度閾値の表示
        if velocity_threshold is not None:
            ax2.axhline(y=velocity_threshold, color='r', linestyle='--', 
                       label=f'Velocity Threshold ({velocity_threshold:.1f} mm/s)')
        
        # 接触点表示
        try:
            if contact_index is not None and contact_index < len(force_time):
                ax2.axvline(x=force_time[contact_index], color='g', linestyle='--', label='Contact Point')
        except Exception as e:
            print(f"Warning: Error plotting contact point: {e}")

        # スキップ範囲表示
        try:
            if skip_index is not None and skip_index < len(force_time):
                ax2.axvline(x=force_time[skip_index], color='m', linestyle=':', label='Skip Boundary')
        except Exception as e:
            print(f"Warning: Error plotting skip boundary: {e}")

        # ベースライン範囲表示
        try:
            if (baseline_start_index is not None and baseline_end_index is not None and
                baseline_start_index < len(force_time) and baseline_end_index < len(force_time)):
                ax2.axvline(x=force_time[baseline_start_index], color='c', linestyle=':', alpha=0.7)
                ax2.axvline(x=force_time[baseline_end_index], color='c', linestyle=':', alpha=0.7, label='Baseline Range')
        except Exception as e:
            print(f"Warning: Error plotting baseline range: {e}")

        ax2.set_xlabel('Time [s]')
        ax2.set_ylabel('Velocity [mm/s]')
        ax2.legend()
        ax2.set_title('Velocity vs. Time with Contact Detection')
        ax2.grid(True)
        
        # 力-変位曲線とフィッティング（解析区間のみ）- 大きく表示
        ax3 = fig.add_subplot(gs[1, :])  # 下段全体を使用
        ax3.scatter(displacement_analysis, force_analysis, c='b', label='Analysis Data', alpha=0.5)
        ax3.plot(fit_disp, fit_force, 'r-', linewidth=2, label=fit_label)
        ax3.set_xlabel('Displacement [mm]', fontsize=18)
        ax3.set_ylabel('Force [N]', fontsize=18)
        ax3.grid(True)
        ax3.legend(fontsize=18)
        ax3.set_title('Force vs. Displacement (Analysis Region) - Stiffness Calculation', fontsize=18)

    else:
        # 通常モード: 2つのグラフを表示
        fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        # plt.rcParams.update({'font.size': 16})

        # 力と変位の時間変化（2軸）
        ax1_force = ax1
        ax1_disp = ax1.twinx()

        # 力のプロット（左軸）
        ax1_force.plot(force_time, force_data, 'b-', label='Force')
        ax1_force.axhline(y=force_data[contact_index], color='g', linestyle='--', label=f'Contact Threshold {round(force_data[contact_index],3)}')
        ax1_force.set_xlabel('Time [s]', fontdict={'size': 18})
        ax1_force.set_ylabel('Force [N]', color='b', fontdict={'size': 18})
        ax1_force.tick_params(axis='y', labelcolor='b')

        # 変位のプロット（右軸）
        ax1_disp.plot(force_time, displacement_3d_resampled, 'r-', label='Displacement')
        ax1_disp.set_ylabel('Displacement [mm]', color='r', fontdict={'size': 18})
        ax1_disp.tick_params(axis='y', labelcolor='r')

        # 接触開始と最大力の時点を表示
        ax1_force.axvline(x=force_time[contact_index], color='g', linestyle='--', label='Contact Start')
        # ax1_force.axvline(x=force_time[max_force_index], color='k', linestyle='--')
        ax1_force.axvline(x=force_time[five_displacement_index], color='k', linestyle='--', label='End Displacement')

        # 凡例の結合
        lines_1 = ax1_force.get_lines() + ax1_disp.get_lines()
        labels_1 = [l.get_label() for l in lines_1]
        ax1.legend(lines_1, labels_1, loc='upper left')
        ax1.grid(True)

        # 力-変位曲線とフィッティング（解析区間のみ）
        ax2.scatter(displacement_analysis, force_analysis, c='b', label='Analysis', alpha=0.5)
        ax2.plot(fit_disp, fit_force, 'r-', label=fit_label)
        ax2.set_xlabel('Displacement [mm]')
        ax2.set_ylabel('Force [N]')
        ax2.grid(True)
        ax2.legend()
    
    parent_txt=parent_dir.split("/")[-3] + "_" + parent_dir.split("/")[-2]
    plt.tight_layout()
    force_file_name = force_file.split("/")[-1].split(".")[0]
    # グラフの保存
    try:
        if (not os.path.isdir(f'./pngs/force_distance/{parent_txt}/{utils.type_name}')):
            print("PNG directory not found")
            os.makedirs(f'./pngs/force_distance/{parent_txt}/{utils.type_name}')
            print(f"PNG directory created {parent_txt}")
        plt.savefig(f'./pngs/force_distance/{parent_txt}/{utils.type_name}/{force_file_name}{"_debug" if debug else ""}.png', dpi=300, bbox_inches='tight')
        print(f'png saved: ./pngs/force_distance/{parent_txt}/{utils.type_name}/{force_file_name}{"_debug" if debug else ""}.png')
        plt.clf()
        plt.close()
    except Exception as e:
        print(f"Error: {e}")
        plt.clf()
        plt.close()