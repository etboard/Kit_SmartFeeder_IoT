/******************************************************************************************
 * FileName     : SmartFeeder_IoT.ino
 * Description  : 이티보드 스마트 급식기 코딩 키트(IoT)
 * Author       : PEJ
 * Created Date : 2024.10.23
 * Reference    : 
******************************************************************************************/
const char* board_firmware_verion = "smartFee_0.91";


//==========================================================================================
// IoT 프로그램 사용하기
//==========================================================================================
#include "ET_IoT_App.h"
ET_IoT_App app;


//==========================================================================================
// 서보 모터 사용하기
//==========================================================================================.
#include <Servo.h>
Servo servo;                                             // 서보 모터 객체 생성
const int servo_pin = D8;                                // 서보 모터 핀 : D8


//==========================================================================================
// 전역 변수 선언
//==========================================================================================
const int motor_pin1 = D2;                               // 모터 제어 핀: D2
const int motor_pin2 = D3;                               // 모터 제어 핀: D3

const int motor_button = D7;                             // 먹이 공급 버튼 : D7(노랑)

const int echo_pin = D8;                                 // 초음파 수신 핀: D8
const int trig_pin = D9;                                 // 초음파 송신 핀: D9

int operation_mode_led = D4;                             // 작동 모드 LED 핀: D4(초록)

int count;                                               // 먹이 공급 횟수
float distance;                                          // 거리
String motor_state = "off";                              // 모터 상태

unsigned long timer = 1 * 60  * 120  * 1000UL;           // 먹이 공급 타이머의 시간
unsigned long now = 0;                                   // 현재 시간
unsigned long last_feeding = 0;                          // 마지막 먹이 공급 시간
String time_remaining = "00:00:00";                      // 남은 타이머 시간


//==========================================================================================
void et_setup()                                          // 사용자 맞춤형 설정
//==========================================================================================
{
  pinMode(motor_pin1, OUTPUT);                           // 모터 제어 핀 1: 출력 모드
  pinMode(motor_pin2, OUTPUT);                           // 모터 제어 핀 2: 출력 모드

  pinMode(motor_button, INPUT);                          // 모터 제어 버튼: 입력 모드

  pinMode(trig_pin, OUTPUT);                             // 초음파 송신부: 출력 모드
  pinMode(echo_pin, INPUT);                              // 초음파 수신부: 입력 모드

  motor_off();                                           // 모터 중지

  app.operation_mode = "automatic";                      // 작동 모드: 자동
  app.send_data("motor", "state", motor_state);          // 파랑 LED 작동 상태 응답
  app.send_data("green_led", "state", LOW);              // 초록 LED 작동 상태 응답
  app.send_data("operation_mode", "mode", app.operation_mode);   // 작동 모드
}


//==========================================================================================
void et_loop()                                           // 사용자 반복 처리
//==========================================================================================
{
  do_sensing_process();                                  // 센싱 처리

  do_automatic_process();                                // 자동화 처리
}


//==========================================================================================
void do_sensing_process()                                // 센싱 처리
//==========================================================================================
{
  now = millis();                                        // 현재 시간 저장

  if (digitalRead(motor_button) == LOW) {                // 먹이 공급 버튼이 눌렸다면
    food_supply();                                       // 먹이 공급
  }

  // 초음파 송신
  digitalWrite(trig_pin, LOW);
  digitalWrite(echo_pin, LOW);
  delayMicroseconds(2);
  digitalWrite(trig_pin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_pin, LOW);

  unsigned long duration  = pulseIn(echo_pin, HIGH);     // 초음파 수신까지의 시간 계산
  distance = duration * 17 / 1000;                        // 거리 계산

  delay(100);
}


//==========================================================================================
void food_supply()                                       // 먹이 공급
//==========================================================================================
{
  motor_control();                                       // 모터 제어

  last_feeding = now;                                    // 마지막 먹이 공급 시간 업데이트
  count += 1;                                            // 먹이 공급 횟수 증가
  app.send_data("feeder", "count", count);               // 먹이 공급 횟수 송신
}


//==========================================================================================
void motor_control()                                     // 모터 제어
//==========================================================================================
{
  motor_on();                                            // 모터 작동
  delay(1000);

  motor_off();                                           // 모터 중지
}


//==========================================================================================
void motor_on()                                          // 모터 작동
//==========================================================================================
{
  motor_state = "on";                                    // 모터 상태 변경
  display_information();                                 // OLED 표시
  app.send_data("motor", "state", motor_state);          // 먹이 공급 횟수 송신

  servo.write(50);                                       // 차단봉 열기

  digitalWrite(motor_pin1, HIGH);                        // DC 모터 작동
  digitalWrite(motor_pin2, HIGH);

  delay(1000);
}


//==========================================================================================
void motor_off()                                         // 모터 작동
//==========================================================================================
{
  motor_state = "off";                                   // 모터 상태 변경
  display_information();                                 // OLED 표시
  app.send_data("motor", "state", motor_state);          // 먹이 공급 횟수 송신

  digitalWrite(motor_pin1, LOW);                         // DC 모터 중지
  digitalWrite(motor_pin2, LOW);

  delay(600);

  servo.write(180);                                       // 차단봉 열기
}


//==========================================================================================
void do_automatic_process()                              // 자동화 처리
//==========================================================================================
{
  if(app.operation_mode != "automatic")                  // 작동 모드가 automatic 일 경우만
    return;

  if(now - last_feeding < timer && distance > 4) return;

  food_supply();                                         // 먹이 공급
}


//==========================================================================================
void et_short_periodic_process()                         // 사용자 주기적 처리 (예 : 1초마다)
//==========================================================================================
{   
  display_information();                                 // 표시 처리
}


//==========================================================================================
void display_information()                               // OLED 표시
//==========================================================================================
{
  String string_count = String(count);                   // 횟수 문자열 변환
  String string_distance = String(distance);             // 거리 문자열 변환

  app.oled.setLine(1, board_firmware_verion);            // 1번째 줄에 펌웨어 버전
  app.oled.setLine(2, "mode: " + app.operation_mode);    // 2번째 줄에 모드
  app.oled.setLine(3, "count: " + string_count);         // 3번째 줄에 횟수
  app.oled.setLine(4, "distance : " + string_distance);  // 4번째 줄에 거리
  app.oled.setLine(5, "motor : " + motor_state);         // 5번째 줄에 모터 상태

  if (app.operation_mode == "automatic") {               // 자동 모드라면
    time_remaining_calculate();
    app.oled.setLine(6, "timer : " + time_remaining);    // 6번째 줄에 타이머
  }
  app.oled.display(6);                                   // OLED에 표시
}


//==========================================================================================
void time_remaining_calculate()                          // 남은 시간 계산
//==========================================================================================
{
  unsigned long time_cal = now - last_feeding;
  unsigned long timer_cal = timer - time_cal;

  int hour = timer_cal / (60 * 60 * 1000);
  timer_cal = timer_cal % (60 * 60 * 1000);

  int minute = timer_cal / (60 * 1000);
  timer_cal = timer_cal % (60 * 1000);

  int second = timer_cal / 1000;

  time_remaining = String(hour) + ":" + String(minute) + ":" + String(second);
}


//==========================================================================================
void et_long_periodic_process()                          // 사용자 주기적 처리 (예 : 5초마다)
//==========================================================================================
{
  send_message();                                        // 메시지 송신
}


//==========================================================================================
void send_message()                                      // 메시지 송신
//==========================================================================================
{
  app.add_sensor_data("distance", distance);             // 센서 데이터 추가
  app.send_sensor_data();                                // 센서 데이터 송신

  app.send_data("feeder", "count", count);               // 먹이 공급 횟수 송신

  if (app.operation_mode == "automatic") {               // 자동 모드라면
    time_remaining_calculate();
    app.send_data("timer", "time_remaining", time_remaining);  // 타이머 남은 시간 송신
  }
}


//==========================================================================================
void recv_message()                                      // 메시지 수신
//==========================================================================================
{
  // "operation_mode" 메시지를 받으면 process_operation_mode() 실행
  app.setup_recv_message("operation_mode", process_operation_mode);

  // "feeder" 메시지를 받으면 process_motor_control() 실행
  app.setup_recv_message("feeder", process_motor_control);
}


//==========================================================================================
void process_operation_mode(const String &msg)           // 작동 모드 처리
//==========================================================================================
{
  pinMode(operation_mode_led, OUTPUT);                   // 작동 모드 LED: 출력 모드

  if (msg == "automatic") {                              // 작동 모드: 자동
    app.operation_mode = "automatic";
    digitalWrite(operation_mode_led, HIGH);
    Serial.println("작동모드: automatic, 초록 LED on");
  } else {                                               // 작동 모드: 수동
    app.operation_mode = "manual";
    digitalWrite(operation_mode_led, LOW);
    Serial.println("작동모드: manual, 초록 LED off");
  }
}


//==========================================================================================
void process_motor_control(const String &msg)            // 모터 LED 제어 처리
//==========================================================================================
{
  // 자동 모드인 경우에는 모터를 원격에서 제어를 할 수 없음
  if (app.operation_mode == "automatic")
    return;

  // 수동 모드인 경우이면서
  if (msg == "action") {                                 // 메시지가 "action"이라면
    food_supply();                                       // 먹이 공급
  }
}


//==========================================================================================
//
// (주)한국공학기술연구원 http://et.ketri.re.kr
//
//==========================================================================================