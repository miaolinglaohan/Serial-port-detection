# 串口黑盒探测小工具 (Serial Port Black-Box Detector)

轻量级、开源且功能强悍的 Python 串口黑盒参数探测与波特率推断小工具。

---

## 🌟 核心亮点与功能

1. **多模式自动探测 (兼顾主动与被动设备)**：
   * **🚀 智能混合模式 (Auto)**：优先静默被动嗅探，若无数据上报则自动切换为主动发送探针问答，兼顾所有串口硬件。
   * **👂 纯被动监听模式 (Passive)**：适用于持续自动吐数据的设备（传感器、GPS、日志上报等），零干扰硬件。
   * **⚡ 主动探针问答模式 (Active)**：适用于问答型设备（Modbus RTU 模组、AT 指令设备等），支持自定义 Hex 探针。

2. **启发式协议分析打分模型**：
   * **Modbus RTU** 自动 CRC16 帧校验逻辑（准确度 100%）。
   * **NMEA 0183 (GPS/GNSS)** 结构解析匹配。
   * **AT 命令响应** (OK/ERROR/READY) 匹配。
   * **ASCII/UTF-8 字符可读比率打分算法**。

3. **现代轻量 UI 界面**：
   * 自动集成现代暗黑主题 UI (CustomTkinter)。
   * 支持内置标准 Tkinter 平滑降级兼容。
   * 包含置信度最高参数推荐 Banner、实时扫描进度条、候选参数分析表格、抓包十六进制 (HEX) 与文本预览。

---

## 🚀 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动应用程序
```bash
python main.py
```

---

## 📦 打包为单文件 executable (.exe)

若需要脱离 Python 环境运行，可使用 `pyinstaller` 进行单文件打包：

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile main.py -n SerialBlackBoxDetector
```
打包完成后在 `dist/` 目录下即可获得轻量独立的 `SerialBlackBoxDetector.exe`。

---

## 📂 项目结构说明

```
Serial-port-detection/
├── main.py                     # 主入口程序
├── requirements.txt            # 项目依赖 (pyserial, customtkinter)
├── README.md                   # 详细使用指南
├── detector/                   # 核心黑盒检测引擎与算法
│   ├── __init__.py
│   ├── serial_utils.py        # 串口可用性与参数组合
│   ├── algorithms.py          # 启发式评估算法 (ASCII/Modbus/NMEA/AT)
│   └── engine.py              # 多线程异步黑盒探测引擎
├── ui/                         # 现代 GUI 交互
│   ├── __init__.py
│   └── app.py                 # Tkinter/CustomTkinter GUI
└── tests/                      # 单元测试
    └── test_detector.py
```
