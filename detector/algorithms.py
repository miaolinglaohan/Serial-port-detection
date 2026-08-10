import math
import re
from typing import Dict, Any
from .i18n import i18n

def crc16_modbus(data: bytes) -> int:
    """计算 Modbus RTU CRC16 校验码"""
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 0x0001) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

def check_modbus_rtu_frame(data: bytes) -> bool:
    """检查数据切片中是否包含有效的 Modbus RTU 响应帧"""
    if len(data) < 4:
        return False
    
    for i in range(len(data) - 3):
        slave_id = data[i]
        func_code = data[i+1]
        if (1 <= slave_id <= 247) and (func_code in [1, 2, 3, 4, 5, 6, 15, 16, 0x81, 0x83]):
            for frame_len in range(4, min(256, len(data) - i + 1)):
                sub = data[i:i+frame_len]
                if len(sub) >= 4:
                    calculated_crc = crc16_modbus(sub[:-2])
                    received_crc = sub[-2] | (sub[-1] << 8)
                    if calculated_crc == received_crc:
                        return True
    return False

def check_nmea_sentence(data_str: str) -> bool:
    """检查是否符合 GPS/GNSS NMEA0183 协议规范 ($GP..., $GN...)"""
    pattern = r'\$(GP|GN|BD|GA|GL)[A-Z]{3},[^*]+\*[0-9A-Fa-f]{2}'
    return bool(re.search(pattern, data_str))

def calculate_ascii_score(data: bytes) -> float:
    """计算可打印 ASCII 字符比例打分 (0.0 - 100.0)"""
    if not data:
        return 0.0
    
    printable_count = 0
    zero_or_ff_count = 0
    
    for byte in data:
        if byte in (0x00, 0xFF):
            zero_or_ff_count += 1
        if 0x20 <= byte <= 0x7E or byte in (0x09, 0x0A, 0x0D):
            printable_count += 1
            
    total = len(data)
    printable_ratio = (printable_count / total) * 100.0
    zero_ratio = (zero_or_ff_count / total) * 100.0
    
    if zero_ratio > 60:
        printable_ratio *= (1 - zero_ratio / 100)
        
    return round(printable_ratio, 2)

def bytes_to_safe_ascii(data: bytes) -> str:
    """把 bytes 转为安全的 ASCII 点阵显示，不可打印字符用 '.' 替代"""
    res = []
    for b in data:
        if 0x20 <= b <= 0x7E:
            res.append(chr(b))
        elif b == 0x0D:
            res.append('\\r')
        elif b == 0x0A:
            res.append('\\n')
        else:
            res.append('.')
    return "".join(res)

def evaluate_data_payload(data: bytes) -> Dict[str, Any]:
    """多维度打分评估模型，返回特征分析结果与综合综合置信度得分 (0-100)"""
    if not data:
        return {
            'score': 0.0,
            'protocol': 'No Data',
            'ascii_ratio': 0.0,
            'details_key': 'detail_no_data',
            'details_kwargs': {},
            'details': i18n.t('detail_no_data')
        }
        
    ascii_score = calculate_ascii_score(data)
    is_modbus = check_modbus_rtu_frame(data)
    
    text_content = ""
    is_utf8 = False
    if ascii_score > 40.0:
        try:
            text_content = data.decode('utf-8')
            is_utf8 = True
        except UnicodeDecodeError:
            try:
                text_content = data.decode('gbk', errors='ignore')
            except Exception:
                text_content = ""
            
    is_nmea = check_nmea_sentence(text_content) if text_content else False
    is_at_resp = bool(re.search(r'\b(OK|ERROR|READY|WIFI|CONNECTED|AT\+)\b', text_content, re.IGNORECASE)) if text_content else False

    final_score = ascii_score
    protocol_type = "Raw Data / Unknown"
    details_key = "detail_ascii_ratio"
    details_kwargs = {"ratio": ascii_score}

    if is_modbus:
        final_score = 100.0
        protocol_type = "Modbus RTU (CRC16 Valid)"
        details_key = "detail_modbus"
        details_kwargs = {}
        safe_str = bytes_to_safe_ascii(data[:64])
        sample_text_display = f"{i18n.t('sample_modbus_tag')} {safe_str}"
    elif is_nmea:
        final_score = 98.0
        protocol_type = "NMEA 0183 (GPS)"
        details_key = "detail_nmea"
        details_kwargs = {}
        sample_text_display = text_content[:128].replace('\r', '\\r').replace('\n', '\\n') if text_content else bytes_to_safe_ascii(data[:64])
    elif is_at_resp:
        final_score = max(ascii_score, 90.0)
        protocol_type = "AT Command Response"
        details_key = "detail_at"
        details_kwargs = {}
        sample_text_display = text_content[:128].replace('\r', '\\r').replace('\n', '\\n') if text_content else bytes_to_safe_ascii(data[:64])
    elif is_utf8 and ascii_score > 85.0:
        protocol_type = "ASCII Text"
        details_key = "detail_ascii"
        details_kwargs = {}
        sample_text_display = text_content[:128].replace('\r', '\\r').replace('\n', '\\n')
    else:
        sample_text_display = f"{i18n.t('sample_binary_tag')} {bytes_to_safe_ascii(data[:64])}"

    return {
        'score': round(final_score, 1),
        'protocol': protocol_type,
        'ascii_ratio': ascii_score,
        'details_key': details_key,
        'details_kwargs': details_kwargs,
        'details': i18n.t(details_key, **details_kwargs),
        'sample_hex': data[:64].hex(' ').upper(),
        'sample_text': sample_text_display
    }
