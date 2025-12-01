#!/usr/bin/python3
# coding=utf8
"""
测试 I2C 时序和延迟对播报的影响
"""
import smbus
import time
import os

I2C_ADDR = 0x34
ASR_SPEAK_ADDR = 0x6E
ASR_ANNOUNCER = 0xFF

def test_with_delays():
    """测试在 I2C 操作之间添加延迟"""
    print("=" * 60)
    print("测试方案 1: 在写入前后添加延迟")
    print("=" * 60)
    
    bus = smbus.SMBus(4)
    
    test_cases = [
        ("无延迟", 0.0, 0.0),
        ("写入前延迟 100ms", 0.1, 0.0),
        ("写入后延迟 100ms", 0.0, 0.1),
        ("前后各延迟 100ms", 0.1, 0.1),
        ("写入前延迟 500ms", 0.5, 0.0),
    ]
    
    for desc, pre_delay, post_delay in test_cases:
        print(f"\n测试: {desc}")
        print(f"  前延迟: {pre_delay}s, 后延迟: {post_delay}s")
        
        if pre_delay > 0:
            time.sleep(pre_delay)
        
        try:
            bus.write_i2c_block_data(I2C_ADDR, ASR_SPEAK_ADDR, [ASR_ANNOUNCER, 1])
            print("  ✓ I2C 写入成功")
        except Exception as e:
            print(f"  ✗ I2C 写入失败: {e}")
            continue
        
        if post_delay > 0:
            time.sleep(post_delay)
        
        print("  请听是否有'可回收物'播报...")
        time.sleep(3)
    
    bus.close()

def test_with_retries():
    """测试重复发送命令"""
    print("\n" + "=" * 60)
    print("测试方案 2: 重复发送相同命令")
    print("=" * 60)
    
    bus = smbus.SMBus(4)
    
    retry_counts = [1, 2, 3, 5]
    
    for count in retry_counts:
        print(f"\n发送 {count} 次相同命令...")
        
        for i in range(count):
            try:
                bus.write_i2c_block_data(I2C_ADDR, ASR_SPEAK_ADDR, [ASR_ANNOUNCER, 2])
                print(f"  第 {i+1} 次发送成功")
                time.sleep(0.05)  # 50ms 间隔
            except Exception as e:
                print(f"  第 {i+1} 次发送失败: {e}")
        
        print("  请听是否有'厨余垃圾'播报...")
        time.sleep(3)
    
    bus.close()

def test_command_before_announce():
    """测试先发送命令词播报，再发送普通播报"""
    print("\n" + "=" * 60)
    print("测试方案 3: 先发送命令词播报，再发送普通播报")
    print("=" * 60)
    
    bus = smbus.SMBus(4)
    
    ASR_COMMAND = 0x00
    
    print("\n1. 先播报命令词 '正在前进' (0x00, 0x01)...")
    try:
        bus.write_i2c_block_data(I2C_ADDR, ASR_SPEAK_ADDR, [ASR_COMMAND, 1])
        print("   ✓ 发送成功")
    except Exception as e:
        print(f"   ✗ 发送失败: {e}")
    
    time.sleep(3)
    
    print("\n2. 再播报普通语 '有害垃圾' (0xFF, 0x03)...")
    try:
        bus.write_i2c_block_data(I2C_ADDR, ASR_SPEAK_ADDR, [ASR_ANNOUNCER, 3])
        print("   ✓ 发送成功")
    except Exception as e:
        print(f"   ✗ 发送失败: {e}")
    
    time.sleep(3)
    
    bus.close()

def test_reset_before_speak():
    """测试先读取结果寄存器（模拟重置），再播报"""
    print("\n" + "=" * 60)
    print("测试方案 4: 先读取结果寄存器，再播报")
    print("=" * 60)
    
    bus = smbus.SMBus(4)
    
    ASR_RESULT_ADDR = 0x64
    
    print("\n读取结果寄存器 0x64...")
    try:
        result = bus.read_i2c_block_data(I2C_ADDR, ASR_RESULT_ADDR, 1)
        print(f"  读取到: {result}")
    except Exception as e:
        print(f"  读取失败: {e}")
    
    time.sleep(0.1)
    
    print("\n发送播报命令 '其他垃圾' (0xFF, 0x04)...")
    try:
        bus.write_i2c_block_data(I2C_ADDR, ASR_SPEAK_ADDR, [ASR_ANNOUNCER, 4])
        print("  ✓ 发送成功")
    except Exception as e:
        print(f"  ✗ 发送失败: {e}")
    
    print("  请听是否有'其他垃圾'播报...")
    time.sleep(3)
    
    bus.close()


if __name__ == "__main__":
    print("WonderEcho I2C 时序测试")
    print("本测试将尝试不同的 I2C 操作时序和模式")
    print("\n重要提示:")
    print("  - 请在安静环境中测试")
    print("  - 注意听 WonderEcho 是否有任何声音输出")
    print("  - 即使声音很小也请记录下来")
    print("\n3 秒后开始测试...")
    time.sleep(3)
    
    test_with_delays()
    test_with_retries()
    test_command_before_announce()
    test_reset_before_speak()
    
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
    print("\n如果以上所有测试都没有声音输出，说明:")
    print("  1. WonderEcho 固件可能不支持 I2C 被动播报")
    print("  2. 或者需要特殊的初始化/激活步骤")
    print("\n建议方案:")
    print("  - 使用 MaixCam 内置扬声器播放音频")
    print("  - 或联系厂商确认固件版本和被动播报支持")
