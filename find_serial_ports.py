#!/usr/bin/env python3
"""查找 MaixCam 上可用的串口设备"""

import os
import glob

def find_serial_ports():
    """扫描所有可能的串口设备"""
    print("=" * 60)
    print("MaixCam 串口设备扫描")
    print("=" * 60)
    
    # 常见的串口设备模式
    patterns = [
        '/dev/ttyS*',      # 标准串口
        '/dev/ttyAMA*',    # ARM 串口
        '/dev/ttyUSB*',    # USB转串口
        '/dev/ttyACM*',    # USB虚拟串口
    ]
    
    found_ports = []
    
    for pattern in patterns:
        ports = glob.glob(pattern)
        if ports:
            print(f"\n{pattern}:")
            for port in sorted(ports):
                # 检查是否可访问
                if os.access(port, os.R_OK | os.W_OK):
                    status = "✓ 可读写"
                    found_ports.append(port)
                elif os.access(port, os.R_OK):
                    status = "○ 只读"
                else:
                    status = "✗ 无权限"
                
                print(f"  {port} - {status}")
    
    print("\n" + "=" * 60)
    
    if found_ports:
        print(f"找到 {len(found_ports)} 个可用串口:")
        for port in found_ports:
            print(f"  {port}")
        
        print("\n建议:")
        print("  1. 通常 /dev/ttyS0 是调试串口（不要用）")
        print("  2. /dev/ttyS1 或 /dev/ttyS2 可能是可用的硬件串口")
        print("  3. 如果 WonderEcho 通过 USB 连接，使用 /dev/ttyUSB0")
    else:
        print("未找到可用串口设备")
        print("\n可能原因:")
        print("  1. 权限不足，尝试: sudo python3 此脚本")
        print("  2. 串口设备未启用")
    
    return found_ports

def test_serial_port(port):
    """测试指定串口是否可用"""
    try:
        import serial
        print(f"\n测试串口: {port}")
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"  ✓ 串口打开成功")
        ser.close()
        return True
    except ImportError:
        print("  ! pyserial 未安装，无法测试")
        print("  安装: pip install pyserial")
        return False
    except Exception as e:
        print(f"  ✗ 打开失败: {e}")
        return False

if __name__ == "__main__":
    ports = find_serial_ports()
    
    # 尝试导入 serial 库测试
    if ports:
        print("\n" + "=" * 60)
        print("串口功能测试")
        print("=" * 60)
        
        for port in ports:
            test_serial_port(port)
