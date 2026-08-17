import time
import threading
import serial
from typing import List, Dict, Any, Callable, Optional
from .serial_utils import COMMON_BAUDRATES, PARITY_OPTIONS, DATABITS_OPTIONS, STOPBITS_OPTIONS
from .algorithms import evaluate_data_payload
from .i18n import i18n

DEFAULT_PROBES = [
    {"name": "Newline Probe", "data": b"\r\n"},
    {"name": "AT Probe", "data": b"AT\r\n"},
    {"name": "Modbus Read Probe", "data": bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A])},
    {"name": "Query Symbol Probe", "data": b"?\r\n"},
]

class DetectionEngine:
    """串口黑盒探测核心引擎"""
    
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def stop(self):
        self._stop_event.set()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start_detection_async(
        self,
        port: str,
        mode: str = "auto",
        baudrates: Optional[List[int]] = None,
        parities: Optional[List[str]] = None,
        databits: Optional[List[int]] = None,
        stopbits: Optional[List[str]] = None,
        custom_probe_hex: Optional[str] = None,
        sample_time: float = 0.3,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_result_found: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_complete: Optional[Callable[[List[Dict[str, Any]]], None]] = None,
        on_log: Optional[Callable[[str], None]] = None
    ):
        if self.is_running():
            return False

        self._stop_event.clear()
        
        bauds = baudrates if baudrates else COMMON_BAUDRATES
        pars = parities if parities else ['None (N)', 'Even (E)', 'Odd (O)']
        dbits = databits if databits else [8, 7]  # 默认同时覆盖 8Bit 和 7Bit
        sbits = stopbits if stopbits else ['1']
        
        self._thread = threading.Thread(
            target=self._run_detection,
            args=(port, mode, bauds, pars, dbits, sbits, custom_probe_hex, 
                  sample_time, on_progress, on_result_found, on_complete, on_log),
            daemon=True
        )
        self._thread.start()
        return True

    def _run_detection(
        self, port, mode, bauds, pars, dbits, sbits, custom_probe_hex,
        sample_time, on_progress, on_result_found, on_complete, on_log
    ):
        def log(msg: str):
            if on_log:
                on_log(msg)

        log(i18n.t('log_start_detection', port=port, mode=mode.upper()))
        
        probes = list(DEFAULT_PROBES)
        if custom_probe_hex:
            try:
                hex_clean = custom_probe_hex.replace(" ", "").replace("0x", "")
                custom_bytes = bytes.fromhex(hex_clean)
                probes.insert(0, {"name": "Custom Hex Probe", "data": custom_bytes})
            except Exception as e:
                log(i18n.t('log_probe_hex_err', err=str(e)))

        # 组织扫描矩阵
        test_matrix = []
        for b in bauds:
            for d in dbits:
                for s in sbits:
                    for p in pars:
                        test_matrix.append((b, p, d, s))
                        
        total_steps = len(test_matrix)
        results: List[Dict[str, Any]] = []

        found_high_score_in_baud = False

        for idx, (baud, parity_key, databit, stopbit_key) in enumerate(test_matrix, start=1):
            if self._stop_event.is_set():
                log(i18n.t('log_user_stop'))
                break

            parity_val = PARITY_OPTIONS.get(parity_key, serial.PARITY_NONE)
            stopbit_val = STOPBITS_OPTIONS.get(stopbit_key, serial.STOPBITS_ONE)
            
            param_desc = f"{baud} bps, {databit}{parity_key[0]}{stopbit_key}"
            if on_progress:
                on_progress(idx, total_steps, param_desc)

            ser = None
            received_data = b""
            used_mode = mode
            
            try:
                ser = serial.Serial(
                    port=port,
                    baudrate=baud,
                    parity=parity_val,
                    bytesize=databit,
                    stopbits=stopbit_val,
                    timeout=sample_time
                )
                
                if mode in ('passive', 'auto'):
                    t_start = time.time()
                    while (time.time() - t_start) < sample_time:
                        if self._stop_event.is_set():
                            break
                        if ser.in_waiting > 0:
                            received_data += ser.read(ser.in_waiting)
                        time.sleep(0.02)
                    used_mode = 'passive'

                if (mode == 'active') or (mode == 'auto' and len(received_data) == 0):
                    used_mode = 'active'
                    for probe in probes:
                        if self._stop_event.is_set():
                            break
                        ser.reset_input_buffer()
                        ser.write(probe["data"])
                        ser.flush()
                        
                        t_start = time.time()
                        probe_data = b""
                        while (time.time() - t_start) < (sample_time * 0.8):
                            if ser.in_waiting > 0:
                                probe_data += ser.read(ser.in_waiting)
                            time.sleep(0.01)
                            
                        if len(probe_data) > 0:
                            received_data += probe_data
                            break

                ser.close()

            except Exception:
                if ser and ser.is_open:
                    try:
                        ser.close()
                    except Exception:
                        pass
                continue

            if received_data:
                eval_res = evaluate_data_payload(received_data, parity_key=parity_key)
                if eval_res['score'] > 0:
                    res_entry = {
                        'port': port,
                        'baudrate': baud,
                        'parity': parity_key,
                        'databits': databit,
                        'stopbits': stopbit_key,
                        'param_str': param_desc,
                        'score': eval_res['score'],
                        'protocol': eval_res['protocol'],
                        'mode_used': used_mode,
                        'ascii_ratio': eval_res['ascii_ratio'],
                        'details_key': eval_res.get('details_key', 'detail_ascii_ratio'),
                        'details_kwargs': eval_res.get('details_kwargs', {}),
                        'details': eval_res['details'],
                        'sample_hex': eval_res['sample_hex'],
                        'sample_text': eval_res['sample_text'],
                        'bytes_len': len(received_data)
                    }
                    results.append(res_entry)
                    log(i18n.t('log_found_match', score=f"{eval_res['score']:.1f}", param=param_desc, protocol=eval_res['protocol']))
                    
                    if on_result_found:
                        on_result_found(res_entry)
                        
                    if eval_res['score'] >= 98.0:
                        found_high_score_in_baud = True

        results.sort(key=lambda x: x['score'], reverse=True)
        log(i18n.t('log_complete_summary', count=len(results)))

        if on_complete:
            on_complete(results)
