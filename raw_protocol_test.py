import smbus
import time

# 配置
BUS_ID = 4
TARGET_ADDR = 0x34

def test_raw_command(bus, reg, data_bytes, desc):
    """发送原始字节序列"""
    print(f"\n[测试] {desc}")
    print(f"  寄存器: {hex(reg)}, 数据: {[hex(b) for b in data_bytes]}")
    
    try:
        if len(data_bytes) == 1:
            bus.write_byte_data(TARGET_ADDR, reg, data_bytes[0])
        elif len(data_bytes) == 2:
            word = data_bytes[0] | (data_bytes[1] << 8)
            bus.write_word_data(TARGET_ADDR, reg, word)
        else:
            bus.write_i2c_block_data(TARGET_ADDR, reg, data_bytes)
        
        print("  -> 已发送，等待 3 秒...")
        time.sleep(3)
        return True
        
    except Exception as e:
        print(f"  -> 失败: {e}")
        return False

def main():
    print("MaixCam I2C 原始协议测试")
    print("=" * 50)
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开总线 {BUS_ID}: {e}")
        return
    
    print("策略: 尝试多种可能的协议格式")
    print("-" * 50)
    
    # 测试多种可能的格式
    # 根据串口协议 AA 55 00 03 FB (我在)
    # 可能 I2C 需要发送完整的包，或者部分包
    
    tests = [
        # 格式1: 只发数据部分 [cmd, id]
        (0x6E, [0x00, 0x03], "格式1: 寄存器0x6E, 数据[0x00, 0x03]"),
        (0x6E, [0x03, 0x00], "格式1-反序: 寄存器0x6E, 数据[0x03, 0x00]"),
        
        # 格式2: 发送完整帧（去掉帧头AA 55和帧尾FB）
        (0x00, [0x00, 0x03], "格式2: 寄存器0x00, 数据[0x00, 0x03]"),
        
        # 格式3: 发送包括帧头的完整数据
        (0x55, [0x00, 0x03, 0xFB], "格式3: 寄存器0x55, 数据[0x00, 0x03, 0xFB]"),
        
        # 格式4: 单字节命令（只发ID）
        (0x6E, [0x03], "格式4: 寄存器0x6E, 单字节0x03"),
        (0x03, [0x00], "格式4-变体: 用ID作寄存器, 写0x00"),
        
        # 格式5: 尝试写入完整的5字节协议
        (0xAA, [0x55, 0x00, 0x03, 0xFB], "格式5: 寄存器0xAA, 完整帧"),
        
        # 格式6: 被动播报格式测试
        (0x6E, [0xFF, 0x01], "格式6: 寄存器0x6E, 被动播报[0xFF, 0x01]"),
        (0x6E, [0x01, 0xFF], "格式6-反序: 寄存器0x6E, [0x01, 0xFF]"),
    ]
    
    print("\n开始测试 (仔细听每次是否有声音)...\n")
    
    for reg, data, desc in tests:
        test_raw_command(bus, reg, data, desc)
    
    print("\n" + "=" * 50)
    print("测试结束。")
    print("\n如果仍然没有声音，请向官方确认:")
    print("1. I2C 模式下，播报功能是否需要特殊初始化?")
    print("2. 是否需要先通过某个寄存器切换到'播报模式'?")
    print("3. 能否提供完整的 I2C 通信时序图或抓包数据?")

if __name__ == "__main__":
    main()
