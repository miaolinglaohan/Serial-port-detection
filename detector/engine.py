import time
import threading
import serial
from typing import List, Dict, Any, Callable, Optional
from .serial_utils import COMMON_BAUDRATES, PARITY_OPTIONS, DATABITS_OPTIONS, STOPBITS_OPTIONS
from .algorithms import evaluate_data_payload

# 预设的常用主动探针列表
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
        """停止探测流程"""
        self._stop_event.set()

    def is_running(self) -> bool:
        """检查探测是否在运行中"""
        return self._thread is not None and self._thread.is_alive()

    def start_detection_async(
        self,
        port: str,
        mode: str = "auto",  # 'passive', 'active', 'auto'
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
        """在后台线程启动串口黑盒探测"""
        if self.is_running():
            return False

        self._stop_event.clear()
        
        bauds = baudrates if baudrates else COMMON_BAUDRATES
        pars = parities if parities else ['None (N)', 'Even (E)', 'Odd (O)']
        dbits = databits if databits else [8]
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

        log(f"🚀 开始串口黑盒探测: {port} | 模式: {mode.upper()}")
        
        # 准备探针列表
        probes = list(DEFAULT_PROBES)
        if custom_probe_hex:
            try:
                hex_clean = custom_probe_hex.replace(" ", "").replace("0x", "")
                custom_bytes = bytes.fromhex(hex_clean)
                probes.insert(0, {"name": "Custom Hex Probe", "data": custom_bytes})
            except Exception as e:
                log(f"⚠️ 自定义 Hex 探针解析失败: {e}")

        # 生成所有参数测试组合
        test_matrix = []
        for b in bauds:
            for p in pars:
                for d in dbits:
                    for s in sbits:
                        test_matrix.append((b, p, d, s))
                        
        total_steps = len(test_matrix)
        results: List[Dict[str, Any]] = []
        best_candidate: Optional[Dict[str, Any]] = None

        for idx, (baud, parity_key, databit, stopbit_key) in enumerate(test_matrix, start=1):
            if self._stop_event.is_set():
                log("🛑 用户中止了探测流程。")
                break

            parity_val = PARITY_OPTIONS.get(parity_key, serial.PARITY_NONE)
            stopbit_val = STOPBITS_OPTIONS.get(stopbit_key, serial.STOPBITS_ONE)
            
            param_desc = f"{baud} bps, {databit}{parity_key[0]}{stopbit_key}"
            if on_progress:
                on_progress(idx, total_steps, param_desc)

            # 打开串口尝试
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
                
                # 1. 被动监听尝试
                if mode in ('passive', 'auto'):
                    t_start = time.time()
                    while (time.time() - t_start) < sample_time:
                        if self._stop_event.is_set():
                            break
                        if ser.in_waiting > 0:
                            received_data += ser.read(ser.in_waiting)
                        time.sleep(0.02)
                    used_mode = 'passive'

                # 2. 如果是主动模式，或者自动模式下被动监听未收到数据
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

            except Exception as e:
                # 某些特定串口卡住或参数不兼容
                if ser and ser.is_open:
                    try:
                        ser.close()
                    except Exception:
                        pass
                continue

            # 评估数据质量
            if received_data:
                eval_res = evaluate_data_payload(received_data)
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
                        'details': eval_res['details'],
                        'sample_hex': eval_res['sample_hex'],
                        'sample_text': eval_res['sample_text'],
                        'bytes_len': len(received_data)
                    }
                    results.append(res_entry)
                    log(f"🎯 [得分 {eval_res['score']:.1f}] 匹配参数: {param_desc} | 协议: {eval_res['protocol']}")
                    
                    if on_result_found:
                        on_result_found(res_entry)
                        
                    # 如果匹配到了 100% 满分的 Modbus 或高置信度协议，提前锁定最佳项
                    if eval_res['score'] >= 98.0:
                        log(f"✅ 已匹配到高置信度目标 ({eval_res['protocol']})，探测完成！")
                        best_candidate = res_entry
                        break

        # 按得分从高到低排序结果
        results.sort(key=lambda x: x['score'], reverse=True)
        log(f"🏁 探测结束！共找到 {len(results)} 个潜在符合的参数组合。")

        if on_complete:
            on_complete(results)
