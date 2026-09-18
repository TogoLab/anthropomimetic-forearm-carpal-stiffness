#include "SDControl.h"
#include "DXLSetup.h"

SdFs sd;
FsFile dataFile;
String fileName = "sensor_data.csv";  // デフォルトのファイル名
bool isReading = false;

int32_t playback_positions[MAX_ROWS][SERVO_NUM] = {};

static String readFilenameFromSerial(const char* prompt){
  DEBUG_SERIAL.println(prompt);
  waitForSerialInput();
  String name = DEBUG_SERIAL.readStringUntil('\n');
  name.trim();
  return name;
}

static void ensureCsvExtension(String& name){
  if (!name.endsWith(".csv")) name += ".csv";
}

static bool confirmYN(const char* msg){
  DEBUG_SERIAL.println(msg);
  waitForSerialInput();
  String input = DEBUG_SERIAL.readStringUntil('\n');
  input.trim();
  return input.equalsIgnoreCase("y");
}

// SDカードのルート直下から .csv ファイルを列挙し、番号選択させる。
// キャンセルまたは候補なしの場合は空文字列を返す。
static String selectCsvByNumber(){
  constexpr uint8_t MAX_LIST = 32;
  String names[MAX_LIST];
  uint8_t count = 0;
  FsFile dir;
  FsFile entry;
  if (!dir.open("/", O_READ)) {
    DEBUG_SERIAL.println("ディレクトリを開けませんでした。");
    return String();
  }
  while (count < MAX_LIST && entry.openNext(&dir, O_READ)) {
    if (!entry.isDirectory()) {
      char nameBuf[64];
      entry.getName(nameBuf, sizeof(nameBuf));
      String n = String(nameBuf);
      if (n.endsWith(".csv") || n.endsWith(".CSV")) {
        names[count++] = n;
      }
    }
    entry.close();
  }
  dir.close();

  if (count == 0) {
    DEBUG_SERIAL.println("CSVファイルがありません。");
    return String();
  }

  while (true) {
    DEBUG_SERIAL.println("ファイルを選択してください:");
    for (uint8_t i = 0; i < count; i++) {
      DEBUG_SERIAL.print("  ");
      DEBUG_SERIAL.print(i + 1);
      DEBUG_SERIAL.print(": ");
      DEBUG_SERIAL.println(names[i]);
    }
    DEBUG_SERIAL.println("  c: キャンセル");
    waitForSerialInput();
    String input = DEBUG_SERIAL.readStringUntil('\n');
    input.trim();
    if (input.equalsIgnoreCase("c")) return String();
    int idx = input.toInt();
    if (idx >= 1 && idx <= (int)count) {
      return names[idx - 1];
    }
    DEBUG_SERIAL.println("無効な選択です。");
  }
}

static bool SDCheck(){
  if (!sd.card()->errorCode()) {
    DEBUG_SERIAL.println("SDカードは正常です。");
  } else {
    DEBUG_SERIAL.print("SDカードエラー: ");
    DEBUG_SERIAL.println(sd.card()->errorCode());
    isReading = false;
    return false;
  }

  if (!dataFile.open(fileName.c_str(), O_READ)) {
    DEBUG_SERIAL.println("ファイルのオープンに失敗しました。");
    DEBUG_SERIAL.print("SDカードエラー: ");
    DEBUG_SERIAL.println(sd.card()->errorCode());
    isReading = false;
    return false;
  }
  return true;
}

bool initSD(){
  isReading = true;
  DEBUG_SERIAL.println("Teensy 4.1 SDカードロガーを初期化中...");
  if (!sd.begin(SD_CONFIG)) {
    sd.initErrorHalt(&DEBUG_SERIAL);
    return false;
  }
  DEBUG_SERIAL.println("SDカード初期化完了");
  return true;
}

bool chooseFile(){
  String selected = selectCsvByNumber();
  if (selected.length() == 0) return false;
  fileName = selected;
  DEBUG_SERIAL.print("選択されたファイル: ");
  DEBUG_SERIAL.println(fileName);
  return true;
}

bool initFileName(){
  fileName = readFilenameFromSerial("ファイル名を入力してください（拡張子 .csv を含む）:");
  ensureCsvExtension(fileName);

  DEBUG_SERIAL.print("使用するファイル名: ");
  DEBUG_SERIAL.println(fileName);

  // ファイルが存在しない場合、ヘッダーを書き込む
  if (!sd.exists(fileName.c_str())) {
    dataFile = sd.open(fileName.c_str(), FILE_WRITE);
    if (dataFile) {
        String dataString = "";
        for (uint8_t i = 0; i < SERVO_NUM; i++)
        {
            dataString += String(i);
            if (i != SERVO_NUM-1) dataString += ",";
        }
      dataFile.println(dataString);
      dataFile.close();
      DEBUG_SERIAL.println("新しいファイルを作成し、ヘッダーを書き込みました。");
    } else {
      DEBUG_SERIAL.println("ファイルの作成に失敗しました。");
      return false;
    }
  } else {
    DEBUG_SERIAL.println("既存のファイルにデータを追加します。");
  }

  DEBUG_SERIAL.println("データ記録を開始します...");
  isReading = false;
  return true;
}

void writeArrayToSD(int16_t *array) {
  dataFile = sd.open(fileName.c_str(), FILE_WRITE);
  String dataArray = "";
  if (dataFile) {
    for (int i = 0; i < SERVO_NUM; i++) {
        dataArray += String(array[i]);
        if (i != SERVO_NUM-1) dataArray += ",";
    }
    dataFile.println(dataArray);
    dataFile.close();
    DEBUG_SERIAL.println("データをSDカードに書き込みました。");
  } else {
    DEBUG_SERIAL.println("ファイルのオープンに失敗しました。");
  }
}

// SDカードを読んでCSVデータの行数を返す
uint8_t readAllData() {
  DEBUG_SERIAL.println("データ読み取りを開始します...");
  isReading = true;
  uint8_t rowCount = 0;
  uint8_t columnCount = 0;


  if(!SDCheck()){
    return 0;
  }


  DEBUG_SERIAL.print("ファイルサイズ: ");
  DEBUG_SERIAL.println(dataFile.size());

  DEBUG_SERIAL.println("データを読み込んでいます...");
  char buffer[256];  // 1行の最大長を想定（必要に応じて調整）
  rowCount = 0;
  columnCount = 0;

  for (uint8_t i = 0; i < MAX_ROWS; i++)
  {
    for (uint8_t j = 0; j < SERVO_NUM; j++)
    {
      playback_positions[i][j] = 0;
    }

  }
  // 先頭行（列番号）をスキップ
  String header = dataFile.readStringUntil('\n');

  while (dataFile.available() && rowCount < MAX_ROWS) {
    if (dataFile.fgets(buffer, sizeof(buffer)) > 0) {
      char* token = strtok(buffer, ",");
      int col = 0;
      while (token != NULL && col < SERVO_NUM) {
        playback_positions[rowCount][col] = atoi(token);
        token = strtok(NULL, ",");
        col++;
      }
      if (col > columnCount) columnCount = col;
      rowCount++;
    }

    // 進捗状況を表示（10行ごと）
    if (rowCount % 10 == 0) {
      DEBUG_SERIAL.print("読み込み中... 行数: ");
      DEBUG_SERIAL.println(rowCount);
    }
  }

  dataFile.close();

  DEBUG_SERIAL.println("---");
  DEBUG_SERIAL.print("読み込んだ行数: ");
  DEBUG_SERIAL.println(rowCount);
  DEBUG_SERIAL.print("列数: ");
  DEBUG_SERIAL.println(columnCount);
  DEBUG_SERIAL.println("データ読み取りが完了しました。");

  isReading = false;
  return rowCount;
}

void listFiles() {
  DEBUG_SERIAL.println("SDカード内のファイル一覧:");
  sd.ls(LS_R | LS_DATE | LS_SIZE);
  DEBUG_SERIAL.println();
}

void deleteFile() {
  String selected = selectCsvByNumber();
  if (selected.length() == 0) {
    DEBUG_SERIAL.println("キャンセルしました。");
    return;
  }
  DEBUG_SERIAL.print("削除するファイル: ");
  DEBUG_SERIAL.println(selected);
  if (!confirmYN("本当に削除しますか？ y/n")) {
    DEBUG_SERIAL.println("キャンセルしました。");
    return;
  }
  if (sd.remove(selected.c_str())) {
    DEBUG_SERIAL.println("ファイルを削除しました。");
  } else {
    DEBUG_SERIAL.println("ファイルの削除に失敗しました。");
  }
}
