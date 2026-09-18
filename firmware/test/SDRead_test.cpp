#include <SPI.h>
#include <SdFat.h>
#include <TeensyThreads.h>

const int chipSelect = BUILTIN_SDCARD;
SdFat sd;
File dataFile;

const int DATA_POINTS = 5; // 一度に読み取るデータポイントの数
String fileName = "sensor_data.csv";  // デフォルトのファイル名

Threads::Mutex fileMutex;
long currentPosition = 0; // ファイル内の現在の読み取り位置

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // シリアルポートの接続を待つ
  }

  Serial.println("Teensy 4.1 SDカードリーダーを初期化中...");

  if (!sd.begin(chipSelect)) {
    Serial.println("SDカードの初期化に失敗しました。");
    while (1);
  }
  Serial.println("SDカードの初期化に成功しました。");

  // ファイル名の入力を要求
  Serial.println("読み取るファイル名を入力してください（拡張子 .csv を含む）:");
  while (!Serial.available()) {
    ; // 入力を待つ
  }
  fileName = Serial.readStringUntil('\n');
  fileName.trim();  // 空白文字を削除

  if (!fileName.endsWith(".csv")) {
    fileName += ".csv";
  }

  Serial.print("読み取るファイル名: ");
  Serial.println(fileName);

  if (!sd.exists(fileName.c_str())) {
    Serial.println("指定されたファイルが存在しません。");
    while (1);
  }

  Serial.println("データ読み取りを開始します...");

  // データ読み取り用のスレッドを開始
  threads.addThread(dataReadingThread);
}

void loop() {
  // メインループは空です。すべての処理はスレッドで行われます。
}

void dataReadingThread() {
  while (true) {
    fileMutex.lock();
    readFromSD();
    fileMutex.unlock();

    threads.delay(1000);  // 1秒ごとに読み取り（必要に応じて調整可能）
  }
}

void readFromSD() {
  dataFile = sd.open(fileName.c_str(), FILE_READ);
  if (dataFile) {
    if (currentPosition >= dataFile.size()) {
      Serial.println("ファイルの終わりに達しました。最初から読み直します。");
      currentPosition = 0;
    }

    dataFile.seek(currentPosition);

    Serial.println("センサーデータ:");
    for (int i = 0; i < DATA_POINTS && dataFile.available(); i++) {
      String line = dataFile.readStringUntil('\n');
      if (line.length() > 0) {  // 空の行をスキップ
        Serial.println(line);
        currentPosition = dataFile.position();
      }
    }

    dataFile.close();
    Serial.println("---");
  } else {
    Serial.println("ファイルのオープンに失敗しました。");
  }
}