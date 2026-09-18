import pandas as pd
import matplotlib.pyplot as plt

# CSVファイルを読み込む
folder = "."
df = pd.read_csv(folder + "/" + 'random.csv')

# 'Finish'行を見つけて、データをトライアルごとに分割
trial_dfs = []
current_trial = []

for _, row in df.iterrows():
    if 'Finish' in row.values:
        if current_trial:
            trial_dfs.append(pd.DataFrame(current_trial))
            current_trial = []
    else:
        current_trial.append(row)

if current_trial:
    trial_dfs.append(pd.DataFrame(current_trial))

# 各トライアルについてグラフを作成
for trial_num, trial_df in enumerate(trial_dfs):
    fig, axs = plt.subplots(11, 2, figsize=(20, 50))
    fig.suptitle(f'Trial {trial_num + 1}: Time-(Current, Position) Graphs', fontsize=16)

    for i in range(22):
        row = i // 2
        col = i % 2
        
        cur_col = f'cur_{i+1}'
        pos_col = f'pos_{i+1}'
        
        ax1 = axs[row, col]
        ax2 = ax1.twinx()
        pos_col = trial_df[pos_col] * 0.088
        
        # 電流のプロット（左軸）
        line1, = ax1.plot(trial_df['timestamp'], trial_df[cur_col], color='blue', label='Current [mA]')
        ax1.set_xlabel('Timestamp')
        ax1.set_ylabel('Current', color='blue')
        ax1.set_ylim(-100, 600)
        ax1.tick_params(axis='y', labelcolor='blue')
        
        # 位置のプロット（右軸）
        line2, = ax2.plot(trial_df['timestamp'], pos_col, color='red', label='Position [°]')
        ax2.set_ylabel('Position', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        ax1.set_title(f'Motor {i+1}')
        
        # 凡例を追加
        lines = [line1, line2]
        ax1.legend(lines, [l.get_label() for l in lines], loc='upper left')
        
    plt.tight_layout()
    plt.savefig(f'{folder}/trial_{trial_num+1}_graphs.png')
    plt.close()

print("全てのグラフが生成されました。")