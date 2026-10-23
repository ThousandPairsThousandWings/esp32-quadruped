# 简版四足机器人开源说明

基于 ESP32 与 MicroPython 的八舵机四足机器人，包含网页遥控、动作库和超声波测距平面图。
本文档面向首次接触本项目的开发者，说明硬件、接线、软件结构、使用方法、接口和二次开发方式。

---

## 1. 项目概述

本项目运行在 ESP32 上，使用 MicroPython 编写：

- 8 个 180° 舵机构成四足，每条腿 2 个自由度（髋关节 + 小腿）。
- ESP32 开启 WiFi，内置 HTTP 服务器，手机或电脑用浏览器即可控制。
- HC-SR04 超声波模块固定朝前测距，网页在控制按钮下方绘制平面图，用红点标记障碍物。

核心设计是把每个舵机的运动抽象为正弦振荡：

```text
舵机角度 = 偏移 O + 振幅 A × sin(相位 Ph + 时间相位)
```

改变 8 个舵机的 A、O、T、Ph 四个参数，就能组合出前进、转向、跳舞等动作。

### 1.1 项目展示

图片统一放在 `images/`，视频放在 `videos/`。对应文件添加后即可正常显示。

**整机与接线**

![四足机器人整机](images/robot.jpg)

![舵机接线图](images/quad-wiring.jpeg)

**网页控制界面**

![网页控制界面](images/web-ui.png)

![超声波平面图](images/ultrasonic.png)

**演示视频**

- [整机动作演示](videos/demo.mp4)
- [超声波测距演示](videos/ultrasonic-demo.mp4)

> GitHub 的 Markdown 不支持直接内嵌播放仓库里的 MP4，点击链接即可播放或下载。
> 如果希望 README 中自动播放，可额外放一个短 GIF：`images/demo.gif`。

### 1.2 媒体文件规范

| 类型 | 目录 | 推荐文件名 | 说明 |
|---|---|---|---|
| 整机照片 | `images/` | `robot.jpg` | 封面图，建议 16:9 或 4:3 |
| 接线图 | `images/` | `quad-wiring.jpeg` | 已存在 |
| 网页截图 | `images/` | `web-ui.png` | 展示按钮与平面图 |
| 超声波截图 | `images/` | `ultrasonic.png` | 正前方有障碍物时截图 |
| 动图预览 | `images/` | `demo.gif` | 5~10 秒，建议小于 10MB |
| 演示视频 | `videos/` | `demo.mp4` | 整机动作，30~60 秒 |
| 超声波演示 | `videos/` | `ultrasonic-demo.mp4` | 展示红点随距离变化 |

命名要求：

- 全部使用小写英文、数字和连字符，例如 `ultrasonic-demo.mp4`。
- 不要使用中文、空格、`#`、`?` 等字符，避免链接失效。
- 视频统一使用 MP4（H.264 + AAC），720p 或 1080p。
- 单个文件建议小于 50MB；GitHub 单文件上限为 100MB。
- 超过 100MB 的视频放到 GitHub Releases 或 B 站，再在文档中放外链。

---

## 2. 功能特性

- 网页方向控制：前进、后退、左转、右转、回中。
- 10 个动作按钮：Hello、OmniWalk、Moonwalk、Dance、UpDown、PushUp、FrontBack、WaveHand、Hide、Scared。
- 支持 AP 热点模式与 STA 路由模式。
- 超声波实时测距，网页每 400ms 刷新一次平面图。
- 障碍物以红色发光点显示，距离圈为 50/100/150/200cm。
- HTTP 接口可被脚本或其他设备直接调用。

---

## 3. 硬件要求

| 部件 | 说明 |
|---|---|
| 主控 | ESP32 开发板（需支持 WiFi，刷入 MicroPython 固件） |
| 舵机 | 8 个 180° 舵机（具体型号按整机配置） |
| 超声波模块 | HC-SR04 |
| 电源 | 5V 电源，需满足 8 个舵机的峰值电流 |
| 电阻 | 1kΩ + 2kΩ，或 3 个 10kΩ（用于 ECHO 分压） |
| 其他 | 杜邦线、电池盒、100µF 电解电容（建议） |

---

## 4. 接线说明

完整接线清单、操作步骤和上电检查见 **[WIRING.md](WIRING.md)**。

### 4.1 舵机引脚

`main.py` 中的默认配置：

```python
SERVO_PINS = (12, 16, 25, 18, 15, 17, 26, 19)
```

| 序号 | 位置 | GPIO |
|---|---|---|
| 0 | 前右髋 | 12 |
| 1 | 前左髋 | 16 |
| 2 | 前右腿 | 25 |
| 3 | 前左腿 | 18 |
| 4 | 后右髋 | 15 |
| 5 | 后左髋 | 17 |
| 6 | 后右腿 | 26 |
| 7 | 后左腿 | 19 |

接线前可用 `test_servo180.py` 逐个确认舵机方向和零点。

### 4.2 超声波引脚

| HC-SR04 | 接到 ESP32 |
|---|---|
| VCC | 5V |
| GND | GND（与 ESP32 共地） |
| TRIG | GPIO 32 |
| ECHO | 分压到 3.3V 后接 GPIO 34 |

ECHO 输出为 5V，不能直接接 ESP32 的 GPIO。分压电路：

```text
ECHO ──[1kΩ]──┬──► GPIO34
              │
            [2kΩ]
              │
             GND
```

只有 10kΩ 电阻时：

```text
ECHO ──[10kΩ]──┬──► GPIO34
               │
            [10kΩ]
               │
            [10kΩ]
               │
              GND
```

分压后约为 3.33V，在 ESP32 的安全输入范围内。

### 4.3 供电

- 舵机和 HC-SR04 使用 5V，ESP32 建议单独 USB 供电或使用稳压模块。
- **所有设备必须共地**，否则舵机信号和超声波信号都不稳定。
- 8 个舵机同时启动时电流较大，建议电源端并联 100µF 电容，必要时舵机单独供电。

---

## 5. 软件结构

| 文件 | 职责 |
|---|---|
| `main.py` | 配置引脚和 WiFi，初始化机器人、超声波模块与 HTTP 服务 |
| `quad.py` | 四足运动库，包含步态与动作实现 |
| `oscillator.py` | 舵机 PWM 驱动与正弦振荡器 |
| `robot_wifi.py` | WiFi 连接、HTTP 路由、命令执行 |
| `scanner.py` | HC-SR04 测距与障碍点缓存 |
| `index.html` | 网页控制界面与 Canvas 平面图 |
| `test_servo180.py` | 单舵机测试脚本 |
| `robot.py` | 通用基类，当前未使用，可删除 |
| `images/` | 图片与 GIF（整机、接线、网页截图） |
| `videos/` | 演示视频（MP4） |
| `WIRING.md` | 完整接线说明、步骤与上电检查清单 |

数据流：

```text
网页按钮
   │  POST /control {"command": "forward"}
   ▼
RobotWifi._handle_command
   │  按命令名调用机器人方法
   ▼
Quad.forward → Oscillator → PWM → 舵机

HC-SR04 → UltrasonicScanner.update
   │  保存距离
   ▼
GET /scan → 网页 Canvas → 红点
```

---

## 6. 快速开始

### 6.1 刷入固件

给 ESP32 刷入 MicroPython 固件，确认串口可以进入 REPL。

### 6.2 上传文件

至少上传以下文件到开发板根目录：

```text
main.py
quad.py
oscillator.py
robot_wifi.py
scanner.py
index.html
```

`test_servo180.py`、`images/` 和 `videos/` 仅用于调试与展示，不需要上传到开发板。

### 6.3 配置 WiFi

默认使用 AP 模式：

```python
AP_SSID = "Otto"
AP_PASSWORD = "88889999"
IFCONFIG = ("192.168.2.182", "255.255.255.0", "192.168.2.1", "8.8.8.8")
```

手机连接热点 `Otto` 后，浏览器访问 `http://192.168.2.182`。

如使用路由模式，取消 `main.py` 中 `create_connect_route` 的注释：

```python
robot_wifi.create_connect_route(ssid=WIFI_SSID,
                                password=WIFI_PASSWORD,
                                ifconfig=IFCONFIG)
```

### 6.4 上电运行

复位后串口会打印 IP 地址，浏览器打开该地址即可看到控制界面。

---

## 7. 网页使用

- 左侧方向键控制前进、后退、左转、右转，中间圆点为回中。
- 右侧按钮触发预设动作。
- 下方平面图显示超声波数据：
  - 绿色射线：当前探测方向（固定正前方）。
  - 红点：检测到的障碍物。
  - 距离圈：50/100/150/200cm。
  - 顶部文字：当前距离与障碍点数量。

机器人执行动作时会阻塞 HTTP 服务，动作结束后平面图恢复更新。

---

## 8. HTTP 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 返回控制网页 |
| GET | `/scan` | 返回超声波数据 |
| POST | `/control` | 执行动作 |

### 8.1 获取测距数据

```bash
curl http://192.168.2.182/scan
```

返回示例：

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

- `distance` 为 `null` 表示当前无回波或超出量程。
- `points` 为网页可直接绘制的 `[角度, 距离]` 列表。
- 当前超声波固定朝前，所以角度恒为 90。

### 8.2 执行动作

```bash
curl -X POST http://192.168.2.182/control \
  -H "Content-Type: application/json" \
  -d '{"command": "forward"}'
```

成功返回：

```json
{"status": "200", "msg": "forward"}
```

可调用 `quad.py` 中任意无参公共方法，例如：

```text
home  forward  backward  turn_L  turn_R  hello  omni_walk
moonwalk_L  dance  up_down  push_up  front_back  wave_hand
hide  scared  walk  walk1
```

以 `_` 开头的方法和不存在的方法会被拒绝。

---

## 9. 可调参数

### 9.1 `main.py`

| 参数 | 作用 |
|---|---|
| `SERVO_PINS` | 8 个舵机引脚顺序 |
| `TRIG_PIN` / `ECHO_PIN` | 超声波引脚 |
| `AP_SSID` / `AP_PASSWORD` | AP 热点名称和密码 |
| `IFCONFIG` | 固定 IP、掩码、网关、DNS |
| `WIFI_SSID` / `WIFI_PASSWORD` | 路由模式下的 WiFi 信息 |

### 9.2 `scanner.py`

| 参数 | 默认值 | 作用 |
|---|---|---|
| `MAX_DISTANCE_CM` | 200 | 超过该距离视为无效 |
| `MEASURE_INTERVAL_MS` | 100 | 测量间隔 |
| `ECHO_TIMEOUT_US` | 30000 | 回波超时时间 |
| `CLEAR_AFTER_MISSES` | 10 | 连续无回波多少次后清除红点 |

### 9.3 `index.html`

| 参数 | 默认值 | 作用 |
|---|---|---|
| `SCAN_POLL_MS` | 400 | 网页请求测距数据的间隔 |
| `maxRangeCm` | 200 | 平面图最大显示距离 |

---

## 10. 二次开发

### 10.1 新增动作

1. 在 `quad.py` 的 `Quad` 类中新增无参方法：

```python
def nod(self, steps=2, t=800):
    amplitude = [10, 10, 0, 0, 10, 10, 0, 0]
    offset = [0, 0, 0, 0, 0, 0, 0, 0]
    period = [t] * self._servo_totals
    phase = [0, 0, 0, 0, 0, 0, 0, 0]
    self._execute(amplitude, offset, period, phase, steps)
```

2. 在 `index.html` 的动作区新增按钮，**id 必须与方法名一致**：

```html
<div class="button" id="nod">Nod</div>
```

网页按钮通过 `button.id` 作为命令发送，不需要额外注册。

### 10.2 新增接口

在 `robot_wifi.py` 的 `_handle_request` 中增加路径判断，并实现对应的处理方法。
返回网页数据时优先使用 `_json_response`。

### 10.3 恢复云台扫描

当前版本为固定朝前测距。若需要左右扫描，可重新加入 SG90 舵机，
按角度步进测量并维护多组 `(angle, distance)` 点，`/scan` 的数据结构无需改变。

---

## 11. 常见问题

**网页打不开**

- 确认手机/电脑已连接热点 `Otto`，或与 ESP32 在同一路由器下。
- 确认访问的 IP 与串口打印一致。
- 路由器网段与 `IFCONFIG` 不一致时，固定 IP 可能无法访问。

**舵机抖动或 ESP32 复位**

- 舵机供电不足，建议单独 5V 供电并共地。
- 电源端增加 100µF 电容。
- 避免舵机堵转。

**超声波一直显示“无回波”**

- 检查 VCC 是否接 5V。
- 检查 TRIG/ECHO 是否接反。
- 检查 ECHO 分压是否接对，GPIO34 是否接到分压中点。
- 障碍物太近（小于 2cm）或太远（大于 200cm）也会视为无效。

**红点位置与实际方向相反**

- 超声波模块安装方向与代码假设相反。可调整 `index.html` 中
  `(angle - 90)` 为 `(90 - angle)`。

**动作执行时网页无响应**

- 动作是阻塞执行的，属于正常现象。动作结束后自动恢复。

**修改网页后仍显示旧界面**

- 浏览器可能缓存了页面，强制刷新或清除缓存。

---

## 12. 安全注意事项

- 接线、改线前务必断电。
- HC-SR04 的 ECHO 是 5V 输出，**必须分压**，直接接 GPIO 可能损坏 ESP32。
- 调试动作时把机器人架空，避免舵机堵转或机器人跌落。
- 不要将金属物体、液体靠近电路板。
- 使用大容量电池时注意正负极和短路保护。

---

## 13. 参与贡献

欢迎提交 Issue 和 Pull Request：

1. Fork 本仓库并从 `main` 创建分支。
2. 保持现有代码风格：MicroPython 兼容、模块化、中文注释。
3. 提交前在真实硬件上验证舵机动作和网页显示。
4. PR 描述中写明改动内容、硬件型号和测试结果。
5. 不要提交个人 WiFi 密码、IP 配置等敏感信息。

适合贡献的方向：

- 新增步态/动作
- 超声波滤波与多点建图
- 网页 UI 与移动端适配
- 文档翻译与接线图完善

---

## 14. 许可证与致谢

仓库根目录的 `LICENSE` 为 **Apache License 2.0**。

需要特别说明：

- `oscillator.py` 顶部保留了上游 GPL 声明（Oscillator.pde / OttoDIY）。
- `quad.py` 基于 OttoDIY 项目整理。

如果计划公开分发，请先确认上游代码的许可证与 Apache-2.0 是否兼容，
并保留原始版权与来源声明。详细条款以各文件头部注释和 `LICENSE` 为准。

相关链接：

- Arduino WiFi 版本：<https://github.com/AniPython/quad-arduino-wifi>
- 项目视频：<https://www.bilibili.com/video/BV1vePeepEV4/>
- 商品页面：<https://mobile.yangkeduo.com/goods2.html?goods_id=703833751916>

---

## 15. 项目状态

当前版本为可运行的教学/DIY 版本，重点在易读、易改和可复现。
超声波部分为固定朝前测距，不包含完整 SLAM 或路径规划。
