# ******************************************************************************************
# FileName     : Kit_SmartFeeder_IoT.py
# Description  : 이티보드 스마트 급식기 코딩 키트(IoT)
# Author       : 박은정
# Created Date : 2024.09.23 : PEJ 
# Reference    :
# ******************************************************************************************
board_firmware_verion = 'smartFee_0.91' 


#===========================================================================================
# 기본 모듈 사용하기
#===========================================================================================
import time
from machine import Pin, ADC, time_pulse_us
from ETboard.lib.pin_define import *
from ETboard.lib.servo import Servo


#===========================================================================================
# IoT 프로그램 사용하기
#===========================================================================================
from ET_IoT_App import ET_IoT_App, setup, loop
app = ET_IoT_App()


#===========================================================================================
# oled 표시 장치 사용하기
#===========================================================================================
from ETboard.lib.OLED_U8G2 import *
oled = oled_u8g2()


#===========================================================================================
# 전역 변수 선언
#===========================================================================================
motor_pin1 = Pin(D2)                                     # 모터 제어 핀 : D2
motor_pin2 = Pin(D3)                                     # 모터 제어 핀 : D3

motor_button = Pin(D7)                                   # 서보 모터 작동 버튼 : 파랑

servo_pin = Servo(Pin(D6))                               # 서보 모터 핀 : D6

echo_pin = Pin(D8)                                       # 초음파 수신 핀: D8
trig_pin = Pin(D9)                                       # 초음파 송신 핀: D9

operation_mode_led = Pin(D4)                             # 작동 모드 LED : 초록

count = 0                                                # 먹이 공급 횟수
distance = 0                                             # 거리
motor_state = 'off'                                      # 모터 상태

timer = 10                                               # 먹이 공급 타이머 시간
now = 0                                                  # 현재 시간
last_feeding = 0                                         # 마지막 먹이 공급 시간
time_remaining = ''                                      # 남은 타이머 시간


#===========================================================================================
def et_setup():                                          #  사용자 맞춤형 설정
#===========================================================================================
    motor_pin1.init(Pin.OUT)                             # 모터 제어 핀 1 : 출력 모드
    motor_pin2.init(Pin.OUT)                             # 모터 제어 핀 2 : 출력 모드

    motor_button.init(Pin.IN)                            # 모터 제어 버튼 : 입력 모드

    echo_pin.init(Pin.IN)                                # 초음파 수신부: 입력 모드
    trig_pin.init(Pin.OUT)                               # 초음파 송신부: 출력 모드

    motor_off()                                          # 서보모터 중지

    app.operation_mode = 'automatic'                     # 작동 모드: 자동
    app.send_data('motor', 'state', motor_state)         # 모터 작동 상태 송신
    app.send_data('operation_mode', 'mode', app.operation_mode)    # 작동 모드    

    recv_message()                                       # 메시지 수신


#===========================================================================================
def et_loop():                                           # 사용자 반복 처리
#===========================================================================================
    do_sensing_proces()                                  # 센싱 처리
    do_automatic_process()                               # 자동화 처리


#===========================================================================================
def do_sensing_proces():                                 # 센싱 처리
#===========================================================================================
    global distance, now

    now = int(round(time.time()))                        # 현재 시간 저장

    if motor_button.value() == LOW:                      # 먹이 공급 버튼이 눌렸다면
        food_supply()                                    # 먹이 공급

    # 초음파 송신
    trig_pin.value(LOW)
    echo_pin.value(LOW)
    time.sleep_ms(2)
    trig_pin.value(HIGH)
    time.sleep_ms(10)
    trig_pin.value(LOW)

    duration = time_pulse_us(echo_pin, HIGH)             # 초음파 수신까지의 시간 계산
    distance = 17 * duration / 1000                      # 거리 계산

    time.sleep(0.1)


#===========================================================================================
def motor_on():                                          # 모터 작동
#===========================================================================================
    global motor_state                                   # 전역 변수 호출

    motor_state = 'on'                                   # 모터 상태 변경
    display_information()                                # oled 표시
    app.send_data('motor', 'state', motor_state)         # 모터 작동 상태 응답

    servo_pin.write_angle(50)                            # 차단봉 열기

    motor_pin1.value(HIGH)                               # DC 모터 켜기
    motor_pin2.value(HIGH)

    time.sleep(1)                                        # 1초간 대기


#===========================================================================================
def motor_off():                                         # 모터 중지
#===========================================================================================
    global motor_state                                   # 전역 변수 호출

    motor_state = 'off'                                  # 모터 상태 변경
    display_information()                                # oled 표시
    app.send_data('motor', 'state', motor_state)         # 모터 작동 상태 응답

    motor_pin1.value(LOW)                                # DC 모터 끄기
    motor_pin2.value(LOW)

    time.sleep(0.6)                                      #  0.6초간 대기

    servo_pin.write_angle(180)                           # 차단봉 닫기


#===========================================================================================
def motor_control():                                     # 모터 제어
#===========================================================================================
    motor_on()                                           # 모터 작동
    time.sleep(1)

    motor_off()                                          # 모터 중지


#===========================================================================================
def food_supply():                                       # 먹이 공급
#===========================================================================================
    global count, last_feeding, now

    motor_control()                                      # 모터 제어

    last_feeding = now                                   # 마지막 먹이 공급 시간 업데이트
    count += 1                                           # 먹이 공급 횟수 증가
    app.send_data('feeder', 'count', count)              # 먹이 공급 횟수 송신


#===========================================================================================
def do_automatic_process():                              # 자동화 처리
#===========================================================================================
    if (app.operation_mode != 'automatic'):              # 작동 모드가 automatic일 경우만
        return

    global distance, timer, now, last_feeding, time_remaining
    if now - last_feeding < timer and distance > 4:
        return

    food_supply()                                        # 먹이 공급


#===========================================================================================
def et_short_periodic_process():                         # 사용자 주기적 처리 (예 : 1초마다)
#===========================================================================================
    display_information()                                # 표시 처리


#===========================================================================================
def time_remaining_calculate():                          # 남은 타이머 시간 계산
#===========================================================================================
    global last_feeding, now, time_remaining

    cal_time = now - last_feeding
    minute, sec = divmod(timer - cal_time, 60)
    hour, minute = divmod(minute, 60)

    time_remaining = '{:0>2}'.format(hour) + ':' + '{:0>2}'.format(minute) + ':' + \
                     '{:0>2}'.format(sec)


#===========================================================================================
def display_information():                               # oled 표시
#===========================================================================================
    global board_firmware_verion, count, distance, motor_state, time_remaining
    string_count = '%3d' % count                         # 횟수 문자열 변환
    string_distance = '%.1f' % distance                  # 거리 문자열 변환

    oled.clear()                                         # oled 초기화
    oled.setLine(1, board_firmware_verion)               # 1번째 줄에 펌웨어 버전
    oled.setLine(2, 'mode: ' + app.operation_mode)       # 2번째 줄에 모드
    oled.setLine(3, 'count: ' + string_count)            # 3번째 줄에 횟수
    oled.setLine(4, 'distance: ' + string_distance + ' cm')   # 4번쩨 줄에 거리
    oled.setLine(5, 'motor: ' + motor_state)             # 5번쩨 줄에 모터 상태

    if app.operation_mode == 'automatic':                # 자동 모드라면
        time_remaining_calculate()
        oled.setLine(6, 'timer: ' + time_remaining)      # 6번쩨 줄에 타이머

    oled.display()


#===========================================================================================
def et_long_periodic_process():                          # 사용자 주기적 처리 (예 : 5초마다)
#===========================================================================================
    send_message()                                       # 메시지 송신


#===========================================================================================
def send_message():                                      # 메시지 송신
#===========================================================================================
    global distance, count, time_remaining
    app.add_sensor_data('distance', distance)            # 센서 데이터 추가
    app.send_sensor_data()                               # 센서 데이터 송신

    app.send_data('feeder', 'count', count)              # 먹이 공급 횟수 송신

    if app.operation_mode == 'automatic':
        time_remaining_calculate()
        app.send_data('timer', 'time_remaining', time_remaining)


#===========================================================================================
def recv_message():                                      # 메시지 수신
#===========================================================================================
    # 'operation_mode' 메시지를 받으면 process_operation_mode() 실행
    app.setup_recv_message('operation_mode', process_operation_mode)

    # 'motor' 메시지를 받으면 process_motor_control() 실행
    app.setup_recv_message('feeder', process_motor_control)


#===========================================================================================
def process_operation_mode(topic, msg):                  # 작동 모드 처리
#===========================================================================================
    operation_mode_led.init(Pin.OUT)                     # 작동 모드 LED: 출력 모드

    if msg == 'automatic':                               # 작동 모드: 자동으로
        app.operation_mode = 'automatic'
        operation_mode_led.value(1)                      # LED 켜기
        print('작동모드: automatic, 초록 LED on')
    else:                                                # 작동 모드: 수동으로
        app.operation_mode = 'manual'
        operation_mode_led.value(0)                      # LED 끄기
        print('작동모드: manual, 초록 LED off')


#===========================================================================================
def process_motor_control(topic, msg):                   # 모터 제어 처리
#===========================================================================================
    # 자동 모드인 경우에는 모터를 원격에서 제어를 할 수 없음
    if (app.operation_mode == 'automatic'):
        return

    if msg == 'action':                                  # 메시지가 'action'이라면
        food_supply()                                    # 먹이 공급


#===========================================================================================
# 시작 지점                     
#===========================================================================================
if __name__ == '__main__':
    setup(app, et_setup)
    while True:
        loop(app, et_loop, et_short_periodic_process, et_long_periodic_process)


#===========================================================================================
#                                                    
# (주)한국공학기술연구원 http://et.ketri.re.kr       
#
#===========================================================================================
