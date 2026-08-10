"""Internationalization (i18n) Module for Serial Black-Box Detector"""

from typing import Dict, Any

LANGUAGES = {
    'zh': '🇨🇳 中文',
    'en': '🇺🇸 English'
}

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'zh': {
        'app_title': '串口黑盒探测小工具 v1.1 (Serial Port Black-Box Detector)',
        'select_port': '选择串口:',
        'refresh': '🔄 刷新',
        'detection_mode': '探测模式:',
        'mode_auto': '🚀 智能混合模式',
        'mode_passive': '👂 纯被动监听模式',
        'mode_active': '⚡ 主动探针问答模式',
        'btn_start': '▶️ 开始黑盒探测',
        'btn_stop': '⏹️ 停止探测',
        'scan_range_title': '⚙️ 探测扫描范围设置',
        'chk_common_bauds': '仅扫描常见波特率(推荐)',
        'parity_title': '校验位 (Parity):',
        'custom_hex_title': '自定义探针 Hex (可选):',
        'custom_hex_placeholder': '例如: 01 03 00 00 00 01',
        'sample_time_title': '单项采样微调(秒):',
        'best_card_title_default': '🏆 最佳候选参数推断：尚未开始探测',
        'best_card_detail_default': '请选择对应串口并点击“开始黑盒探测”，系统将自动匹配极大概率配置。',
        'best_card_title_testing': '⏳ 正在黑盒探测中...',
        'best_card_detail_testing': '已选模式: {mode} | 正在评估候选参数逻辑，请稍候...',
        'best_card_title_none': '❌ 未推导出有效参数',
        'best_card_detail_none': '在所测试的组合中未接收到任何有效回应。建议检查硬件连线或尝试【主动探针模式】。',
        'best_card_title_found': '🏆 最高置信度配置：{baud} bps | {param}',
        'best_card_detail_found': '匹配协议/类型: [{protocol}] | 置信度得分: {score} / 100 | 判定理由: {details}',
        'table_score': '置信度得分',
        'table_param': '串口参数 (Baud, Parity)',
        'table_protocol': '识别协议/特征',
        'table_mode': '探测方式',
        'table_ascii_ratio': 'ASCII可读率',
        'table_details': '匹配分析判定规则',
        'sample_title': '📦 抓取样本预览 (HEX / Text)',
        'log_title': '📜 实时日志与探测过程',
        'no_port_warning': '未检测到有效串口',
        'warn_select_port': '请先选择有效的系统串口端口！',
        'err_engine_running': '探测引擎已在运行中，请勿重复启动！',
        'log_refresh_ports': '🔄 刷新系统串口完成，发现 {count} 个端口设备。',
        'log_start_detection': '🚀 开始串口黑盒探测: {port} | 模式: {mode}',
        'log_user_stop': '🛑 用户中止了探测流程。',
        'log_found_match': '🎯 [得分 {score}] 匹配参数: {param} | 协议: {protocol}',
        'log_high_confidence': '✅ 已匹配到高置信度目标 ({protocol})，探测完成！',
        'log_complete_summary': '🏁 探测结束！共找到 {count} 个潜在符合的参数组合。',
        'log_complete_best': '🎉 探测完美完成！推导结果: 波特率={baud}, 校验位={parity}, 协议={protocol}',
    },
    'en': {
        'app_title': 'Serial Black-Box Detector v1.1',
        'select_port': 'Select Port:',
        'refresh': '🔄 Refresh',
        'detection_mode': 'Detect Mode:',
        'mode_auto': '🚀 Auto / Hybrid Mode',
        'mode_passive': '👂 Passive Sniffing',
        'mode_active': '⚡ Active Probing',
        'btn_start': '▶️ Start Detection',
        'btn_stop': '⏹️ Stop Detection',
        'scan_range_title': '⚙️ Scan Range Settings',
        'chk_common_bauds': 'Common Baudrates Only',
        'parity_title': 'Parity Check:',
        'custom_hex_title': 'Custom Probe Hex (Opt):',
        'custom_hex_placeholder': 'e.g. 01 03 00 00 00 01',
        'sample_time_title': 'Sample Time (sec):',
        'best_card_title_default': '🏆 Best Match: Detection Not Started',
        'best_card_detail_default': 'Select a serial port and click "Start Detection" to infer parameters.',
        'best_card_title_testing': '⏳ Detecting Serial Parameters...',
        'best_card_detail_testing': 'Mode: {mode} | Evaluating candidate combinations, please wait...',
        'best_card_title_none': '❌ No Valid Parameters Inferred',
        'best_card_detail_none': 'No valid response received under tested settings. Check hardware wiring or try Active Probing Mode.',
        'best_card_title_found': '🏆 Top Confidence Config: {baud} bps | {param}',
        'best_card_detail_found': 'Protocol: [{protocol}] | Confidence Score: {score} / 100 | Reason: {details}',
        'table_score': 'Score',
        'table_param': 'Serial Params',
        'table_protocol': 'Detected Protocol',
        'table_mode': 'Mode',
        'table_ascii_ratio': 'ASCII Ratio',
        'table_details': 'Evaluation Details',
        'sample_title': '📦 Captured Sample Preview (HEX / Text)',
        'log_title': '📜 Live Logs & Status',
        'no_port_warning': 'No valid serial ports found',
        'warn_select_port': 'Please select a valid serial port first!',
        'err_engine_running': 'Detection engine is already running!',
        'log_refresh_ports': '🔄 Refreshed ports list, found {count} available devices.',
        'log_start_detection': '🚀 Started detection: {port} | Mode: {mode}',
        'log_user_stop': '🛑 User cancelled detection process.',
        'log_found_match': '🎯 [Score {score}] Matched Params: {param} | Protocol: {protocol}',
        'log_high_confidence': '✅ Matched high confidence target ({protocol}), detection completed!',
        'log_complete_summary': '🏁 Scan finished! Found {count} candidate parameter combinations.',
        'log_complete_best': '🎉 Detection complete! Inferred Result: Baud={baud}, Parity={parity}, Protocol={protocol}',
    }
}

class I18nManager:
    def __init__(self, default_lang: str = 'zh'):
        self.current_lang = default_lang

    def set_language(self, lang: str):
        if lang in TRANSLATIONS:
            self.current_lang = lang

    def t(self, key: str, **kwargs) -> str:
        """获取本地化字符串，支持占位符替换"""
        lang_dict = TRANSLATIONS.get(self.current_lang, TRANSLATIONS['zh'])
        text = lang_dict.get(key, TRANSLATIONS['zh'].get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

i18n = I18nManager('zh')
