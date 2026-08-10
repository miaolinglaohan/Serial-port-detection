import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List
import serial

try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

from detector.serial_utils import get_available_ports, COMMON_BAUDRATES, ALL_BAUDRATES, PARITY_OPTIONS
from detector.engine import DetectionEngine

class SerialDetectorApp:
    """串口黑盒探测小工具 GUI 主界面"""

    def __init__(self):
        self.engine = DetectionEngine()
        self.results_data: List[Dict[str, Any]] = []

        if HAS_CTK:
            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()

        self.root.title("串口黑盒探测小工具 v1.0 (Serial Port Black-Box Detector)")
        self.root.geometry("1000 Granger 720".replace("Granger", "x"))
        self.root.minsize(850, 600)

        self._setup_ui()
        self.refresh_ports()

    def _setup_ui(self):
        # 主网格布局
        if HAS_CTK:
            self.main_frame = ctk.CTkFrame(self.root, corner_radius=10)
            self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        else:
            self.main_frame = ttk.Frame(self.root, padding=10)
            self.main_frame.pack(fill="both", expand=True)

        # 1. 顶部控制栏 (串口选择, 模式选择, 启动/停止按钮)
        self._build_top_controls()

        # 2. 中部面板 (左侧参数筛选与探针配置, 右侧最佳检测结果卡片与表格)
        self._build_middle_panel()

        # 3. 底部面板 (样本 Hex/Text 预览 + 日志输出)
        self._build_bottom_panel()

    def _build_top_controls(self):
        if HAS_CTK:
            control_frame = ctk.CTkFrame(self.main_frame, corner_radius=8)
            control_frame.pack(fill="x", padx=10, pady=(10, 5))
            
            # 串口选择
            label_port = ctk.CTkLabel(control_frame, text="选择串口:", font=("Microsoft YaHei", 12, "bold"))
            label_port.pack(side="left", padx=(15, 5), pady=10)
            
            self.combo_ports = ctk.CTkOptionMenu(control_frame, width=220, values=["扫描串口中..."])
            self.combo_ports.pack(side="left", padx=5, pady=10)
            
            btn_refresh = ctk.CTkButton(control_frame, text="🔄 刷新", width=70, command=self.refresh_ports)
            btn_refresh.pack(side="left", padx=5, pady=10)
            
            # 模式选择器 (兼顾两者)
            label_mode = ctk.CTkLabel(control_frame, text="探测模式:", font=("Microsoft YaHei", 12, "bold"))
            label_mode.pack(side="left", padx=(20, 5), pady=10)
            
            self.combo_mode = ctk.CTkOptionMenu(
                control_frame, 
                width=190, 
                values=["🚀 智能混合模式", "👂 纯被动监听模式", "⚡ 主动探针问答模式"]
            )
            self.combo_mode.set("🚀 智能混合模式")
            self.combo_mode.pack(side="left", padx=5, pady=10)
            
            # 启动/停止按钮
            self.btn_start = ctk.CTkButton(
                control_frame, 
                text="▶️ 开始黑盒探测", 
                fg_color="#2b8a3e", 
                hover_color="#216e31",
                font=("Microsoft YaHei", 13, "bold"),
                width=140,
                command=self.toggle_detection
            )
            self.btn_start.pack(side="right", padx=15, pady=10)
        else:
            control_frame = ttk.LabelFrame(self.main_frame, text=" 控制面板 ", padding=10)
            control_frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(control_frame, text="选择串口:").pack(side="left", padx=5)
            self.combo_ports = ttk.Combobox(control_frame, width=25, state="readonly")
            self.combo_ports.pack(side="left", padx=5)
            
            btn_refresh = ttk.Button(control_frame, text="刷新", command=self.refresh_ports)
            btn_refresh.pack(side="left", padx=5)
            
            ttk.Label(control_frame, text="探测模式:").pack(side="left", padx=(15, 5))
            self.combo_mode = ttk.Combobox(
                control_frame, 
                values=["🚀 智能混合模式", "👂 纯被动监听模式", "⚡ 主动探针问答模式"], 
                state="readonly",
                width=18
            )
            self.combo_mode.current(0)
            self.combo_mode.pack(side="left", padx=5)
            
            self.btn_start = ttk.Button(control_frame, text="开始黑盒探测", command=self.toggle_detection)
            self.btn_start.pack(side="right", padx=5)

    def _build_middle_panel(self):
        if HAS_CTK:
            mid_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            mid_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # 左侧参数配置区
            left_config = ctk.CTkFrame(mid_frame, width=250)
            left_config.pack(side="left", fill="y", padx=(0, 5), pady=5)
            
            ctk.CTkLabel(left_config, text="⚙️ 探测扫描范围设置", font=("Microsoft YaHei", 13, "bold")).pack(anchor="w", padx=10, pady=10)
            
            # 波特率组合框
            self.use_common_bauds = ctk.CTkCheckBox(left_config, text="仅扫描常见波特率(推荐)", onvalue=1, offvalue=0)
            self.use_common_bauds.select()
            self.use_common_bauds.pack(anchor="w", padx=10, pady=5)
            
            # 校验位筛选
            ctk.CTkLabel(left_config, text="校验位 (Parity):", font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
            self.chk_parity_n = ctk.CTkCheckBox(left_config, text="None (N)", onvalue=1, offvalue=0)
            self.chk_parity_n.select()
            self.chk_parity_n.pack(anchor="w", padx=15, pady=2)
            self.chk_parity_e = ctk.CTkCheckBox(left_config, text="Even (E)", onvalue=1, offvalue=0)
            self.chk_parity_e.select()
            self.chk_parity_e.pack(anchor="w", padx=15, pady=2)
            self.chk_parity_o = ctk.CTkCheckBox(left_config, text="Odd (O)", onvalue=1, offvalue=0)
            self.chk_parity_o.select()
            self.chk_parity_o.pack(anchor="w", padx=15, pady=2)
            
            # 自定义探针 HEX
            ctk.CTkLabel(left_config, text="自定义探针 Hex (可选):", font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=(15, 2))
            self.entry_custom_hex = ctk.CTkEntry(left_config, placeholder_text="例如: 01 03 00 00 00 01")
            self.entry_custom_hex.pack(fill="x", padx=10, pady=5)
            
            # 采样等待时间
            ctk.CTkLabel(left_config, text="单项采样微调(秒):", font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
            self.slider_sample_time = ctk.CTkSlider(left_config, from_=0.1, to=1.0, number_of_steps=9)
            self.slider_sample_time.set(0.3)
            self.slider_sample_time.pack(fill="x", padx=10, pady=5)
            
            # 右侧展示区 (最佳卡片 + 表格)
            right_display = ctk.CTkFrame(mid_frame)
            right_display.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=5)
            
            # 最佳匹配推荐 Banner
            self.card_best = ctk.CTkFrame(right_display, fg_color="#1e293b", corner_radius=8)
            self.card_best.pack(fill="x", padx=10, pady=10)
            
            self.lbl_best_title = ctk.CTkLabel(
                self.card_best, 
                text="🏆 最佳候选参数推断：尚未开始探测", 
                font=("Microsoft YaHei", 14, "bold"),
                text_color="#94a3b8"
            )
            self.lbl_best_title.pack(anchor="w", padx=15, pady=(10, 2))
            
            self.lbl_best_detail = ctk.CTkLabel(
                self.card_best, 
                text="请选择对应串口并点击“开始黑盒探测”，系统将自动匹配极大概率配置。", 
                font=("Microsoft YaHei", 11),
                text_color="#cbd5e1"
            )
            self.lbl_best_detail.pack(anchor="w", padx=15, pady=(0, 10))

            # 进度条
            self.progress_bar = ctk.CTkProgressBar(right_display)
            self.progress_bar.set(0)
            self.progress_bar.pack(fill="x", padx=10, pady=(0, 5))

            # 结果表格
            self._build_results_table(right_display)

        else:
            mid_frame = ttk.Frame(self.main_frame)
            mid_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 最佳推荐 Banner
            self.card_best = ttk.LabelFrame(mid_frame, text=" 🏆 最佳候选推断 ", padding=10)
            self.card_best.pack(fill="x", padx=5, pady=5)
            
            self.lbl_best_title = ttk.Label(self.card_best, text="尚未开始探测", font=("Microsoft YaHei", 12, "bold"))
            self.lbl_best_title.pack(anchor="w")
            self.lbl_best_detail = ttk.Label(self.card_best, text="选择串口后点击开始探测...")
            self.lbl_best_detail.pack(anchor="w")

            # 进度条
            self.progress_bar = ttk.Progressbar(mid_frame, mode='determinate')
            self.progress_bar.pack(fill="x", padx=5, pady=5)

            # 表格
            self._build_results_table(mid_frame)

    def _build_results_table(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("score", "param", "protocol", "mode", "ascii_ratio", "details")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)

        self.tree.heading("score", text="置信度得分")
        self.tree.heading("param", text="串口参数 (Baud, Parity)")
        self.tree.heading("protocol", text="识别协议/特征")
        self.tree.heading("mode", text="探测方式")
        self.tree.heading("ascii_ratio", text="ASCII可读率")
        self.tree.heading("details", text="匹配分析判定规则")

        self.tree.column("score", width=85, anchor="center")
        self.tree.column("param", width=160, anchor="center")
        self.tree.column("protocol", width=160, anchor="w")
        self.tree.column("mode", width=85, anchor="center")
        self.tree.column("ascii_ratio", width=85, anchor="center")
        self.tree.column("details", width=250, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_table_select)

    def _build_bottom_panel(self):
        if HAS_CTK:
            bottom_frame = ctk.CTkFrame(self.main_frame)
            bottom_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
            
            # 分割线两栏：抓包样品预览与日志
            left_preview = ctk.CTkFrame(bottom_frame)
            left_preview.pack(side="left", fill="both", expand=True, padx=(5, 2), pady=5)
            
            ctk.CTkLabel(left_preview, text="📦 抓取样本预览 (HEX / Text)", font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=5)
            self.txt_sample = ctk.CTkTextbox(left_preview, font=("Consolas", 10))
            self.txt_sample.pack(fill="both", expand=True, padx=5, pady=5)
            
            right_log = ctk.CTkFrame(bottom_frame)
            right_log.pack(side="right", fill="both", expand=True, padx=(2, 5), pady=5)
            
            ctk.CTkLabel(right_log, text="📜 实时日志与探测过程", font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=5)
            self.txt_log = ctk.CTkTextbox(right_log, font=("Consolas", 10))
            self.txt_log.pack(fill="both", expand=True, padx=5, pady=5)
        else:
            bottom_frame = ttk.Frame(self.main_frame)
            bottom_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            lbl_log = ttk.LabelFrame(bottom_frame, text=" 📜 实时日志 ", padding=5)
            lbl_log.pack(fill="both", expand=True)
            
            self.txt_log = tk.Text(lbl_log, height=6, font=("Consolas", 9))
            self.txt_log.pack(fill="both", expand=True)

    def refresh_ports(self):
        ports_list = get_available_ports()
        if not ports_list:
            display_values = ["未检测到有效串口"]
        else:
            display_values = [p['display'] for p in ports_list]

        if HAS_CTK:
            self.combo_ports.configure(values=display_values)
            self.combo_ports.set(display_values[0])
        else:
            self.combo_ports['values'] = display_values
            if display_values:
                self.combo_ports.current(0)

        self.log(f"🔄 刷新系统串口完成，发现 {len(ports_list)} 个端口设备。")

    def toggle_detection(self):
        if self.engine.is_running():
            self.engine.stop()
            self.log("⏸️ 用户请求停止探测...")
            return

        port_str = self.combo_ports.get()
        if not port_str or "未检测到" in port_str:
            messagebox.showwarning("警告", "请先选择有效的系统串口端口！")
            return

        port = port_str.split(" ")[0].strip()

        # 模式解析
        mode_str = self.combo_mode.get()
        if "被动" in mode_str:
            mode = "passive"
        elif "主动" in mode_str:
            mode = "active"
        else:
            mode = "auto"

        # 波特率范围
        if HAS_CTK and self.use_common_bauds.get() == 1:
            bauds = COMMON_BAUDRATES
        else:
            bauds = ALL_BAUDRATES

        # 校验位范围
        parities = []
        if not HAS_CTK or self.chk_parity_n.get() == 1:
            parities.append('None (N)')
        if not HAS_CTK or self.chk_parity_e.get() == 1:
            parities.append('Even (E)')
        if not HAS_CTK or self.chk_parity_o.get() == 1:
            parities.append('Odd (O)')

        if not parities:
            parities = ['None (N)']

        custom_hex = self.entry_custom_hex.get().strip() if HAS_CTK else ""
        sample_time = self.slider_sample_time.get() if HAS_CTK else 0.3

        # 清空 UI 表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results_data.clear()

        # 界面状态切换
        if HAS_CTK:
            self.btn_start.configure(text="⏹️ 停止探测", fg_color="#c92a2a", hover_color="#a61e1e")
            self.progress_bar.set(0)
            self.lbl_best_title.configure(text="⏳ 正在黑盒探测中...", text_color="#38bdf8")
            self.lbl_best_detail.configure(text=f"已选模式: {mode.upper()} | 正在评估候选参数逻辑，请稍候...")

        # 后台启动
        started = self.engine.start_detection_async(
            port=port,
            mode=mode,
            baudrates=bauds,
            parities=parities,
            custom_probe_hex=custom_hex,
            sample_time=sample_time,
            on_progress=self._on_progress,
            on_result_found=self._on_result_found,
            on_complete=self._on_complete,
            on_log=self.log
        )

        if not started:
            messagebox.showerror("错误", "探测引擎已在运行中，请勿重复启动！")

    def _on_progress(self, current: int, total: int, param_desc: str):
        ratio = current / total
        self.root.after(0, self._update_progress_ui, ratio, current, total, param_desc)

    def _update_progress_ui(self, ratio: float, current: int, total: int, param_desc: str):
        if HAS_CTK:
            self.progress_bar.set(ratio)
        else:
            self.progress_bar['value'] = ratio * 100

    def _on_result_found(self, result: Dict[str, Any]):
        self.root.after(0, self._add_result_to_tree, result)

    def _add_result_to_tree(self, res: Dict[str, Any]):
        self.results_data.append(res)
        self.tree.insert(
            "", "end",
            values=(
                f"{res['score']:.1f}",
                res['param_str'],
                res['protocol'],
                res['mode_used'].upper(),
                f"{res['ascii_ratio']:.1f}%",
                res['details']
            )
        )
        self._update_best_card()

    def _on_complete(self, results: List[Dict[str, Any]]):
        self.root.after(0, self._finish_ui_state, results)

    def _finish_ui_state(self, results: List[Dict[str, Any]]):
        if HAS_CTK:
            self.btn_start.configure(text="▶️ 开始黑盒探测", fg_color="#2b8a3e", hover_color="#216e31")
            self.progress_bar.set(1.0)

        if not results:
            if HAS_CTK:
                self.lbl_best_title.configure(text="❌ 未推导出有效参数", text_color="#f87171")
                self.lbl_best_detail.configure(text="在所测试的组合中未接收到任何有效回应。建议检查硬件连线或尝试【主动探针模式】并填入特定探针。")
            self.log("⚠️ 探测结束，未发现符合特征的设备。")
        else:
            self._update_best_card()
            best = results[0]
            self.log(f"🎉 探测完美完成！推导结果: 波特率={best['baudrate']}, 校验位={best['parity']}, 协议={best['protocol']}")

    def _update_best_card(self):
        if not self.results_data:
            return
        
        # 结果降序
        sorted_res = sorted(self.results_data, key=lambda x: x['score'], reverse=True)
        best = sorted_res[0]

        title = f"🏆 最高置信度配置：{best['baudrate']} bps | {best['databits']}{best['parity'][0]}{best['stopbits']}"
        detail = f"匹配协议/类型: [{best['protocol']}] | 置信度得分: {best['score']:.1f} / 100 | 判定理由: {best['details']}"

        if HAS_CTK:
            self.lbl_best_title.configure(text=title, text_color="#4ade80")
            self.lbl_best_detail.configure(text=detail)

    def _on_table_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item_idx = self.tree.index(selected_items[0])
        if item_idx < len(self.results_data):
            res = sorted(self.results_data, key=lambda x: x['score'], reverse=True)[item_idx]
            
            sample_info = f"=== 采样参数: {res['param_str']} ===\n"
            sample_info += f"HEX View:\n{res['sample_hex']}\n\n"
            sample_info += f"ASCII Text View:\n{res['sample_text']}\n"
            
            if HAS_CTK:
                self.txt_sample.delete("1.0", "end")
                self.txt_sample.insert("1.0", sample_info)

    def log(self, message: str):
        self.root.after(0, self._append_log_ui, message)

    def _append_log_ui(self, message: str):
        if HAS_CTK:
            self.txt_log.insert("end", message + "\n")
            self.txt_log.see("end")
        else:
            self.txt_log.insert("end", message + "\n")
            self.txt_log.see("end")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SerialDetectorApp()
    app.run()
