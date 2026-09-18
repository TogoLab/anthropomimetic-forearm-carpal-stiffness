# -*- coding: utf-8 -*-
import serial
import re
from serial.serialutil import SerialException
from serial.tools import list_ports
import csv

def parse_numeric_string(input_string):
    #  数値部分のみを抽出し、カンマと改行を除去して返す
    numeric_string = re.sub(r'[^\d,]', '', input_string)
    return numeric_string

def select_port(devices):    
    #  シリアルポートに接続されているデバイスに接続
    if len(devices) == 0:
        print("USBデバイスが見つかりませんでした")
    elif len(devices) == 1:
        print("USBデバイス %s が見つかりました。接続します" % devices[0])
        return 0
    else:
        print("複数のUSBデバイスを検出しました。以下より接続するデバイスを番号で指定してください")
        for i in range(len(devices)):
            print("%3d: %s" % (i, devices[i]))
        num = int(input())
        return num


Serial = serial.Serial()

devices = list(list_ports.comports())

# Arduinoとのシリアル通信の設定
Serial.baudrate = 115200                                  # ボーレート
Serial.timeout = 1                                      # タイムアウト
Serial.port = str(devices[select_port(devices)].device) # 接続するCOMポート
Serial.dtr = False                                      # DTRを無効にする
# print(Serial.port)

# 送信するCSVファイルのパス
csv_file_path = './data.csv'
sending_line = ''

while True:
    try:
        Serial.open() # シリアルポートを開く
        
        with open(csv_file_path, 'w+') as file: # CSVファイルを開いて内容を読み取り、Arduinoに送信
            lines = file.readlines()
            received_data = Serial.readline() # write前に一度readする
            if(Serial.writable()):
                Serial.write("Hello".encode())
            while(Serial.readable()):
                received_data: bytes = Serial.readline() # write前に一度readする
                if(received_data):
                    data = received_data.decode()
                    print(data)
                    file.writelines(data)

        #     for line in lines:
        #         sending_line = sending_line + parse_numeric_string(line) # データを追加
        #         # time.sleep(0.1)  # Arduinoが読み取りやすいように適切な遅延を挿入
            
        #     Serial.write((sending_line + "e").encode()) # Arduinoへ書き込み

        #     # received_data = Serial.readline()   # 返答を読む
        
        print("CSVファイルをデバイスに送信しました")
        
    except FileNotFoundError:   # csvファイルが見つからないとき
        print("指定されたCSVファイルが見つかりませんでした")

    except SerialException:     # シリアルポートが開けなかったとき
        print("シリアルポートが開けませんでした")
    
    except Exception as e:
        print("エラーが発生しました", e)

    finally:
        print("ポートを閉じます")
        Serial.close()                                  # シリアルポートを閉じる
        sending_line = ''                               # 送信データをクリア    
