#!/usr/bin/python3
# coding=utf8
import smbus
import time
import struct

# 配置
I2C_ADDR = 0x34
BUS_ID = 4
ASR_SPEAK_ADDR = 0x6E
ASR_CMDMAND = 0x00
ASR_ANNOUNCER = 0xFF

def test_method(bus, method_name, send_func, cmd, id):
    """测试不同的发送方法"""
    print(f"\n[{method_name}] cmd={hex(cmd)}, id={hex(id)}")
    try:
        send_func(bus, cmd, id)
        print("  -> 已发送，等待 4 秒...")
        time.sleep(4)
        return True
    except Exception as e:
        print(f"  -> 失败: {e}")
        return False

def method1_write_i2c_block(bus, cmd, id):
    """方法1: write_i2c_block_data (标准SMBus)"""
    data = [cmd, id]
    bus.write_i2c_block_data(I2C_ADDR, ASR_SPEAK_ADDR, data)

def method2_write_word(bus, cmd, id):
    """方法2: write_word_data"""
    word = cmd | (id << 8)
    bus.write_word_data(I2C_ADDR, ASR_SPEAK_ADDR, word)

def method3_write_bytes_separately(bus, cmd, id):
    """方法3: 分两次 write_byte_data"""
    bus.write_byte_data(I2C_ADDR, ASR_SPEAK_ADDR, cmd)
    time.sleep(0.01)
    bus.write_byte_data(I2C_ADDR, ASR_SPEAK_ADDR + 1, id)

def method4_raw_i2c(bus, cmd, id):
    """方法4: 使用 write_block_data (原始数据块)"""
    # 尝试直接写入，不带寄存器地址
    try:
        # 这是一个hack：先写寄存器地址，然后写数据
        bus.write_byte(I2C_ADDR, ASR_SPEAK_ADDR)
        time.sleep(0.001)
        bus.write_byte(I2C_ADDR, cmd)
        time.sleep(0.001)
        bus.write_byte(I2C_ADDR, id)
    except:
        raise

def main():
    print("MaixCam I2C 多方法播报测试")
    print("=" * 50)
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开总线 {BUS_ID}: {e}")
        return
    
    methods = [
        ("write_i2c_block_data (官方方法)", method1_write_i2c_block),
        ("write_word_data", method2_write_word),
        ("两次 write_byte_data", method3_write_bytes_separately),
        ("原始 I2C 写入", method4_raw_i2c),
    ]
    
    # 测试数据
    tests = [
        ("命令词: 我在", ASR_CMDMAND, 3),
        ("播报语: 可回收物", ASR_ANNOUNCER, 1),
    ]
    
    print("策略: 对每个播报测试所有4种方法")
    print("-" * 50)
    
    for test_name, cmd, id in tests:
        print(f"\n{'='*50}")
        print(f"测试内容: {test_name}")
        print(f"{'='*50}")
        
        for method_name, method_func in methods:
            test_method(bus, method_name, method_func, cmd, id)
        
        print(f"\n{test_name} 的所有方法测试完毕。")
        print("如果听到声音，请记录是哪个方法！")
        time.sleep(2)
    
    print("\n" + "=" * 50)
    print("全部测试结束。")
    print("\n请报告:")
    print("1. 哪个方法有声音？")
    print("2. 如果都没声音，模块单独供电时正常吗？")

if __name__ == "__main__":
    main()
