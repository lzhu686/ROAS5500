#!/usr/bin/env python3
"""验证 I2C 设备身份"""

import smbus
import time

BUS_ID = 4
CANDIDATES = [0x34, 0x51, 0x6b]

def test_device(addr):
    """测试设备是否是 WonderEcho"""
    print(f"\n{'='*60}")
    print(f"测试地址: 0x{addr:02X}")
    print('='*60)
    
    bus = smbus.SMBus(BUS_ID)
    
    # 测试1: 尝试读取 WonderEcho 的识别结果寄存器 (0x64)
    print("\n[测试1] 读取寄存器 0x64 (语音识别结果)")
    try:
        data = bus.read_i2c_block_data(addr, 0x64, 1)
        print(f"  ✓ 成功读取: {data} (值: {data[0]})")
        print(f"  -> 如果是 WonderEcho，值应该是 0 或小的正整数（识别ID）")
        result_0x64 = True
    except Exception as e:
        print(f"  ✗ 读取失败: {e}")
        result_0x64 = False
    
    # 测试2: 尝试写入播报寄存器 (0x6E)
    print("\n[测试2] 写入寄存器 0x6E (播报命令)")
    try:
        # 发送"我在"命令 (0x00, 0x03)
        bus.write_i2c_block_data(addr, 0x6E, [0x00, 0x03])
        print(f"  ✓ 成功写入 [0x00, 0x03]")
        print(f"  -> 如果是 WonderEcho，可能会播放'我在'（等待3秒）")
        time.sleep(3)
        result_0x6E = True
    except Exception as e:
        print(f"  ✗ 写入失败: {e}")
        result_0x6E = False
    
    # 测试3: 读取一些常见寄存器，看数据特征
    print("\n[测试3] 读取多个寄存器查看数据模式")
    for reg in [0x00, 0x01, 0x64, 0x6E]:
        try:
            data = bus.read_byte_data(addr, reg)
            print(f"  寄存器 0x{reg:02X}: {data} (0x{data:02X})")
        except Exception as e:
            print(f"  寄存器 0x{reg:02X}: 读取失败 - {e}")
    
    bus.close()
    
    # 判断
    print(f"\n{'='*60}")
    if result_0x64 and result_0x6E:
        print(f"✓✓✓ 地址 0x{addr:02X} 很可能是 WonderEcho ✓✓✓")
    elif result_0x64:
        print(f"? 地址 0x{addr:02X} 可以读取 0x64，可能是 WonderEcho")
    else:
        print(f"✗ 地址 0x{addr:02X} 不太像 WonderEcho")
    print('='*60)

def main():
    print("WonderEcho I2C 地址验证工具")
    print("=" * 60)
    print(f"Bus {BUS_ID} 上发现的设备: {[hex(a) for a in CANDIDATES]}")
    print("\n将逐个测试，验证哪个是 WonderEcho...")
    
    for addr in CANDIDATES:
        test_device(addr)
        time.sleep(1)
    
    print("\n\n" + "=" * 60)
    print("验证完成！")
    print("=" * 60)
    print("\n请根据以上测试结果判断:")
    print("1. 哪个地址能成功读取寄存器 0x64？")
    print("2. 哪个地址写入 0x6E 后有声音？")
    print("3. 那个地址就是 WonderEcho！")

if __name__ == "__main__":
    main()
