"""
WiFi 连接与 HTTP 控制服务。

接口:
    GET  /         网页控制界面
    POST /control  执行动作，请求体: {"command": "forward"}
    GET  /scan     超声波测距结果（JSON）
"""

import json
import time

import machine
import network
import usocket as socket


class RobotWifi:
    """把机器人动作和测距数据通过 WiFi 暴露给网页。"""

    def __init__(self, robot, scanner=None, html_path="index.html"):
        self.robot = robot
        self.scanner = scanner
        with open(html_path, "r", encoding="utf-8") as file:
            self.html = file.read()
        self._status_led = None

    # ---------- WiFi ----------

    def create_connect_ap(self, essid, password, ifconfig=None):
        """AP 模式：ESP32 自己创建热点，手机直接连接。"""
        ap = network.WLAN(network.AP_IF)
        if ifconfig:
            ap.ifconfig(ifconfig)
        ap.active(True)
        ap.config(essid=essid, password=password,
                  authmode=network.AUTH_WPA_WPA2_PSK)

        self._enable_status_led()
        ip = ap.ifconfig()[0]
        print("AP IP:", ip)
        return ip

    def create_connect_route(self, ssid, password, ifconfig=None):
        """STA 模式：ESP32 连接路由器，手机与 ESP32 在同一局域网。"""
        wlan = network.WLAN(network.STA_IF)
        if ifconfig:
            wlan.ifconfig(ifconfig)
        wlan.active(True)

        if not wlan.isconnected():
            print("Connecting to WiFi:", ssid)
            wlan.connect(ssid, password)
            while not wlan.isconnected():
                print("Waiting for WiFi...")
                time.sleep(1)

        self._enable_status_led()
        ip = wlan.ifconfig()[0]
        print("Station IP:", ip)
        return ip

    def _enable_status_led(self):
        """点亮板载 LED（GPIO2），表示 WiFi 已就绪。"""
        if self._status_led is None:
            self._status_led = machine.PWM(machine.Pin(2), duty=512)

    # ---------- HTTP 响应 ----------

    @staticmethod
    def _build_response(body, content_type="text/html; charset=utf-8"):
        """构造完整的 HTTP 响应，返回 bytes。"""
        body_bytes = body.encode("utf-8")
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: {}\r\n"
            "Content-Length: {}\r\n"
            "Cache-Control: no-store\r\n"
            "Connection: close\r\n\r\n"
        ).format(content_type, len(body_bytes))
        return headers.encode("utf-8") + body_bytes

    def _json_response(self, payload):
        return self._build_response(json.dumps(payload), "application/json")

    # ---------- 请求处理 ----------

    def _handle_command(self, body):
        """执行网页发来的动作命令，返回状态字典。"""
        try:
            payload = json.loads(body)
        except ValueError:
            return {"status": "400", "msg": "invalid json"}

        command = payload.get("command", "") if isinstance(payload, dict) else ""
        if not isinstance(command, str):
            return {"status": "400", "msg": "command must be a string"}

        action = getattr(self.robot, command, None) if command else None
        if not command or command.startswith("_") or not callable(action):
            return {"status": "400", "msg": "unknown command: " + str(command)}

        try:
            print("Command:", command)
            action()
            return {"status": "200", "msg": command}
        except Exception as error:
            message = "Error executing command: " + str(error)
            print(message)
            return {"status": "500", "msg": message}

    def _handle_scan(self):
        """返回当前超声测距数据。"""
        if not self.scanner:
            return self._json_response({"angle": 90, "distance": None,
                                        "points": [], "max_cm": 200})
        return self._json_response(self.scanner.snapshot())

    def _handle_request(self, client_socket):
        """解析 HTTP 请求并发送响应。"""
        request = client_socket.recv(1024)
        if not request:
            return

        head, _, body = request.decode("utf-8").partition("\r\n\r\n")
        parts = head.split("\r\n")[0].split()
        if len(parts) != 3:
            return

        method, path, _ = parts
        path = path.split("?")[0]

        if method == "POST" and path == "/control":
            response = self._json_response(self._handle_command(body))
        elif method == "GET" and path == "/scan":
            response = self._handle_scan()
        else:
            response = self._build_response(self.html)

        client_socket.send(response)

    # ---------- 服务器 ----------

    def create_server(self, port=80):
        """启动 HTTP 服务器，空闲时持续测量距离。"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", port))
        server_socket.listen(128)
        server_socket.settimeout(0.05)
        print("HTTP server started on port", port)

        while True:
            # 没有请求时测量一次距离，使网页数据持续更新
            if self.scanner:
                self.scanner.update()

            try:
                client_socket, _ = server_socket.accept()
            except OSError:
                continue

            try:
                client_socket.settimeout(1.0)
                self._handle_request(client_socket)
            except Exception as error:
                print("Request error:", error)
            finally:
                client_socket.close()
