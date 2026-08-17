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
from detector.i18n import i18n, LANGUAGES, TRANSLATIONS

class SerialDetectorApp:
    """串口黑盒探测小工具 GUI 主界面 (包含字体统一与 Data Bits / Parity 修复)"""

    def __init__(self):
        self.engine = DetectionEngine()
        self.results_data: List[Dict[str, Any]] = []
        self.stop_requested = False

        if HAS_CTK:
            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()

        self.root.title(i18n.t('app_title'))
        self.root.geometry("1040x760")
        self.root.minsize(880, 620)

        self._setup_ui()
        self.refresh_ports()

    def _setup_ui(self):
        if HAS_CTK:
            self.main_frame = ctk.CTkFrame(self.root, corner_radius=10)
            self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        else:
            self.main_frame = ttk.Frame(self.root, padding=10)
            self.main_frame.pack(fill="both", expand=True)

        self._build_top_controls()
        self._build_middle_panel()
        self._build_bottom_panel()

    def _build_top_controls(self):
        if HAS_CTK:
            control_frame = ctk.CTkFrame(self.main_frame, corner_radius=8, fg_color="#2f2f2f")
            control_frame.pack(fill="x", padx=8, pady=(8, 10))
            control_frame.grid_columnconfigure(3, weight=1)

            self.lbl_port = ctk.CTkLabel(control_frame, text=i18n.t('select_port'), font=("Microsoft YaHei UI", 12, "bold"))
            self.lbl_port.grid(row=0, column=0, padx=(14, 8), pady=12, sticky="w")

            self.combo_ports = ctk.CTkOptionMenu(control_frame, width=320, height=34, font=("Microsoft YaHei UI", 12), values=["..."])
            self.combo_ports.grid(row=0, column=1, padx=(0, 10), pady=12, sticky="w")

            self.btn_refresh = ctk.CTkButton(control_frame, text=i18n.t('refresh'), width=90, height=34, font=("Microsoft YaHei UI", 12), command=self.refresh_ports)
            self.btn_refresh.grid(row=0, column=2, padx=(0, 12), pady=12)

            self.lbl_mode = ctk.CTkLabel(control_frame, text=i18n.t('detection_mode'), font=("Microsoft YaHei UI", 12, "bold"))
            self.lbl_mode.grid(row=0, column=3, padx=(12, 6), pady=12, sticky="e")

            self.combo_mode = ctk.CTkOptionMenu(
                control_frame, 
                width=190, 
                height=34,
                font=("Microsoft YaHei UI", 12),
                values=[i18n.t('mode_auto'), i18n.t('mode_passive'), i18n.t('mode_active')]
            )
            self.combo_mode.set(i18n.t('mode_auto'))
            self.combo_mode.grid(row=0, column=4, padx=(0, 12), pady=12)

            self.combo_lang = ctk.CTkOptionMenu(
                control_frame,
                width=115,
                height=34,
                font=("Microsoft YaHei UI", 12),
                values=list(LANGUAGES.values()),
                command=self._on_language_change
            )
            self.combo_lang.set(LANGUAGES['zh'])
            self.combo_lang.grid(row=0, column=5, padx=(0, 12), pady=12)

            self.btn_start = ctk.CTkButton(
                control_frame, 
                text=i18n.t('btn_start'), 
                fg_color="#2b8a3e", 
                hover_color="#216e31",
                font=("Microsoft YaHei UI", 13, "bold"),
                width=160,
                height=36,
                command=self.toggle_detection
            )
            self.btn_start.grid(row=0, column=6, padx=(0, 14), pady=12)
        else:
            self.control_frame = ttk.LabelFrame(self.main_frame, text=f" {i18n.t('controls_title')} ", padding=10)
            control_frame = self.control_frame
            control_frame.pack(fill="x", padx=5, pady=5)
            control_frame.grid_columnconfigure(3, weight=1)

            self.lbl_port = ttk.Label(control_frame, text=i18n.t('select_port'))
            self.lbl_port.grid(row=0, column=0, padx=5, pady=4, sticky="w")

            self.combo_ports = ttk.Combobox(control_frame, width=40, state="readonly")
            self.combo_ports.grid(row=0, column=1, padx=5, pady=4, sticky="w")

            self.btn_refresh = ttk.Button(control_frame, text=i18n.t('refresh'), command=self.refresh_ports)
            self.btn_refresh.grid(row=0, column=2, padx=5, pady=4)

            self.lbl_mode = ttk.Label(control_frame, text=i18n.t('detection_mode'))
            self.lbl_mode.grid(row=0, column=3, padx=5, pady=4, sticky="e")

            self.combo_mode = ttk.Combobox(
                control_frame, 
                values=[i18n.t('mode_auto'), i18n.t('mode_passive'), i18n.t('mode_active')], 
                state="readonly",
                width=20
            )
            self.combo_mode.current(0)
            self.combo_mode.grid(row=0, column=4, padx=5, pady=4)

            self.combo_lang = ttk.Combobox(
                control_frame,
                values=list(LANGUAGES.values()),
                state="readonly",
                width=10
            )
            self.combo_lang.current(0)
            self.combo_lang.grid(row=0, column=5, padx=5, pady=4)
            self.combo_lang.bind("<<ComboboxSelected>>", self._on_language_change_ttk)

            self.btn_start = ttk.Button(control_frame, text=i18n.t('btn_start'), command=self.toggle_detection)
            self.btn_start.grid(row=0, column=6, padx=5, pady=4)

    def _build_middle_panel(self):
        if HAS_CTK:
            mid_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            mid_frame.pack(fill="both", expand=True, padx=0, pady=5)
            
            left_config = ctk.CTkFrame(mid_frame, width=260, corner_radius=8, fg_color="#2a2a2a")
            left_config.pack(side="left", fill="y", padx=(0, 8), pady=0)
            
            self.lbl_scan_range = ctk.CTkLabel(left_config, text=i18n.t('scan_range_title'), font=("Microsoft YaHei UI", 13, "bold"))
            self.lbl_scan_range.pack(anchor="w", padx=12, pady=(12, 8))
            
            self.use_common_bauds = ctk.CTkCheckBox(left_config, text=i18n.t('chk_common_bauds'), font=("Microsoft YaHei UI", 12), onvalue=1, offvalue=0)
            self.use_common_bauds.select()
            self.use_common_bauds.pack(anchor="w", padx=12, pady=5)
            
            # 数据位勾选
            self.lbl_databits_title = ctk.CTkLabel(left_config, text=i18n.t('databits_title'), font=("Microsoft YaHei UI", 11, "bold"))
            self.lbl_databits_title.pack(anchor="w", padx=12, pady=(10, 2))
            
            self.chk_dbit_8 = ctk.CTkCheckBox(left_config, text=i18n.t('chk_databits_8'), font=("Microsoft YaHei UI", 11), onvalue=1, offvalue=0)
            self.chk_dbit_8.select()
            self.chk_dbit_8.pack(anchor="w", padx=18, pady=2)
            
            self.chk_dbit_7 = ctk.CTkCheckBox(left_config, text=i18n.t('chk_databits_7'), font=("Microsoft YaHei UI", 11), onvalue=1, offvalue=0)
            self.chk_dbit_7.select()
            self.chk_dbit_7.pack(anchor="w", padx=18, pady=2)

            # 校验位勾选
            self.lbl_parity_title = ctk.CTkLabel(left_config, text=i18n.t('parity_title'), font=("Microsoft YaHei UI", 11, "bold"))
            self.lbl_parity_title.pack(anchor="w", padx=12, pady=(10, 2))
            
            self.chk_parity_n = ctk.CTkCheckBox(left_config, text="None (N)", font=("Microsoft YaHei UI", 11), onvalue=1, offvalue=0)
            self.chk_parity_n.select()
            self.chk_parity_n.pack(anchor="w", padx=18, pady=2)
            
            self.chk_parity_e = ctk.CTkCheckBox(left_config, text="Even (E)", font=("Microsoft YaHei UI", 11), onvalue=1, offvalue=0)
            self.chk_parity_e.select()
            self.chk_parity_e.pack(anchor="w", padx=18, pady=2)
            
            self.chk_parity_o = ctk.CTkCheckBox(left_config, text="Odd (O)", font=("Microsoft YaHei UI", 11), onvalue=1, offvalue=0)
            self.chk_parity_o.select()
            self.chk_parity_o.pack(anchor="w", padx=18, pady=2)
            
            self.lbl_custom_hex = ctk.CTkLabel(left_config, text=i18n.t('custom_hex_title'), font=("Microsoft YaHei UI", 11, "bold"))
            self.lbl_custom_hex.pack(anchor="w", padx=12, pady=(12, 2))
            
            self.entry_custom_hex = ctk.CTkEntry(left_config, placeholder_text=i18n.t('custom_hex_placeholder'), font=("Microsoft YaHei UI", 11))
            self.entry_custom_hex.pack(fill="x", padx=12, pady=4)
            
            self.lbl_sample_time = ctk.CTkLabel(left_config, text=i18n.t('sample_time_title'), font=("Microsoft YaHei UI", 11, "bold"))
            self.lbl_sample_time.pack(anchor="w", padx=12, pady=(10, 2))
            
            self.slider_sample_time = ctk.CTkSlider(left_config, from_=0.1, to=1.0, number_of_steps=9)
            self.slider_sample_time.set(0.3)
            self.slider_sample_time.pack(fill="x", padx=12, pady=4)
            
            right_display = ctk.CTkFrame(mid_frame, fg_color="transparent")
            right_display.pack(side="right", fill="both", expand=True, padx=0, pady=0)
            
            self.card_best = ctk.CTkFrame(right_display, fg_color="#1e293b", corner_radius=8)
            self.card_best.pack(fill="x", padx=0, pady=(0, 8))
            
            self.lbl_best_title = ctk.CTkLabel(
                self.card_best, 
                text=i18n.t('best_card_title_default'), 
                font=("Microsoft YaHei UI", 13, "bold"),
                text_color="#94a3b8"
            )
            self.lbl_best_title.pack(anchor="w", padx=15, pady=(10, 2))
            
            self.lbl_best_detail = ctk.CTkLabel(
                self.card_best, 
                text=i18n.t('best_card_detail_default'), 
                font=("Microsoft YaHei UI", 11),
                text_color="#cbd5e1"
            )
            self.lbl_best_detail.pack(anchor="w", padx=15, pady=(0, 10))

            self.progress_bar = ctk.CTkProgressBar(right_display)
            self.progress_bar.set(0)
            self.progress_bar.pack(fill="x", padx=0, pady=(0, 6))

            self._build_results_table(right_display)

        else:
            mid_frame = ttk.Frame(self.main_frame)
            mid_frame.pack(fill="both", expand=True, padx=5, pady=5)

            self.left_config_group = ttk.LabelFrame(mid_frame, text=f" {i18n.t('scan_range_title')} ", padding=10)
            left_config = self.left_config_group
            left_config.pack(side="left", fill="y", padx=(0, 5), pady=0)

            self.use_common_bauds = ttk.Checkbutton(left_config, text=i18n.t('chk_common_bauds'))
            self.use_common_bauds.pack(anchor="w", pady=2)

            self.card_best = ttk.LabelFrame(mid_frame, text=f" {i18n.t('best_group_title')} ", padding=10)
            self.card_best.pack(fill="x", padx=5, pady=5)
            
            self.lbl_best_title = ttk.Label(self.card_best, text=i18n.t('best_card_title_default'), font=("Microsoft YaHei UI", 12, "bold"))
            self.lbl_best_title.pack(anchor="w")
            self.lbl_best_detail = ttk.Label(self.card_best, text=i18n.t('best_card_detail_default'))
            self.lbl_best_detail.pack(anchor="w")

            self.progress_bar = ttk.Progressbar(mid_frame, mode='determinate')
            self.progress_bar.pack(fill="x", padx=5, pady=5)

            self._build_results_table(mid_frame)

    def _build_results_table(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=0, pady=0)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#171717",
            fieldbackground="#171717",
            foreground="#e5e7eb",
            borderwidth=0,
            rowheight=30,
            font=("Consolas", "Microsoft YaHei UI", 11),  # 修复表格中英文混排字体
        )
        style.configure(
            "Treeview.Heading",
            background="#262626",
            foreground="#f8fafc",
            borderwidth=0,
            relief="flat",
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")],
        )

        columns = ("score", "param", "protocol", "mode", "ascii_ratio", "details")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8, style="Treeview")

        self.tree.heading("score", text=i18n.t('table_score'))
        self.tree.heading("param", text=i18n.t('table_param'))
        self.tree.heading("protocol", text=i18n.t('table_protocol'))
        self.tree.heading("mode", text=i18n.t('table_mode'))
        self.tree.heading("ascii_ratio", text=i18n.t('table_ascii_ratio'))
        self.tree.heading("details", text=i18n.t('table_details'))

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
            bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            bottom_frame.pack(fill="both", expand=True, padx=0, pady=(8, 0))
            
            left_preview = ctk.CTkFrame(bottom_frame, corner_radius=8, fg_color="#2a2a2a")
            left_preview.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=0)
            
            self.lbl_sample = ctk.CTkLabel(left_preview, text=i18n.t('sample_title'), font=("Microsoft YaHei UI", 12, "bold"))
            self.lbl_sample.pack(anchor="w", padx=12, pady=(10, 6))
            
            # 修复 Consolas 与 微软雅黑混排字体
            self.txt_sample = ctk.CTkTextbox(left_preview, font=("Consolas", "Microsoft YaHei UI", 11), fg_color="#171717", corner_radius=6)
            self.txt_sample.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            right_log = ctk.CTkFrame(bottom_frame, corner_radius=8, fg_color="#2a2a2a")
            right_log.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)
            
            self.lbl_log = ctk.CTkLabel(right_log, text=i18n.t('log_title'), font=("Microsoft YaHei UI", 12, "bold"))
            self.lbl_log.pack(anchor="w", padx=12, pady=(10, 6))
            
            # 修复 Consolas 与 微软雅黑混排字体（解决日志粗宋体不美观问题）
            self.txt_log = ctk.CTkTextbox(right_log, font=("Consolas", "Microsoft YaHei UI", 11), fg_color="#171717", corner_radius=6)
            self.txt_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        else:
            bottom_frame = ttk.Frame(self.main_frame)
            bottom_frame.pack(fill="both", expand=True, padx=0, pady=(0, 0))
            
            self.lbl_log_group = ttk.LabelFrame(bottom_frame, text=f" {i18n.t('logs_group_title')} ", padding=5)
            lbl_log = self.lbl_log_group
            lbl_log.pack(fill="both", expand=True)
            
            self.txt_log = tk.Text(lbl_log, height=6, font=("Consolas", "Microsoft YaHei UI", 11))
            self.txt_log.pack(fill="both", expand=True)

    def _on_language_change(self, selected_val: str):
        target_lang = 'zh' if '中文' in selected_val else 'en'
        i18n.set_language(target_lang)
        self.update_ui_language()

    def _on_language_change_ttk(self, event):
        selected_val = self.combo_lang.get()
        target_lang = 'zh' if '中文' in selected_val else 'en'
        i18n.set_language(target_lang)
        self.update_ui_language()

    def update_ui_language(self):
        """刷新界面上所有组件的文案内容，包括动态表格和卡片"""
        self.root.title(i18n.t('app_title'))
        
        self.lbl_port.configure(text=i18n.t('select_port')) if HAS_CTK else self.lbl_port.config(text=i18n.t('select_port'))
        self.btn_refresh.configure(text=i18n.t('refresh')) if HAS_CTK else self.btn_refresh.config(text=i18n.t('refresh'))
        self.lbl_mode.configure(text=i18n.t('detection_mode')) if HAS_CTK else self.lbl_mode.config(text=i18n.t('detection_mode'))
        
        mode_values = [i18n.t('mode_auto'), i18n.t('mode_passive'), i18n.t('mode_active')]
        if HAS_CTK:
            self.combo_mode.configure(values=mode_values)
            self.combo_mode.set(mode_values[0])
            if self.stop_requested:
                self.btn_start.configure(text=i18n.t('btn_stopping'))
            else:
                self.btn_start.configure(text=i18n.t('btn_stop') if self.engine.is_running() else i18n.t('btn_start'))
            
            self.lbl_scan_range.configure(text=i18n.t('scan_range_title'))
            self.use_common_bauds.configure(text=i18n.t('chk_common_bauds'))
            self.lbl_databits_title.configure(text=i18n.t('databits_title'))
            self.chk_dbit_8.configure(text=i18n.t('chk_databits_8'))
            self.chk_dbit_7.configure(text=i18n.t('chk_databits_7'))
            self.lbl_parity_title.configure(text=i18n.t('parity_title'))
            self.lbl_custom_hex.configure(text=i18n.t('custom_hex_title'))
            self.entry_custom_hex.configure(placeholder_text=i18n.t('custom_hex_placeholder'))
            self.lbl_sample_time.configure(text=i18n.t('sample_time_title'))
            self.lbl_sample.configure(text=i18n.t('sample_title'))
            self.lbl_log.configure(text=i18n.t('log_title'))
        else:
            self.combo_mode['values'] = mode_values
            self.combo_mode.current(0)
            if self.stop_requested:
                self.btn_start.config(text=i18n.t('btn_stopping'))
            else:
                self.btn_start.config(text=i18n.t('btn_stop') if self.engine.is_running() else i18n.t('btn_start'))
            self.control_frame.config(text=f" {i18n.t('controls_title')} ")
            self.left_config_group.config(text=f" {i18n.t('scan_range_title')} ")
            self.card_best.config(text=f" {i18n.t('best_group_title')} ")
            self.lbl_log_group.config(text=f" {i18n.t('logs_group_title')} ")

        self.refresh_ports(silent_log=True)

        self.tree.heading("score", text=i18n.t('table_score'))
        self.tree.heading("param", text=i18n.t('table_param'))
        self.tree.heading("protocol", text=i18n.t('table_protocol'))
        self.tree.heading("mode", text=i18n.t('table_mode'))
        self.tree.heading("ascii_ratio", text=i18n.t('table_ascii_ratio'))
        self.tree.heading("details", text=i18n.t('table_details'))

        for item in self.tree.get_children():
            self.tree.delete(item)

        for res in self.results_data:
            res['details'] = i18n.t(res.get('details_key', 'detail_ascii_ratio'), **res.get('details_kwargs', {}))
            self.tree.insert(
                "", "end",
                values=(
                    f"{res['score']:.1f}",
                    res['param_str'],
                    res['protocol'],
                    self._localized_mode_label(res['mode_used']),
                    f"{res['ascii_ratio']:.1f}%",
                    res['details']
                )
            )

        if not self.results_data:
            if HAS_CTK:
                self.lbl_best_title.configure(text=i18n.t('best_card_title_default'))
                self.lbl_best_detail.configure(text=i18n.t('best_card_detail_default'))
            else:
                self.lbl_best_title.config(text=i18n.t('best_card_title_default'))
                self.lbl_best_detail.config(text=i18n.t('best_card_detail_default'))
        else:
            self._update_best_card()

    def refresh_ports(self, silent_log: bool = False):
        ports_list = get_available_ports()
        if not ports_list:
            display_values = [i18n.t('no_port_warning')]
        else:
            display_values = [self._format_port_display(p) for p in ports_list]

        if HAS_CTK:
            self.combo_ports.configure(values=display_values)
            self.combo_ports.set(display_values[0])
        else:
            self.combo_ports['values'] = display_values
            if display_values:
                self.combo_ports.current(0)

        if not silent_log:
            self.log(i18n.t('log_refresh_ports', count=len(ports_list)))

    def toggle_detection(self):
        if self.engine.is_running():
            if self.stop_requested:
                return
            self.stop_requested = True
            self.engine.stop()
            self.log(i18n.t('log_user_stop'))
            self._show_stopping_state()
            return

        port_str = self.combo_ports.get()
        if not port_str or port_str in (i18n.t('no_port_warning'), "未检测到有效串口", "No valid serial ports found"):
            messagebox.showwarning(i18n.t('dialog_warning_title'), i18n.t('warn_select_port'))
            return
        if self._is_busy_port_display(port_str):
            messagebox.showwarning(i18n.t('dialog_warning_title'), i18n.t('warn_port_busy'))
            return

        port = port_str.split(" ")[0].strip()

        mode_str = self.combo_mode.get()
        if "Passive" in mode_str or "被动" in mode_str:
            mode = "passive"
        elif "Active" in mode_str or "主动" in mode_str:
            mode = "active"
        else:
            mode = "auto"

        if HAS_CTK and self.use_common_bauds.get() == 1:
            bauds = COMMON_BAUDRATES
        else:
            bauds = ALL_BAUDRATES

        # 数据位选择
        databits = []
        if not HAS_CTK or self.chk_dbit_8.get() == 1:
            databits.append(8)
        if not HAS_CTK or self.chk_dbit_7.get() == 1:
            databits.append(7)
        if not databits:
            databits = [8, 7]

        # 校验位选择
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

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results_data.clear()
        self.stop_requested = False

        if HAS_CTK:
            self.btn_start.configure(text=i18n.t('btn_stop'), state="normal", fg_color="#c92a2a", hover_color="#a61e1e")
            self.progress_bar.set(0)
            self.lbl_best_title.configure(text=i18n.t('best_card_title_testing'), text_color="#38bdf8")
            self.lbl_best_detail.configure(text=i18n.t('best_card_detail_testing', mode=self._localized_mode_label(mode)))
        else:
            self.btn_start.config(text=i18n.t('btn_stop'), state="normal")

        started = self.engine.start_detection_async(
            port=port,
            mode=mode,
            baudrates=bauds,
            parities=parities,
            databits=databits,
            custom_probe_hex=custom_hex,
            sample_time=sample_time,
            on_progress=self._on_progress,
            on_result_found=self._on_result_found,
            on_complete=self._on_complete,
            on_log=self.log
        )

        if not started:
            self.stop_requested = False
            messagebox.showerror(i18n.t('dialog_error_title'), i18n.t('err_engine_running'))

    def _show_stopping_state(self):
        if HAS_CTK:
            self.btn_start.configure(text=i18n.t('btn_stopping'), state="disabled")
            self.lbl_best_title.configure(text=i18n.t('best_card_title_stopping'), text_color="#facc15")
            self.lbl_best_detail.configure(text=i18n.t('best_card_detail_stopping'))
        else:
            self.btn_start.config(text=i18n.t('btn_stopping'), state="disabled")

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
        res['details'] = i18n.t(res.get('details_key', 'detail_ascii_ratio'), **res.get('details_kwargs', {}))
        self.tree.insert(
            "", "end",
            values=(
                f"{res['score']:.1f}",
                res['param_str'],
                res['protocol'],
                self._localized_mode_label(res['mode_used']),
                f"{res['ascii_ratio']:.1f}%",
                res['details']
            )
        )
        self._update_best_card()

    def _on_complete(self, results: List[Dict[str, Any]]):
        self.root.after(0, self._finish_ui_state, results)

    def _finish_ui_state(self, results: List[Dict[str, Any]]):
        was_stopped = self.stop_requested
        self.stop_requested = False

        if HAS_CTK:
            self.btn_start.configure(text=i18n.t('btn_start'), state="normal", fg_color="#2b8a3e", hover_color="#216e31")
            self.progress_bar.set(0 if was_stopped else 1.0)
        else:
            self.btn_start.config(text=i18n.t('btn_start'), state="normal")
            self.progress_bar['value'] = 0 if was_stopped else 100

        if was_stopped:
            if HAS_CTK:
                self.lbl_best_title.configure(text=i18n.t('best_card_title_default'), text_color="#94a3b8")
                self.lbl_best_detail.configure(text=i18n.t('best_card_detail_default'))
            else:
                self.lbl_best_title.config(text=i18n.t('best_card_title_default'))
                self.lbl_best_detail.config(text=i18n.t('best_card_detail_default'))
        elif not results:
            if HAS_CTK:
                self.lbl_best_title.configure(text=i18n.t('best_card_title_none'), text_color="#f87171")
                self.lbl_best_detail.configure(text=i18n.t('best_card_detail_none'))
            self.log(i18n.t('best_card_title_none'))
        else:
            self._update_best_card()
            best = results[0]
            self.log(i18n.t('log_complete_best', baud=best['baudrate'], parity=best['parity'], protocol=best['protocol']))

    def _update_best_card(self):
        if not self.results_data:
            return
        
        sorted_res = sorted(self.results_data, key=lambda x: x['score'], reverse=True)
        best = sorted_res[0]

        details_str = i18n.t(best.get('details_key', 'detail_ascii_ratio'), **best.get('details_kwargs', {}))

        title = i18n.t('best_card_title_found', baud=best['baudrate'], param=f"{best['databits']}{best['parity'][0]}{best['stopbits']}")
        detail = i18n.t('best_card_detail_found', protocol=best['protocol'], score=f"{best['score']:.1f}", details=details_str)

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
            
            sample_info = f"=== {res['param_str']} ===\n"
            sample_info += f"{i18n.t('sample_hex_view')}:\n{res['sample_hex']}\n\n"
            sample_info += f"{i18n.t('sample_text_view')}:\n{res['sample_text']}\n"
            
            if HAS_CTK:
                self.txt_sample.delete("1.0", "end")
                self.txt_sample.insert("1.0", sample_info)

    def _localized_mode_label(self, mode: str) -> str:
        return i18n.t(f"mode_value_{mode}", mode=mode).upper() if i18n.current_lang == 'en' else i18n.t(f"mode_value_{mode}", mode=mode)

    def _format_port_display(self, port_info: Dict[str, Any]) -> str:
        display = port_info['display']
        if port_info.get('is_busy'):
            display += f" [{i18n.t('port_status_busy')}]"
        return display

    def _is_busy_port_display(self, display_text: str) -> bool:
        busy_labels = [TRANSLATIONS[lang]['port_status_busy'] for lang in TRANSLATIONS]
        return any(f"[{label}]" in display_text for label in busy_labels)

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
