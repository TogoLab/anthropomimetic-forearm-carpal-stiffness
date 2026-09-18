angles = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
force_dir_name = "force_gage"
motion_dir_name = "motion_capture"
# type_name = "low_contraction_1217"
# type_name = "high_contraction_1222"
# type_name = "high_contraction_0202"
type_name = "low_contraction_0202"
# type_name = "super_high_contraction"
# type_name = "finger_contraction"
START_FORCE = 0.5
MEASUREMENT_DISTANCE = 5
# 力センサーデータの読み込み
headers = ['timestamp']
for i in range(1, 23):
    headers.extend([f'curr{i}', f'pos{i}'])
headers.append('Force')
