import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

def read_csv(file_path):
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = [list(map(float, row)) for row in reader]
    return header, np.array(data)

def interpolate_data(data, num_points):
    num_rows, num_cols = data.shape
    
    # x軸の値を生成（各行のインデックス）
    x = np.arange(num_rows)
    x_new = np.linspace(0, num_rows - 1, num_points)
    
    interpolated_data = []
    for col in range(num_cols):
        y = data[:, col]
        cs = CubicSpline(x, y)
        y_new = cs(x_new)
        interpolated_data.append(y_new)
    
    return np.array(interpolated_data).T

def write_csv(file_path, header, data):
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in data:
            writer.writerow(row)

def plot_data(header, original_data, interpolated_data, output_file):
    plt.figure(figsize=(15, 10))
    
    x_original = np.arange(len(original_data))
    x_interpolated = np.linspace(0, len(original_data) - 1, len(interpolated_data))
    
    for i in range(len(header)):
        plt.plot(x_original, original_data[:, i], 'o', label=f'Original {header[i]}')
        plt.plot(x_interpolated, interpolated_data[:, i], '-', label=f'Interpolated {header[i]}')
    
    plt.xlabel('Row Index')
    plt.ylabel('Values')
    plt.title('Original vs Interpolated Data')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def main():
    input_file = 'input.csv'
    output_csv = 'output_interpolated.csv'
    output_graph = 'output_graph_interpolated.png'
    num_points = 100  # 補間後の総ポイント数

    header, data = read_csv(input_file)
    interpolated_data = interpolate_data(data, num_points)
    
    # 補間されたx軸の値を生成
    x_interpolated = np.linspace(data[0, 0], data[-1, 0], num_points)
    interpolated_data = np.column_stack((x_interpolated, interpolated_data[:, 1:]))
    
    write_csv(output_csv, header, interpolated_data)
    plot_data(header, data, interpolated_data, output_graph)

    print(f"補間されたデータが {output_csv} に書き込まれました。")
    print(f"グラフが {output_graph} として保存されました。")

if __name__ == "__main__":
    main()