"""
手首剛性解析モジュール
ForceGageの力と変位から回帰直線を求めて手首剛性を計算
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import japanize_matplotlib
plt.rcParams['axes.axisbelow'] = True
def calculate_wrist_stiffness(force_data, displacement_data, subject_id="", condition=""):
    """
    解析区間での力と変位から手首剛性を計算
    
    Parameters:
    -----------
    force_data : array-like
        解析区間の力データ (N)
    displacement_data : array-like  
        解析区間の変位データ (mm)
    subject_id : str
        被験者ID
    condition : str
        実験条件
        
    Returns:
    --------
    dict : 手首剛性解析結果
    """
    try:
        if len(force_data) != len(displacement_data) or len(force_data) < 3:
            print(f"    {subject_id}: データ不足 (長さ: {len(force_data)})")
            return None
        
        # 有効なデータ点のみを使用
        valid_mask = np.isfinite(force_data) & np.isfinite(displacement_data)
        
        if np.sum(valid_mask) < 3:
            print(f"    {subject_id}: 有効データ不足")
            return None
        
        force_valid = force_data[valid_mask]
        displacement_valid = displacement_data[valid_mask]
        
        # 回帰直線を計算 (x: 変位, y: 力)
        slope, intercept, r_value, p_value, std_err = linregress(displacement_valid, force_valid)
        
        # 決定係数
        r_squared = r_value**2
        
        # 統計情報
        force_range = np.max(force_valid) - np.min(force_valid)
        displacement_range = np.max(displacement_valid) - np.min(displacement_valid)
        
        print(f"    {subject_id}: 剛性={slope:.2f} N/mm, R²={r_squared:.3f}, 力範囲={force_range:.1f}N, 変位範囲={displacement_range:.1f}mm")
        
        return {
            'subject_id': subject_id,
            'condition': condition,
            'stiffness': slope,  # N/mm
            'intercept': intercept,  # N
            'r_squared': r_squared,
            'p_value': p_value,
            'std_error': std_err,
            'force_range': force_range,
            'displacement_range': displacement_range,
            'n_points': len(force_valid),
            'force_data': force_valid,
            'displacement_data': displacement_valid
        }
        
    except Exception as e:
        print(f"    {subject_id}: 手首剛性計算エラー - {e}")
        return None

def calculate_standard_error(values):
    """標準誤差を計算"""
    if len(values) == 0:
        return 0.0
    return np.std(values) / np.sqrt(len(values))

def plot_wrist_stiffness_comparison(stiffness_results, conditions=['Wrist_Contraction', 'Finger_Contraction', 'Finger_Wrist_Contraction']):
    """
    手首剛性の条件間比較棒グラフ
    
    Parameters:
    -----------
    stiffness_results : dict
        条件別手首剛性結果
    conditions : list
        比較する条件のリスト
    """
    print("\n=== 手首剛性比較解析 ===")
    
    # 条件別統計を計算
    condition_stats = {}
    
    for condition in conditions:
        if condition in stiffness_results:
            stiffness_values = [result['stiffness'] for result in stiffness_results[condition] if result is not None]
            
            if stiffness_values:
                condition_stats[condition] = {
                    'mean': np.mean(stiffness_values),
                    'std': np.std(stiffness_values),
                    'se': calculate_standard_error(stiffness_values),
                    'n': len(stiffness_values),
                    'values': stiffness_values
                }
                
                print(f"{condition}: 平均剛性={condition_stats[condition]['mean']:.2f}±{condition_stats[condition]['se']:.2f} N/mm (n={condition_stats[condition]['n']})")
            else:
                print(f"{condition}: データなし")
                condition_stats[condition] = {'mean': 0, 'std': 0, 'se': 0, 'n': 0, 'values': []}
    
    if not condition_stats:
        print("手首剛性データが見つかりません")
        return
    
    # 棒グラフ作成
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 条件名を日本語に変換
    condition_labels = {
        'Wrist_Contraction': '手首収縮',
        'Finger_Contraction': '指収縮', 
        'Finger_Wrist_Contraction': '指・手首収縮'
    }
    
    plot_conditions = [cond for cond in conditions if cond in condition_stats and condition_stats[cond]['n'] > 0]
    
    if not plot_conditions:
        print("プロット可能なデータがありません")
        return
    
    # メイン棒グラフ（標準誤差付き）
    means = [condition_stats[cond]['mean'] for cond in plot_conditions]
    ses = [condition_stats[cond]['se'] for cond in plot_conditions]
    ns = [condition_stats[cond]['n'] for cond in plot_conditions]
    labels = [condition_labels.get(cond, cond) for cond in plot_conditions]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c'][:len(plot_conditions)]
    
    bars = ax1.bar(labels, means, yerr=ses, capsize=5, alpha=0.8, color=colors, edgecolor='black', linewidth=1)
    
    # 被験者数を棒の上に表示
    for i, (bar, n, se) in enumerate(zip(bars, ns, ses)):
        height = bar.get_height()
    
    ax1.set_ylabel('手首剛性 (N/mm)', fontsize=12, fontweight='bold')
    ax1.set_title('手首剛性の条件間比較（平均値±標準誤差）', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, max(means) * 1.3 if means else 10)
    
    # 個別データ点プロット
    for i, condition in enumerate(plot_conditions):
        values = condition_stats[condition]['values']
        if values:
            # 個別データ点を散布図で表示
            x_positions = np.random.normal(i, 0.1, len(values))  # 少しランダムにばらつかせる
            ax2.scatter(x_positions, values, alpha=0.6, color=colors[i], s=50, edgecolors='black', linewidth=0.5)
            
            # 平均値を水平線で表示
            ax2.hlines(condition_stats[condition]['mean'], i-0.3, i+0.3, colors=colors[i], linewidth=3, alpha=0.8)
    
    ax2.set_xticks(range(len(plot_conditions)))
    ax2.set_xticklabels(labels)
    ax2.set_ylabel('手首剛性 (N/mm)', fontsize=12, fontweight='bold')
    ax2.set_title('個別被験者データと平均値', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('wrist_stiffness_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 統計的比較（簡易版）
    print("\n=== 統計比較 ===")
    if len(plot_conditions) >= 2:
        from scipy.stats import ttest_ind
        
        for i in range(len(plot_conditions)):
            for j in range(i+1, len(plot_conditions)):
                cond1 = plot_conditions[i]
                cond2 = plot_conditions[j]
                
                values1 = condition_stats[cond1]['values']
                values2 = condition_stats[cond2]['values']
                
                if len(values1) >= 2 and len(values2) >= 2:
                    t_stat, p_val = ttest_ind(values1, values2)
                    
                    label1 = condition_labels.get(cond1, cond1)
                    label2 = condition_labels.get(cond2, cond2)
                    
                    print(f"{label1} vs {label2}: t={t_stat:.3f}, p={p_val:.3f} {'***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'n.s.'}")

def plot_individual_stiffness_regression(stiffness_results, max_plots=6):
    """
    個別被験者の力-変位関係と回帰直線をプロット
    
    Parameters:
    -----------
    stiffness_results : dict
        条件別手首剛性結果
    max_plots : int
        最大プロット数
    """
    print(f"\n=== 個別被験者回帰直線プロット（最大{max_plots}名）===")
    
    all_results = []
    for condition, results in stiffness_results.items():
        for result in results:
            if result is not None:
                all_results.append(result)
    
    if not all_results:
        print("プロット可能なデータがありません")
        return
    
    # R²値でソートして上位をプロット
    all_results.sort(key=lambda x: x['r_squared'], reverse=True)
    plot_results = all_results[:max_plots]
    
    # グリッド計算
    n_plots = len(plot_results)
    cols = 3
    rows = (n_plots + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(15, 5*rows))
    if rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()
    
    colors = {'Wrist_Contraction': '#1f77b4', 'Finger_Contraction': '#ff7f0e', 'Finger_Wrist_Contraction': '#2ca02c'}
    
    for i, result in enumerate(plot_results):
        ax = axes[i]
        
        displacement = result['displacement_data']
        force = result['force_data']
        
        # 散布図
        color = colors.get(result['condition'], '#666666')
        ax.scatter(displacement, force, alpha=0.6, color=color, s=30, edgecolors='black', linewidth=0.5)
        
        # 回帰直線
        x_range = np.linspace(np.min(displacement), np.max(displacement), 100)
        y_pred = result['stiffness'] * x_range + result['intercept']
        ax.plot(x_range, y_pred, 'r-', linewidth=2, label=f'剛性={result["stiffness"]:.1f} N/mm')
        
        # 条件名を日本語に変換
        condition_jp = {'Wrist_Contraction': '手首収縮', 'Finger_Contraction': '指収縮', 'Finger_Wrist_Contraction': '指・手首収縮'}.get(result['condition'], result['condition'])
        
        ax.set_title(f'{result["subject_id"]} ({condition_jp})\nR²={result["r_squared"]:.3f}', fontsize=10)
        ax.set_xlabel('ForceGage変位 (mm)')
        ax.set_ylabel('ForceGage力 (N)')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # 余ったサブプロットを非表示
    for i in range(n_plots, len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.savefig('individual_stiffness_regression.png', dpi=300, bbox_inches='tight')
    plt.show()

def analyze_stiffness_quality(stiffness_results):
    """
    手首剛性解析の品質評価
    
    Parameters:
    -----------
    stiffness_results : dict
        条件別手首剛性結果
    """
    print("\n=== 手首剛性解析品質評価 ===")
    
    all_results = []
    for condition, results in stiffness_results.items():
        for result in results:
            if result is not None:
                all_results.append(result)
    
    if not all_results:
        print("評価可能なデータがありません")
        return
    
    # 品質指標の計算
    r_squared_values = [r['r_squared'] for r in all_results]
    stiffness_values = [r['stiffness'] for r in all_results]
    n_points = [r['n_points'] for r in all_results]
    
    print(f"総解析数: {len(all_results)}")
    print(f"決定係数 (R²): 平均={np.mean(r_squared_values):.3f}, 最小={np.min(r_squared_values):.3f}, 最大={np.max(r_squared_values):.3f}")
    print(f"手首剛性: 平均={np.mean(stiffness_values):.2f} N/mm, 範囲={np.min(stiffness_values):.2f}-{np.max(stiffness_values):.2f} N/mm")
    print(f"データ点数: 平均={np.mean(n_points):.1f}, 範囲={np.min(n_points)}-{np.max(n_points)}")
    
    # 低品質データの特定
    low_quality = [r for r in all_results if r['r_squared'] < 0.8]
    if low_quality:
        print(f"\n低決定係数データ (R² < 0.8): {len(low_quality)}件")
        for r in low_quality[:5]:  # 上位5件表示
            print(f"  {r['subject_id']} ({r['condition']}): R²={r['r_squared']:.3f}, 剛性={r['stiffness']:.1f} N/mm")

def run_wrist_stiffness_analysis(stiffness_results):
    """
    手首剛性解析の統合実行
    
    Parameters:
    -----------
    stiffness_results : dict
        条件別手首剛性結果
    """
    print("\n" + "="*50)
    print("手首剛性解析システム実行")
    print("="*50)
    
    # 1. 条件間比較棒グラフ
    plot_wrist_stiffness_comparison(stiffness_results)
    
    # 2. 個別回帰直線プロット
    plot_individual_stiffness_regression(stiffness_results, max_plots=9)
    
    # 3. 品質評価
    analyze_stiffness_quality(stiffness_results)
    
    print("\n手首剛性解析完了!")