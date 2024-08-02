#include <Arduino.h>
#include <WiFi.h>
#include <FirebaseESP32.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// Firebase 프로젝트 설정
#define FIREBASE_HOST "FIREBASE_DATABASE_URL"
#define FIREBASE_AUTH "FIREBASE_AUTHORIZATION_KEY"

// WiFi 설정
#define WIFI_SSID ""
#define WIFI_PASSWORD ""

// 핀 설정
const int hrvPowerPin = 17;  // HRV 센서 전원 핀 연결
const int inputPin = 34;     // HRV 센서 신호 핀 연결

Adafruit_MPU6050 mpu;

bool im_home_now = false;
bool music_create = false;
unsigned long starttime = 0;
unsigned long saved_state = 0;
int beepnumber = 0;
int state = 0;  // 0: Default, 1: sleep, 2: off

// Firebase 객체 생성
FirebaseData firebaseData;
FirebaseAuth auth;
FirebaseConfig config;

// 랜덤 값 업데이트 주기
unsigned long lastUpdate = 0;
const unsigned long updateInterval = 20000; // 20초

void setup() {
  // Serial 통신 초기화
  Serial.begin(115200);

  // HRV 센서 전원 핀을 HIGH로 설정
  pinMode(hrvPowerPin, OUTPUT);
  digitalWrite(hrvPowerPin, HIGH); // 전원 핀을 항상 HIGH로 설정

  // WiFi 연결
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected with IP: ");
  Serial.println(WiFi.localIP());

  // Firebase 설정
  config.api_key = FIREBASE_AUTH;
  config.database_url = "https://" FIREBASE_HOST;
  
  // 인증 설정
  auth.token.uid = ""; // 익명 인증은 UID 필요 없음

  // Firebase 초기화
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);




}

int determineStatus() {
  unsigned long startTime = millis();
  float totalMotion = 0;
  int count = 0;

  while (millis() - startTime < 3000) { // 3초 동안 데이터 수집
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    float motion = abs(g.gyro.x) + abs(g.gyro.y) + abs(g.gyro.z);
    totalMotion += motion;
    count++;

    delay(100); // 데이터 수집 간격 조정
  }

  float averageMotion = totalMotion / count;

  if (averageMotion < 0.05) {
    return 1;  // 수면
  } else if (averageMotion > 0.5) {
    return 0;  // 벗음
  } else {
    return 2;  // Default
  }
}

void loop() {
  Firebase.setInt(firebaseData, "/HRV", 0);
  Firebase.setFloat(firebaseData, "/temp", 0.0);
  Firebase.setFloat(firebaseData, "/humid", 0);
  Firebase.setBool(firebaseData, "/music_create", false);
  // Firebase에서 "/im_home_now" 값을 가져와서 im_home_now 변수에 저장
  if (Firebase.getBool(firebaseData, "/im_home_now")) {
    im_home_now = firebaseData.boolData();
  }

  while (im_home_now) {
    
    Serial.print("Home entrance: ");
    Serial.println(im_home_now);
    Serial.print("It's in the imhome sequence");
    Serial.print("State: ");
    Serial.println(state);
    state=0;
    /*
    if (state == 0) {  // 상태가 기본(Default)인 경우
      while (millis() - starttime <= 10000) {  // 60초 동안 데이터를 수집
        unsigned long hrv_state = analogRead(inputPin);

        if (hrv_state != saved_state) {
          beepnumber += 1;
          saved_state = hrv_state;
        }

        Serial.print("HRV Data: ");
        Serial.println(hrv_state);  // HRV 데이터 출력

        if (state == 2) {
          music_create = false;
          break;
        }

        delay(500);  // 안정성을 위한 지연
      }

      im_home_now = false;

      Serial.print("HRV: ");
      Serial.println(beepnumber / 2);

      if (music_create) {
        Firebase.setInt(firebaseData, "/HRV", beepnumber / 2);
        Firebase.setBool(firebaseData, "/music_create", music_create);

        beepnumber = 0;  // beepnumber 초기화
        music_create = false;
      }
    } else {
      Serial.print("Took off the watch");
      music_create = false;
    }
  }
  */
  // 랜덤 값 업데이트
    Firebase.setInt(firebaseData, "/HRV", 1);
    unsigned long startTime = millis();
    while (millis() - starttime <= 10000){
      
    }
    if(true){
      // 랜덤 값 생성
      int randomBeepnumber = random(160, 201); // 160~200
      float randomTemp = random(359, 376) / 10.0; // 35.9~37.5
      float randomHumid = random(20, 41); // 20~40
  
      // Firebase에 데이터 전송
      Firebase.setInt(firebaseData, "/HRV", randomBeepnumber/2);
      Firebase.setFloat(firebaseData, "/temp", randomTemp);
      Firebase.setFloat(firebaseData, "/humid", randomHumid);
      Firebase.setBool(firebaseData, "/music_create", true);
      delay(1000);
      // music_create를 0으로 변경
      
  
      Serial.print("Sent random data to Firebase:");
      Serial.print(" HRV: "); Serial.print(randomBeepnumber);
      Serial.print(" Temp: "); Serial.print(randomTemp);
      Serial.print(" Humid: "); Serial.print(randomHumid);
      Serial.println();
    }

  // 상태 결정 및 처리
  /*
  state = determineStatus();
  Serial.print("State: ");
  Serial.println(state);

  if (state == 1) {  // 수면 상태인 경우
    Serial.print("I'm in the sleeping sequence");
    starttime = millis();
    music_create = true;

    while ((millis() - starttime <= 10000) && state == 1) {
      if (state != 1) {
        state = 0;
        music_create = false;
        break;
      }

      unsigned long hrv_state = analogRead(inputPin);

      if (hrv_state != saved_state) {
        beepnumber += 1;
        saved_state = hrv_state;
      }

      Serial.print("HRV Data: ");
      Serial.println(hrv_state);

      state = determineStatus();
      delay(500); // 안정성을 위한 지연
    }

    if (music_create && state == 1) {
      Serial.print("Sleeping Data sent ");
      Firebase.setInt(firebaseData, "/HRV", beepnumber / 2);
      Firebase.setBool(firebaseData, "/music_create", music_create);

      beepnumber = 0;
      music_create = false;
    }
    */
  }
  //Firebase.setBool(firebaseData, "/music_create", false);
}