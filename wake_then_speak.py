#!/usr/bin/env python3
"""测试唤醒后播报"""

import smbus
import time

BUS_ID = 4
ADDR = 0x34
SPEAK_REG = 0x6E

def speak(bus, cmd, id, desc):
    """发送播报命令"""
    data = [cmd, id]
    bus.write_i2c_block_data(ADDR, SPEAK_REG, data)
    print(f"  -> 发送: {desc} (0x{cmd:02X} 0x{id:02X})")

def main():
    print("=" * 60)
    print("WonderEcho 唤醒+播报测试")
    print("=" * 60)
    
    bus = smbus.SMBus(BUS_ID)
    
    # 策略1: 先发送"我在"命令（模拟唤醒词的响应）
    print("\n[策略1] 先发送'我在'命令激活模块")
    print("-" * 60)
    speak(bus, 0x00, 0x03, "我在")
    print("  -> 等待 3 秒...")
    time.sleep(3)
    
    print("\n然后立即发送播报语...")
    speak(bus, 0xFF, 0x01, "可回收物")
    print("  -> 等待 5 秒...")
    time.sleep(5)
    
    # 策略2: 发送"开启播报"命令（ID=9）
    print("\n[策略2] 发送'开启播报'命令")
    print("-" * 60)
    speak(bus, 0x00, 0x09, "开启播报")
    print("  -> 等待 2 秒...")
    time.sleep(2)
    
    speak(bus, 0xFF, 0x02, "厨余垃圾")
    print("  -> 等待 5 秒...")
    time.sleep(5)
    
    # 策略3: 发送"最大音量"命令（ID=6）
    print("\n[策略3] 先设置最大音量")
    print("-" * 60)
    speak(bus, 0x00, 0x06, "最大音量")
    print("  -> 等待 2 秒...")
    time.sleep(2)
    
    speak(bus, 0xFF, 0x03, "有害垃圾")
    print("  -> 等待 5 秒...")
    time.sleep(5)
    
    # 策略4: 连续发送多次同一命令
    print("\n[策略4] 重复发送命令3次")
    print("-" * 60)
    for i in range(3):
        speak(bus, 0xFF, 0x04, f"其他垃圾 (第{i+1}次)")
        time.sleep(0.5)
    print("  -> 等待 5 秒...")
    time.sleep(5)
    
    bus.close()
    
    print("\n" + "=" * 60)
    print("测试结束")
    print("=" * 60)
    print("\n如果仍然没有声音，请确认:")
    print("1. 模块单独 Type-C 供电时，说'小幻小幻'能听到'我在'吗？")
    print("2. 如果能，请在测试期间手动说'小幻小幻'唤醒，看是否影响")
    print("3. 检查固件是否真的包含这些播报语（ID 1-4）")

if __name__ == "__main__":
    main()
