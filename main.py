"""
舵机与 ESP32 引脚接线图, 数据口方向为后 (tail)

    前 (head)
        -----               -----
        |  2  |             |  3  |
        |pin25|             |Pin18|
        ----- -----   ----- -----
            |  0  | |  1  |
            |Pin12| |Pin16|
             -----   -----
            |  4  | |  5  |
            |Pin15| |Pin17|
        ----- -----   ----- -----
        |  6  |             |  7  |
        |Pin26|             |Pin19|
        -----               -----
    后 (tail)
"""

from quad import Quad
from robot_wifi import RobotWifi
from scanner import UltrasonicScanner

# ---------- 配置 ----------

# 8 个舵机引脚:
# 前右髋、前左髋、前右腿、前左腿、后右髋、后左髋、后右腿、后左腿
SERVO_PINS = (12, 16, 25, 18, 15, 17, 26, 19)

# 超声波测距引脚（ECHO 需要分压到 3.3V）
TRIG_PIN = 32
ECHO_PIN = 34

# AP 模式：ESP32 自己创建热点
AP_SSID = "Otto"
AP_PASSWORD = "88889999"
IFCONFIG = ("192.168.2.182", "255.255.255.0", "192.168.2.1", "8.8.8.8")

# 路由模式：ESP32 连接已有路由器（按需修改）
WIFI_SSID = "wifi_name"
WIFI_PASSWORD = "wifi_password"


def main():
    robot = Quad()
    robot.init(*SERVO_PINS)
    robot.setTrims(0, 0, 0, 0, 0, 0, 0, 0)

    scanner = UltrasonicScanner(trig_pin=TRIG_PIN, echo_pin=ECHO_PIN)
    robot_wifi = RobotWifi(robot=robot, scanner=scanner)

    # 没有路由器时使用 AP 模式：手机连接热点 Otto，访问 192.168.2.182
    robot_wifi.create_connect_ap(essid=AP_SSID, password=AP_PASSWORD,
                                 ifconfig=IFCONFIG)

    # 路由模式：ESP32 和手机连接同一个路由器
    # robot_wifi.create_connect_route(ssid=WIFI_SSID,
    #                                 password=WIFI_PASSWORD,
    #                                 ifconfig=IFCONFIG)

    robot_wifi.create_server()


if __name__ == "__main__":
    main()
