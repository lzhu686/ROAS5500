#!/usr/bin/env python3
"""测试 WonderEcho 语音播报功能

根据官方文档：
- 播报寄存器地址: 0x6E
- 类型 0x00: 命令词条播报语
- 类型 0xFF: 普通播报语（被动播报）

被动播报语ID：
- 150: 可回收物 -> 写入 0xFF 0x01
- 151: 厨余垃圾 -> 写入 0xFF 0x02
- 152: 有害垃圾 -> 写入 0xFF 0x03
- 153: 其他垃圾 -> 写入 0xFF 0x04
"""

import smbus
import time

# I2C 配置
I2C_BUS = 4          # MaixCam Pro 使用 bus 4
I2C_ADDR = 0x34      # WonderEcho 模块地址
SPEAK_REG = 0x6E     # 播报寄存器地址

# 播报类型
CMD_TYPE = 0x00      # 命令词条播报语
PASSIVE_TYPE = 0xFF  # 普通播报语（被动播报）

def speak(bus, cmd_type, phrase_id):
    """发送播报命令到 WonderEcho"""
    try:
        data = [cmd_type, phrase_id]
        bus.write_i2c_block_data(I2C_ADDR, SPEAK_REG, data)
        print(f"✓ 发送成功: 0x{cmd_type:02X} 0x{phrase_id:02X}")
        return True
    except OSError as e:
        print(f"✗ 发送失败: {e}")
        return False

def main():
    print("=" * 50)
    print("WonderEcho 播报测试")
    print("=" * 50)
    
    # 打开 I2C 总线
    try:
        bus = smbus.SMBus(I2C_BUS)
        print(f"✓ I2C 总线 {I2C_BUS} 打开成功")
    except Exception as e:
        print(f"✗ I2C 总线打开失败: {e}")
        return
    
    print()
    print("测试被动播报语（垃圾分类）:")
    print("-" * 50)
    
    # 测试播报 "其他垃圾" (ID 153 -> 0xFF 0x04)
    print("\n1. 播放 '其他垃圾' (0xFF 0x04)...")
    speak(bus, PASSIVE_TYPE, 0x04)
    time.sleep(3)  # 等待播放完成
    
    # 测试播报 "可回收物" (ID 150 -> 0xFF 0x01)
    print("\n2. 播放 '可回收物' (0xFF 0x01)...")
    speak(bus, PASSIVE_TYPE, 0x01)
    time.sleep(3)
    
    # 测试播报 "厨余垃圾" (ID 151 -> 0xFF 0x02)
    print("\n3. 播放 '厨余垃圾' (0xFF 0x02)...")
    speak(bus, PASSIVE_TYPE, 0x02)
    time.sleep(3)
    
    # 测试播报 "有害垃圾" (ID 152 -> 0xFF 0x03)
    print("\n4. 播放 '有害垃圾' (0xFF 0x03)...")
    speak(bus, PASSIVE_TYPE, 0x03)
    time.sleep(3)
    
    print()
    print("=" * 50)
    print("测试命令词条播报语:")
    print("-" * 50)
    
    # 测试命令词条播报语 "正在前进" (0x00 0x01)
    print("\n5. 播放命令词条 '正在前进' (0x00 0x01)...")
    speak(bus, CMD_TYPE, 0x01)
    time.sleep(3)
    
    print()
    print("=" * 50)
    print("测试完成!")
    print("=" * 50)
    
    bus.close()

if __name__ == "__main__":
    main()
