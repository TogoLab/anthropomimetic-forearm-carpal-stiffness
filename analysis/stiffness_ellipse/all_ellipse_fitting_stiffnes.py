import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
import lib.utils as utils
from lib.analyze import analyze_360deg
from lib import fitting
from scipy.optimize import minimize
import japanize_matplotlib  # 日本語化matplotlib
import datetime
# プロット
fig, ax = plt.subplots(figsize=(10, 10))
# data_dir = "./datas/normal/0202/"
# data_dir = "./datas/fixed_bone/0220/"
data_dir = "./datas/ellipse_carpal/0223/"
low = "low_contraction"
high = "high_contraction"
super_high = "super_high_contraction"
finger = "finger_contraction"
label = [
    "Relax", 
    "Wrist Muscle", 
    "Finger Muscle", 
    "Wrist and Finger Muscles"
    ]
# param_df = pd.read_csv(f"results/ellipse/param/data_dir.split('/')[2]+"_" + data_dir.split('/')[3]}_20250226.csv", index_col="types")
# start_forces = param_df.loc["start_force"].values
start_forces = np.array([0.15, 0.2, 0.6, 0.7])

measurement_distance = np.array([3, 3, 3, 3])
cnt = 0
datasets = np.array([
            low, 
            high, 
            finger, 
            super_high
            ])
analyzed_datas = np.array(utils.angles)
ellpse_rate = []
phis_min = []
phis_max = []
# params = np.vstack((datasets, start_forces))
# params = np.vstack((params, measurement_distance))
# print(params)
# params = np.hstack((np.array([["types"], ["start_force"], ["measurement_distance"]]), params))
# timestamp = datetime.datetime.now().strftime("%Y%m%d")
# # パラメータの保存
# np.savetxt(f"results/ellipse/param/{data_dir.split('/')[2]+'_' + data_dir.split('/')[3]}_{timestamp}.csv", params, delimiter=',', fmt='%s')
error_files = []
areas = []
min_distance_points = []
max_distance_points = []
for i, dataset in enumerate(datasets):
    if "low" in dataset:
        start_force = start_forces[0]
        print(f"sart_force = {start_force}")
    elif "finger" in dataset:
        start_force = start_forces[2]
        print(f"sart_force = {start_force}")
    elif "super_high" in dataset:
        start_force = start_forces[3]
        print(f"sart_force = {start_force}")
    else:
        start_force = start_forces[1]
        print(f"sart_force = {start_force}")

    utils.type_name = dataset
    utils.force_dir_name = data_dir + dataset + "/force_gage"
    utils.motion_dir_name = data_dir + dataset + "/motion_capture"
    mean_stiffness, std_stiffnesses, _, files = analyze_360deg(
                                                    parent_dir=f"{data_dir}",
                                                    force_dir=f"{utils.force_dir_name}",
                                                    motion_dir=f"{utils.motion_dir_name}", 
                                                    start_force=start_force, 
                                                    measurement_distance=measurement_distance[i],
                                                    middle_plot=True,
                                                    use_kalman=True
                                                )
    result_data = np.array([])
    # for i in range(len(mean_stiffness)):
    #     result_data = np.append(result_data, str(round(mean_stiffness[i], 3)) + "±" + str(round(std_stiffnesses[i], 3)))
    analyzed_datas = np.vstack((
        analyzed_datas, 
        # result_data
        np.vstack((
            mean_stiffness, std_stiffnesses
        ))
    ))
    # 各角度の平均値と標準偏差の棒グラフを作成して保存
    fig_bar, ax_bar = plt.subplots(figsize=(10, 10))
    ax_bar.bar(utils.angles, mean_stiffness, width=10, color="gray", yerr=std_stiffnesses, capsize=5)
    ax_bar.set_title(f"Mean and Std of {utils.type_name}")
    ax_bar.set_xlabel("Angle [degree]")
    ax_bar.set_ylabel("Stiffness [N/m]")
    ax_bar.set_xticks(utils.angles)
    ax_bar.set_xticklabels(utils.angles)
    ax_bar.grid()
    # ax_bar.legend()
    plt.savefig(f"results/ellipse/mean_and_std/{data_dir.split('/')[2]+'_'+data_dir.split('/')[3]}_{dataset}.png", dpi=300, bbox_inches='tight')
    fig_bar.clf()
    plt.close(fig_bar)
    
    # エラーファイルの格納
    if len(files) != 0:
        error_files.append(files)
    # ラジアンに変換
    theta = np.radians(utils.angles)
    r = np.array(mean_stiffness)
    x = r * np.cos(theta)
    y = r * np.sin(theta)

    # メインコードの最後で使用
    a, b, h, k, phi  = fitting.fit_cartesian(x, y)
    if a >= b:
        ellpse_rate.append(1 - b/a)
    else:
        ellpse_rate.append(1 - a/b)

    # 楕円の面積を計算（π × a × b）
    area = np.pi * a * b
    areas.append(area)

    # # 各点をプロット
    # ax.plot(x, y, 'o',
    #     # label=f'Data {utils.type_name}'
    #     )
        
    # フィッティングした楕円をプロット
    t = np.linspace(0, 2*np.pi, 10000)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    x_ellipse = h + a*np.cos(t)*cos_phi - b*np.sin(t)*sin_phi
    y_ellipse = k + a*np.cos(t)*sin_phi + b*np.sin(t)*cos_phi
    # 最小距離点を計算
    norm = np.sqrt(x_ellipse**2 + y_ellipse**2)
    point = np.array([x_ellipse, y_ellipse])
    min_point = [x_ellipse[np.argmin(norm)], y_ellipse[np.argmin(norm)]]
    max_point = [x_ellipse[np.argmax(norm)], y_ellipse[np.argmax(norm)]]
    min_distance_points.append(min_point)
    max_distance_points.append(max_point)
    # 最小距離点とx軸のなす角度を計算
    min_distance_angle = np.arctan2(min_point[1], min_point[0])
    max_distance_angle = np.arctan2(max_point[1], max_point[0])
    min_angle_deg = np.degrees(min_distance_angle)
    max_angle_deg = np.degrees(max_distance_angle)

    # 角度を0~360度に変換
    if max_angle_deg < 0:
        max_angle_deg += 360
    if min_angle_deg < 0:
        min_angle_deg += 360
    phis_max.append(max_angle_deg)
    phis_min.append(min_angle_deg)
    # color = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
    color = ['black', 'black', 'b', 'c', 'm', 'y', 'k']
    linestyle = ['-', '--', '-', '-']
    ax.plot(x_ellipse, y_ellipse, 
            linestyle=linestyle[cnt], 
            # linestyle='-',
            linewidth=5,
            color=color[cnt],
            # label=f'Fitted Ellipse {utils.type_name}'
            label=f'{label[cnt]}'
            )
    # ax.plot([0,max_point[0]], [0,max_point[1]], '.--', color=color[cnt])
    cnt += 1

    # # 長軸と短軸を表示
    # major_x = [h + a*cos_phi, h - a*cos_phi]
    # major_y = [k + a*sin_phi, k - a*sin_phi]
    # ax.plot(major_x, major_y, '--')
    
    # minor_x = [h - b*sin_phi, h + b*sin_phi]
    # minor_y = [k + b*cos_phi, k - b*cos_phi]
    # ax.plot(minor_x, minor_y, '--')

    # 中心点をプロット
    # ax.plot(h, k, '+', markersize=10, label=f'Center of {utils.type_name}')
    

# 解析結果の保存
# analyzed_datasをpandasのデータフレームに変換し，行ラベルを付与
# 行ラベルは平均値と標準偏差を４つずつ交互に並べる
index_labels = ["angles", "mean", "std", "mean", "std", "mean", "std", "mean", "std"]

# analyzed_datasの形状を確認
print(f"Shape of analyzed_datas: {analyzed_datas.shape}")

# ellpse_rateとphisをanalyzed_datasの列数に合わせて拡張
ellpse_rate_padded = np.pad(ellpse_rate, (0, analyzed_datas.shape[1] - len(ellpse_rate)), constant_values=np.nan)
phis_padded_min = np.pad(phis_min, (0, analyzed_datas.shape[1] - len(phis_min)), constant_values=np.nan)
phis_padded_max = np.pad(phis_max, (0, analyzed_datas.shape[1] - len(phis_max)), constant_values=np.nan)
areas_padded = np.pad(areas, (0, analyzed_datas.shape[1] - len(areas)), constant_values=np.nan)

# 配列を結合
analyzed_datas = np.vstack((
    analyzed_datas,
    ellpse_rate_padded,  # 楕円率を追加
    phis_padded_min,          # 最小角度を追加
    phis_padded_max,          # 最小角度を追加
    areas_padded          # 面積を追加
))

# インデックスラベルを更新
index_labels.extend(["ellipse_rate", "phis_min", "phis_max", "area"])

# データフレームを作成
# analyzed_datas_df = pd.DataFrame(analyzed_datas, index=index_labels)

# データフレームをCSVファイルに保存
# timestamp = datetime.datetime.now().strftime("%Y%m%d")
# output_path = f"results/ellipse/mean_and_std/{data_dir.split('/')[2] + '_' + data_dir.split('/')[3]}_{timestamp}.csv"
# analyzed_datas_df.to_csv(output_path, index=True, header=False)
# np.savetxt(f"results/ellipse/mean_and_std/{data_dir.split('/')[2]+"_"+data_dir.split('/')[3]}.csv", analyzed_datas, delimiter=',', fmt='%s')

print(f"エラーファイル: {error_files}")
# エラーファイルをテキストファイルに保存
with open(f"results/ellipse/param/{data_dir.split('/')[2]+'_'+data_dir.split('/')[3]}_error_files.txt", 'w') as f:
    for error_file in error_files:
        f.write(f"{error_file}\n")

print(f"楕円率: {ellpse_rate}")
# print(f"角度の平均: {phis.mean()}，角度の標準偏差: {phis.std()}")
# plt.rcParams["font.family"] = "DejaVu Serif"   # 使用するフォント
# plt.rcParams['font.family'] = 'Times New Roman' # Fonts
plt.rcParams["font.size"] = 22                # 文字の大きさ
# 軸の範囲を設定
margin = max(a, b) * 1
# ax.set_xlim(h - a - margin, h + a + margin)
# ax.set_ylim(k - b - margin, k + b + margin)
ax.set_xlim(-600, 600)
ax.set_ylim(-600, 600)

# グリッドと軸の設定
ax.grid(True)
ax.set_aspect('equal')

ax.set_xlabel('Palmar - Dorsal axis stiffness [N/m]', fontdict={'size': 24})
ax.set_ylabel('Radius - Ulnar axis stiffness [N/m]', fontdict={'size': 24})
plt.tick_params(labelsize = 14)   # メモリの数字のフォントサイズを設定

ax.legend()

plt.tight_layout()
plt.savefig(f'results/ellipse/ellipse_cartesian_{data_dir.split("/")[2]+"_"+data_dir.split("/")[3]}.png', dpi=300, bbox_inches='tight')
plt.savefig(f'results/ellipse/ellipse_cartesian_{data_dir.split("/")[2]+"_"+data_dir.split("/")[3]}.svg', 
            format='svg', 
            dpi=300, 
            bbox_inches='tight', 
            transparent=True
            )
plt.ion()
plt.show(block=True)
plt.ioff()
