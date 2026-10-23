# 简版四足机器人（ESP32 + MicroPython）

ESP32 · MicroPython · 8 舵机 · WiFi 网页控制 · 超声波测距

基于 ESP32 和 MicroPython 的八舵机四足机器人。手机或电脑通过浏览器即可控制行走、
转向和预设动作；板载 HC-SR04 超声波模块实时检测正前方障碍物，并在网页平面图上用红点标记。

- 完整的项目说明、接口和二次开发指南：[OPEN_SOURCE.md](OPEN_SOURCE.md)
- 详细接线步骤与上电检查清单：[WIRING.md](WIRING.md)

---

## 功能特性

- 网页方向控制：前进、后退、左转、右转、回中
- 10 个预设动作：Hello、OmniWalk、Moonwalk、Dance、UpDown、PushUp、
  FrontBack、WaveHand、Hide、Scared
- AP 热点模式 / STA 路由模式
- 超声波实时测距，网页每 400ms 刷新一次平面图
- 障碍物以红色发光点显示，距离圈为 50/100/150/200cm
- HTTP 接口可被脚本或其他设备直接调用

## 项目展示

![舵机接线图](images/quad-wiring.jpeg)

整机照片与演示视频后续补充，计划使用以下路径：

- 整机照片：`images/robot.jpg`
- 网页截图：`images/web-ui.png`
- 演示视频：`videos/demo.mp4`

素材命名与格式规范见 [OPEN_SOURCE.md](OPEN_SOURCE.md) 的「项目展示」一节。

## 硬件清单

| 部件 | 数量 | 说明 |
|---|---|---|
| ESP32 开发板 | 1 | 支持 WiFi，刷入 MicroPython |
| 180° 舵机 | 8 | 四足，每条腿 2 个自由度 |
| HC-SR04 | 1 | 超声波测距 |
| 5V 电源 | 1 | 建议 5V / 3A 以上 |
| 电阻 | 2 或 3 个 | ECHO 分压：1kΩ + 2kΩ，或 3 个 10kΩ |
| 电解电容 | 1 | 100µF，并联在舵机电源端 |

## 快速开始

### 1. 刷入固件

给 ESP32 刷入 MicroPython 固件，确认串口可以进入 REPL。

### 2. 上传文件

将以下文件上传到开发板根目录：

```text
main.py
quad.py
oscillator.py
robot_wifi.py
scanner.py
index.html
```

`test_servo180.py`、`images/`、`videos/` 和文档文件不需要上传到开发板。

### 3. 配置 WiFi

默认使用 AP 模式，配置在 `main.py` 顶部：

```python
AP_SSID = "Otto"
AP_PASSWORD = "88889999"
IFCONFIG = ("192.168.2.182", "255.255.255.0", "192.168.2.1", "8.8.8.8")
```

手机连接热点 `Otto`（密码 `88889999`），浏览器访问：

```text
http://192.168.2.182
```

如需连接路由器，取消 `main.py` 中 `create_connect_route(...)` 的注释，
并填写 `WIFI_SSID` 和 `WIFI_PASSWORD`。

## 接线

### 8 个舵机

```python
SERVO_PINS = (12, 16, 25, 18, 15, 17, 26, 19)
```

顺序为：前右髋、前左髋、前右腿、前左腿、后右髋、后左髋、后右腿、后左腿。

### HC-SR04 超声波

| HC-SR04 | 接到 ESP32 |
|---|---|
| VCC | 5V |
| GND | GND（与 ESP32 共地） |
| TRIG | GPIO 32 |
| ECHO | 分压到 3.3V 后接 GPIO 34 |

ECHO 输出为 5V，必须分压。例如：

```text
ECHO ──[1kΩ]──┬──► GPIO34
              │
            [2kΩ]
              │
             GND
```

完整引脚表、10kΩ 分压方案、接线步骤和检查清单见 **[WIRING.md](WIRING.md)**。

## 使用说明

- 左侧方向键控制移动，中间圆点回中。
- 右侧按钮触发预设动作。
- 下方平面图显示超声波数据：绿色射线为探测方向，红点为障碍物。
- 机器人执行动作时会阻塞 HTTP 服务，动作结束后平面图自动恢复更新。

## HTTP 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 网页控制界面 |
| GET | `/scan` | 超声波测距数据（JSON） |
| POST | `/control` | 执行动作 |

执行动作：

```bash
curl -X POST http://192.168.2.182/control \
  -H "Content-Type: application/json" \
  -d '{"command": "forward"}'
```

返回：

```json
{"status": "200", "msg": "forward"}
```

获取测距数据：

```bash
curl http://192.168.2.182/scan
```

```json
{
  "angle": 90,
  "distance": 62.3,
  "min_angle": 90,
  "max_angle": 90,
  "max_cm": 200,
  "points": [[90, 62.3]]
}
```

`distance` 为 `null` 表示无回波或超出量程。可调用的动作包括：

```text
home  forward  backward  turn_L  turn_R  hello  omni_walk
moonwalk_L  dance  up_down  push_up  front_back  wave_hand
hide  scared  walk  walk1
```

## 项目结构

```text
esp32-quadruped/
├── main.py              # 入口：引脚配置、初始化、启动 WiFi 与 HTTP 服务
├── quad.py              # 四足运动库与动作实现
├── oscillator.py        # 舵机 PWM 驱动与正弦振荡器
├── robot_wifi.py        # WiFi 连接、HTTP 路由、命令执行
├── scanner.py           # HC-SR04 测距与障碍点缓存
├── index.html           # 网页控制界面与 Canvas 平面图
├── test_servo180.py     # 单舵机接线/角度测试
├── robot.py             # 遗留基类，当前未使用，可删除
├── WIRING.md            # 接线说明与检查清单
├── OPEN_SOURCE.md       # 完整开源说明
├── README.md            # 项目入口文档
├── LICENSE              # Apache License 2.0
└── images/
    └── quad-wiring.jpeg # 舵机接线图
```

## 参数配置

| 参数 | 位置 | 默认值 |
|---|---|---|
| `SERVO_PINS` | `main.py` | `(12, 16, 25, 18, 15, 17, 26, 19)` |
| `TRIG_PIN` / `ECHO_PIN` | `main.py` | `32` / `34` |
| `MAX_DISTANCE_CM` | `scanner.py` | `200` |
| `MEASURE_INTERVAL_MS` | `scanner.py` | `100` |
| `SCAN_POLL_MS` | `index.html` | `400` |

新增动作时，在 `quad.py` 中添加无参方法，并在 `index.html` 中添加
**id 与方法名相同**的按钮即可。

## 常见问题

**网页打不开**

确认手机已连接热点 `Otto` 或与 ESP32 在同一路由器下，并访问串口打印的 IP。

**舵机抖动或 ESP32 复位**

多为舵机供电不足。建议舵机单独 5V 供电、与 ESP32 共地，并加 100µF 电容。

**超声波一直无回波**

检查 VCC 是否接 5V、TRIG/ECHO 是否接反、ECHO 是否经过分压、是否共地。

**动作时网页无响应**

动作阻塞执行属于正常现象，动作结束后恢复。

更多问题见 [OPEN_SOURCE.md](OPEN_SOURCE.md) 的「常见问题」一节。

## 相关链接

- Arduino WiFi 版本：<https://github.com/AniPython/quad-arduino-wifi>
- 项目视频：<https://www.bilibili.com/video/BV1vePeepEV4/>
- 商品页面：<https://mobile.yangkeduo.com/goods2.html?goods_id=703833751916>

## 许可证

仓库根目录的 `LICENSE` 为 **Apache License 2.0**。

需要注意：`oscillator.py` 顶部保留了上游 GPL 声明（Oscillator.pde / OttoDIY），
`quad.py` 也基于 OttoDIY 项目整理。公开发布前请确认上游许可证与 Apache-2.0
的兼容性，并保留原始版权声明。详见 [OPEN_SOURCE.md](OPEN_SOURCE.md) 的
「许可证与致谢」一节。
