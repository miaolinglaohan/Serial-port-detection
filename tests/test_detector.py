import unittest
from detector.algorithms import evaluate_data_payload, crc16_modbus, calculate_ascii_score
from detector.serial_utils import COMMON_BAUDRATES, get_available_ports
from detector.engine import DetectionEngine

class TestSerialDetector(unittest.TestCase):

    def test_ascii_scoring(self):
        # 纯 ASCII 文本测试
        ascii_bytes = b"Hello, World!\r\nSystem initialized successfully."
        res = evaluate_data_payload(ascii_bytes)
        self.assertGreater(res['score'], 80.0)
        self.assertEqual(res['protocol'], "ASCII Text")

    def test_modbus_rtu_scoring(self):
        # 组装有效 Modbus RTU 读 Holding Register 响应帧
        # Slave 01, Func 03, ByteCount 02, Data 00 05, CRC16
        raw_frame = bytes([0x01, 0x03, 0x02, 0x00, 0x05])
        crc = crc16_modbus(raw_frame)
        full_frame = raw_frame + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        
        res = evaluate_data_payload(full_frame)
        self.assertEqual(res['score'], 100.0)
        self.assertIn("Modbus RTU", res['protocol'])

    def test_nmea_scoring(self):
        nmea_bytes = b"$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
        res = evaluate_data_payload(nmea_bytes)
        self.assertEqual(res['score'], 98.0)
        self.assertIn("NMEA", res['protocol'])

    def test_at_response_scoring(self):
        at_bytes = b"\r\nOK\r\nWIFI CONNECTED\r\n"
        res = evaluate_data_payload(at_bytes)
        self.assertGreaterEqual(res['score'], 90.0)

    def test_baudrates_list(self):
        self.assertIn(9600, COMMON_BAUDRATES)
        self.assertIn(115200, COMMON_BAUDRATES)

    def test_available_ports(self):
        ports = get_available_ports()
        self.assertIsInstance(ports, list)

if __name__ == '__main__':
    unittest.main()
