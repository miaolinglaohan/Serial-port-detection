import unittest
import threading
from detector.algorithms import evaluate_data_payload, crc16_modbus, calculate_ascii_score
from detector.serial_utils import COMMON_BAUDRATES, get_available_ports
from detector.engine import DetectionEngine
from unittest.mock import patch

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

    def test_available_ports_marks_busy_ports(self):
        class FakePort:
            device = "COM_BUSY"
            description = "Busy test port"
            hwid = "TEST"

        def fake_serial(*args, **kwargs):
            raise PermissionError("Access is denied")

        with patch("detector.serial_utils.serial.tools.list_ports.comports", return_value=[FakePort()]):
            with patch("detector.serial_utils.serial.Serial", side_effect=fake_serial):
                ports = get_available_ports()

        self.assertEqual(ports[0]["device"], "COM_BUSY")
        self.assertTrue(ports[0]["is_busy"])

    def test_stop_interrupts_active_probe_without_data(self):
        class FakeSerial:
            def __init__(self, *args, **kwargs):
                self.is_open = True
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                return len(data)

            def flush(self):
                pass

            def read(self, size=1):
                return b""

            def cancel_read(self):
                pass

            def cancel_write(self):
                pass

            def close(self):
                self.is_open = False

        engine = DetectionEngine()
        first_progress = threading.Event()
        completed = threading.Event()
        progress_calls = []

        def on_progress(current, total, param_desc):
            progress_calls.append(current)
            first_progress.set()

        with patch("detector.engine.serial.Serial", FakeSerial):
            started = engine.start_detection_async(
                port="COM_TEST",
                mode="active",
                baudrates=[9600, 19200, 38400],
                parities=["None (N)"],
                sample_time=1.0,
                on_progress=on_progress,
                on_complete=lambda results: completed.set(),
            )

            self.assertTrue(started)
            self.assertTrue(first_progress.wait(0.5))
            engine.stop()
            self.assertTrue(completed.wait(0.5))
            self.assertLess(len(progress_calls), 3)

if __name__ == '__main__':
    unittest.main()
