import numpy as np
from numpy import ndarray
from scipy.optimize import minimize
import matplotlib.pyplot as plt
    
def _distance_to_ellipse(params, points):
    """
    点群から楕円までの距離の二乗和を計算
    """
    a, b, h, k, phi = params
    x = points[:, 0]
    y = points[:, 1]
    
    # 中心を原点に移動
    xc = x - h
    yc = y - k
    
    # 回転
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    xr = xc * cos_phi + yc * sin_phi
    yr = -xc * sin_phi + yc * cos_phi
    
    # 楕円からの距離を計算
    distance = ((xr/a)**2 + (yr/b)**2 - 1)**2
    return np.sum(distance)


def fit_polar(theta, r):
    # 極座標から直交座標への変換
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    
    # データ行列の作成
    D = np.column_stack([x**2, x*y, y**2])
    
    # 最小二乗法でフィッティング
    u, s, vh = np.linalg.svd(D)
    
    # 最小の特異値に対応する解を取得
    a, b, c = vh[-1]
    
    # 楕円のパラメータを計算
    # 中心は原点 (0,0) を仮定
    if abs(b) < 1e-10:  # bが非常に小さい場合
        phi = 0
    else:
        phi = 0.5 * np.arctan2(b, (a - c))
    
    # 回転した楕円の半径を計算
    ct = np.cos(phi)
    st = np.sin(phi)
    ap = a * ct**2 + b * ct * st + c * st**2
    cp = a * st**2 - b * ct * st + c * ct**2
    
    # 半径の計算
    scale = np.mean(r)  # データの平均値でスケーリング
    major_axis = scale / np.sqrt(min(abs(ap), abs(cp)))
    minor_axis = scale / np.sqrt(max(abs(ap), abs(cp)))
    
    return major_axis, minor_axis, phi

def fit_cartesian(x: ndarray, y: ndarray) -> tuple[float, float, float, float, float]:
    """直交座標系で点群を楕円近似する

    Args:
        x (Numpy Array): x軸のデータ列
        y (Numpy Array): y軸のデータ列

    Returns:
        float: a, b, h, k, phi
    楕円の式: x = h + a*cos(t)*cos(phi) - b*sin(t)*sin(phi),
              y = k + a*cos(t)*sin(phi) + b*sin(t)*cos(phi)
    """
    points = np.column_stack((x, y))
    
    # データの特性から初期値を推定
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    x_range = np.max(x) - np.min(x)
    y_range = np.max(y) - np.min(y)
    
    # 初期値の設定
    initial_guess = [
        x_range / 2,  # a
        y_range / 2,  # b
        x_mean,       # h
        y_mean,       # k
        0.0           # phi
    ]
    
    # 境界条件
    bounds = [
        (0, x_range),           # a
        (0, y_range),           # b
        # (x_mean - x_range / 2, x_mean + x_range / 2),  # h
        # (y_mean - y_range / 2, y_mean + y_range / 2),  # k
        (x_mean, x_mean),  # h
        (y_mean, y_mean),  # k
        (-np.pi / 2, np.pi / 2)  # phi
    ]
    
    # 最適化
    result = minimize(
        _distance_to_ellipse,
        initial_guess,
        args=(points,),
        bounds=bounds,
        method='L-BFGS-B',
        options={'maxiter': 1000}
    )
    
    if result.success:
        a, b, h, k, phi = result.x
        return a, b, h, k, phi
    else:
        print("Optimization failed:", result.message)
        return None
    
if __name__ == "__main__":
    import utils
    from analyze import analyze
    mean_stiffness, std_stiffnesses, _ = analyze(
        start_force=utils.START_FORCE,
        measurement_distance=7,
        middle_plot=False)
    """
    デカルト座標系での楕円フィッティングとプロット
    """
    # 極座標からデカルト座標への変換
    r = np.array(mean_stiffness)
    theta = np.radians(utils.angles)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    r = np.array(mean_stiffness)

    a, b, h, k, phi = fit_cartesian(x, y)

    fig, ax = plt.subplots(figsize=(10, 10))

    ax.plot(x, y, 'o',
        label=f'Data {utils.type_name}')

    # フィッティングした楕円をプロット
    t = np.linspace(0, 2*np.pi, 1000)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    x_ellipse = h + a*np.cos(t)*cos_phi - b*np.sin(t)*sin_phi
    y_ellipse = k + a*np.cos(t)*sin_phi + b*np.sin(t)*cos_phi
    ax.plot(x_ellipse, y_ellipse, '-', label=f'Fitted Ellipse {utils.type_name}')

    # 中心点をプロット
    ax.plot(h, k, '+', markersize=10, label=f'Center of {utils.type_name}')

    # # 長軸と短軸を表示
    # major_x = [h + a*cos_phi, h - a*cos_phi]
    # major_y = [k + a*sin_phi, k - a*sin_phi]
    # ax.plot(major_x, major_y, 'g--', label='Major Axis')

    # minor_x = [h - b*sin_phi, h + b*sin_phi]
    # minor_y = [k + b*cos_phi, k - b*cos_phi]
    # ax.plot(minor_x, minor_y, 'm--', label='Minor Axis')

    # グリッドと軸の設定
    ax.grid(True)
    ax.set_aspect('equal')

    # 軸の範囲を設定
    margin = max(a, b) * 1
    ax.set_xlim(h - a - margin, h + a + margin)
    ax.set_ylim(k - b - margin, k + b + margin)

    ax.set_xlabel('Palmar - Dorsal axis stiffness [N/m]')
    ax.set_ylabel('Radius - Ulnar axis stiffness [N/m]')
    ax.legend()

    ax2 = fig.add_subplot(111, projection='polar')
    ax2.plot(np.append(theta, theta[0]), 
        np.append(mean_stiffness, mean_stiffness[0]), 
        'o', linewidth=2,
        label=f'Mean Stiffnes: {mean_stiffness}')
    a, b, rot_angle = fit_polar(theta, mean_stiffness)

    t = np.linspace(0, 2*np.pi, 100)
    fitted_points = []

    for angle in t:
        # 楕円のパラメトリック方程式
        x = a * np.cos(angle)
        y = b * np.sin(angle)
        
        # 回転変換
        x_rot = x * np.cos(rot_angle) - y * np.sin(rot_angle)
        y_rot = x * np.sin(rot_angle) + y * np.cos(rot_angle)
        
        # 極座標に変換
        r = np.sqrt(x_rot**2 + y_rot**2)
        theta = np.arctan2(y_rot, x_rot)
        
        fitted_points.append((theta, r))

    # ソートして描画
    fitted_points.sort(key=lambda x: x[0])
    fitted_theta, fitted_r = zip(*fitted_points)
    ax2.plot(fitted_theta, fitted_r, '--', label=f'Fitted Ellipse least: {utils.type_name}', linewidth=2)
    # プロットの装飾
    ax2.set_title('Stiffness by Angle with Standard Deviation')
    # 角度の目盛りを設定（別の方法）
    ax2.set_thetagrids(utils.angles, labels=[f'{angle}°' for angle in utils.angles])
    ax2.grid(True)
    ax2.legend()


    plt.tight_layout()
    plt.savefig(f'results/ellipse/all_ellipse_cartesian.png', dpi=300, bbox_inches='tight')
    plt.show()
