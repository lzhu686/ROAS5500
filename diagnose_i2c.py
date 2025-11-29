#!/usr/bin/env python3
"""诊断 WonderEcho I2C 连接问题

扫描所有 I2C 总线，找到 WonderEcho 模块，并尝试发送播报命令
"""

import time

# 尝试导入 smbus
try:
    import smbus
    print("✓ smbus 模块导入成功")
except ImportError:
    print("✗ smbus 模块未安装")
    print("  尝试: pip install smbus2")
    exit(1)

# I2C 配置
SPEAK_REG = 0x6E     # 播报寄存器地址
RESULT_REG = 0x64    # 识别结果寄存器

def scan_bus(bus_id):
    """扫描指定 I2C 总线上的所有设备"""
    devices = []
    try:
        bus = smbus.SMBus(bus_id)
        for addr in range(0x03, 0x78):
            try:
                bus.read_byte(addr)
                devices.append(addr)
            except:
                pass
        bus.close()
    except Exception as e:
        return None, str(e)
    return devices, None

def test_speak(bus_id, addr, cmd_type, phrase_id):
    """测试播报功能"""
    try:
        bus = smbus.SMBus(bus_id)
        data = [cmd_type, phrase_id]
        bus.write_i2c_block_data(addr, SPEAK_REG, data)
        bus.close()
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("WonderEcho I2C 诊断工具")
    print("=" * 60)
    
    # 扫描所有可能的 I2C 总线 (0-7)
    print("\n[1] 扫描 I2C 总线...")
    print("-" * 60)
    
    found_buses = {}
    for bus_id in range(8):
        devices, error = scan_bus(bus_id)
        if devices is not None:
            if devices:
                print(f"  Bus {bus_id}: 找到设备 {[hex(d) for d in devices]}")
                found_buses[bus_id] = devices
            else:
                print(f"  Bus {bus_id}: 无设备")
        else:
            print(f"  Bus {bus_id}: 无法打开 ({error})")
    
    # 检查是否找到 0x34 地址
    print("\n[2] 查找 WonderEcho (0x34)...")
    print("-" * 60)
    
    wonderecho_bus = None
    wonderecho_addr = 0x34
    
    for bus_id, devices in found_buses.items():
        if wonderecho_addr in devices:
            wonderecho_bus = bus_id
            print(f"  ✓ 在 Bus {bus_id} 找到 WonderEcho (0x34)")
            break
    
    if wonderecho_bus is None:
        print("  ✗ 未找到 WonderEcho (0x34)")
        print("\n  可能原因:")
        print("    1. WonderEcho 模块未正确连接")
        print("    2. I2C 地址被修改过")
        print("    3. 模块电源未接通")
        
        # 检查是否有其他可疑设备
        all_devices = []
        for devices in found_buses.values():
            all_devices.extend(devices)
        
        if all_devices:
            print(f"\n  发现其他设备: {[hex(d) for d in set(all_devices)]}")
            print("  如果 WonderEcho 地址被修改，可能是上述地址之一")
        return
    
    # 测试播报功能
    print(f"\n[3] 测试播报功能 (Bus {wonderecho_bus}, Addr 0x34)...")
    print("-" * 60)
    
    # 先读取一下结果寄存器，确认通信正常
    try:
        bus = smbus.SMBus(wonderecho_bus)
        result = bus.read_i2c_block_data(wonderecho_addr, RESULT_REG, 1)
        print(f"  ✓ 读取结果寄存器成功: {result}")
        bus.close()
    except Exception as e:
        print(f"  ✗ 读取结果寄存器失败: {e}")
    
    # 测试播报
    test_cases = [
        (0x00, 0x01, "命令词条: 正在前进"),
        (0x00, 0x03, "命令词条: 正在左转"),
        (0xFF, 0x01, "播报语: 可回收物"),
        (0xFF, 0x02, "播报语: 厨余垃圾"),
        (0xFF, 0x03, "播报语: 有害垃圾"),
        (0xFF, 0x04, "播报语: 其他垃圾"),
    ]
    
    print("\n  即将测试以下播报（每个间隔3秒）:")
    for cmd, phrase_id, desc in test_cases:
        print(f"    - {desc} (0x{cmd:02X} 0x{phrase_id:02X})")
    
    print("\n  3秒后开始测试...")
    time.sleep(3)
    
    for cmd, phrase_id, desc in test_cases:
        print(f"\n  播放: {desc}")
        success, error = test_speak(wonderecho_bus, wonderecho_addr, cmd, phrase_id)
        if success:
            print(f"    ✓ I2C 发送成功 (0x{cmd:02X} 0x{phrase_id:02X})")
        else:
            print(f"    ✗ I2C 发送失败: {error}")
        
        print("    等待 3 秒...")
        time.sleep(3)
    
    print("\n" + "=" * 60)
    print("诊断完成!")
    print("=" * 60)
    print("\n如果 I2C 发送成功但没有声音，可能原因:")
    print("  1. WonderEcho 固件中没有对应的播报语音文件")
    print("  2. 播报语 ID 与固件不匹配")
    print("  3. WonderEcho 扬声器故障")
    print("  4. 需要先唤醒模块 (说'小幻小幻')")

if __name__ == "__main__":
    main()
