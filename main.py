#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
串口黑盒探测小工具 (Serial Port Black-Box Detector)
主程序入口

作者: DeepMind AI Pair Programmer
许可: MIT License
"""

import sys
import os

# 确保把当前路径添加到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import SerialDetectorApp

def main():
    print("==================================================")
    print(" 🚀 正在启动串口黑盒探测小工具 (Serial Port Black-Box Detector)...")
    print("==================================================")
    
    app = SerialDetectorApp()
    app.run()

if __name__ == "__main__":
    main()
