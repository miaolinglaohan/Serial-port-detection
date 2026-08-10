import serial
import serial.tools.list_ports
from typing import List, Dict, Tuple

# 常用标准与高速波特率列表
COMMON_BAUDRATES = [
    9600, 115200, 19200, 38400, 57600, 4800, 2400, 1200,
    230400, 460800, 921600, 1500000, 2000000, 76800, 14400
]

# 全量可选波特率
ALL_BAUDRATES = [
    300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 
    38400, 57600, 76800, 115200, 128000, 230400, 256000, 
    460800, 921600, 1000000, 1500000, 2000000, 3000000
]

# 校验位选项
PARITY_OPTIONS = {
    'None (N)': serial.PARITY_NONE,
    'Even (E)': serial.PARITY_EVEN,
    'Odd (O)': serial.PARITY_ODD,
    'Mark (M)': serial.PARITY_MARK,
    'Space (S)': serial.PARITY_SPACE,
}

# 数据位
DATABITS_OPTIONS = [8, 7, 6, 5]

# 停止位
STOPBITS_OPTIONS = {
    '1': serial.STOPBITS_ONE,
    '1.5': serial.STOPBITS_ONE_POINT_FIVE,
    '2': serial.STOPBITS_TWO,
}

def get_available_ports() -> List[Dict[str, str]]:
    """获取当前系统可用的串口列表及详细描述"""
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append({
            'device': port.device,
            'description': port.description,
            'hwid': port.hwid,
            'display': f"{port.device} - {port.description}"
        })
    return ports

def test_serial_open(port: str, baudrate: int, parity=serial.PARITY_NONE, 
                     bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, 
                     timeout=0.2) -> Tuple[bool, str]:
    """测试指定参数串口是否可正常打开"""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=parity,
            bytesize=bytesize,
            stopbits=stopbits,
            timeout=timeout
        )
        ser.close()
        return True, "Success"
    except Exception as e:
        return False, str(e)
