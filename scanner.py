"""
HC-SR04 超声波测距模块（固定朝前）

接线:
    HC-SR04 VCC  -> 5V
    HC-SR04 GND  -> GND（与 ESP32 共地）
    HC-SR04 TRIG -> GPIO 32
    HC-SR04 ECHO -> 分压到 3.3V 后接 GPIO 34

说明:
    ECHO 输出为 5V，必须用电阻分压后再接 ESP32。
    例如 1kΩ + 2kΩ，或 3 个 10kΩ（1 个串联、2 个串联到地）。
"""

import machine
import time

# ---- 测距参数 ----
TRIG_PIN = 32
ECHO_PIN = 34
MAX_DISTANCE_CM = 200      # 超过该距离视为无有效障碍物
MEASURE_INTERVAL_MS = 100  # 两次测量的间隔
ECHO_TIMEOUT_US = 30000    # 等待回波的最长时间（约 5m）
CLEAR_AFTER_MISSES = 10    # 连续无回波次数达到该值后清除障碍点（约 1s）
FRONT_ANGLE = 90           # 固定朝前


class UltrasonicScanner:
    """周期读取超声波距离，并保存供网页显示的最新障碍点。"""

    def __init__(self, trig_pin=TRIG_PIN, echo_pin=ECHO_PIN,
                 interval_ms=MEASURE_INTERVAL_MS, max_cm=MAX_DISTANCE_CM):
        self._trig = machine.Pin(trig_pin, machine.Pin.OUT, value=0)
        self._echo = machine.Pin(echo_pin, machine.Pin.IN)

        self._interval_ms = interval_ms
        self._max_cm = max_cm

        self._distance = None
        self._miss_count = 0
        self._points = []

    def _read_distance_cm(self):
        """触发一次测距，返回厘米；无回波或超量程返回 None。"""
        self._trig.value(1)
        time.sleep_us(10)
        self._trig.value(0)

        duration = machine.time_pulse_us(self._echo, 1, ECHO_TIMEOUT_US)
        if duration < 0:
            return None

        distance = duration / 58.0
        if distance <= 0 or distance > self._max_cm:
            return None
        return round(distance, 1)

    def update(self):
        """测量一次并更新障碍点，由 HTTP 服务器主循环调用。"""
        self._distance = self._read_distance_cm()

        if self._distance is None:
            self._miss_count += 1
            if self._miss_count >= CLEAR_AFTER_MISSES:
                self._points = []
        else:
            self._miss_count = 0
            self._points = [(FRONT_ANGLE, self._distance)]

        time.sleep_ms(self._interval_ms)

    def snapshot(self):
        """返回网页所需的当前测距结果。"""
        return {
            "angle": FRONT_ANGLE,
            "distance": self._distance,
            "min_angle": FRONT_ANGLE,
            "max_angle": FRONT_ANGLE,
            "max_cm": self._max_cm,
            "points": [[angle, distance] for angle, distance in self._points],
        }
