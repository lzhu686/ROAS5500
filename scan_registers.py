import smbus
import time

# 配置
BUS_ID = 4
TARGET_ADDR = 0x34

def test_register(bus, reg_addr, cmd_type, sound_id, desc):
    """测试指定寄存器"""
    print(f"\n[测试] 寄存器 {hex(reg_addr)} - {desc}")
    
    try:
        # 方法1: write_word_data (小端序: 先cmd_type, 后sound_id)
        word_val = cmd_type | (sound_id << 8)
        bus.write_word_data(TARGET_ADDR, reg_addr, word_val)
        print(f"  方法1 (word): 已发送 [{hex(cmd_type)}, {hex(sound_id)}]")
        time.sleep(3)
        
    except Exception as e:
        print(f"  方法1 失败: {e}")
    
    try:
        # 方法2: write_i2c_block_data
        data = [cmd_type, sound_id]
        bus.write_i2c_block_data(TARGET_ADDR, reg_addr, data)
        print(f"  方法2 (block): 已发送 {[hex(d) for d in data]}")
        time.sleep(3)
        
    except Exception as e:
        print(f"  方法2 失败: {e}")

def main():
    print("MaixCam I2C 寄存器地址扫描测试")
    print("=" * 50)
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开总线 {BUS_ID}: {e}")
        return
    
    print("测试目标: 播报'我在' (ID=0x03, cmd=0x00)")
    print("策略: 尝试多个可能的寄存器地址")
    print("-" * 50)
    
    # 测试多个可能的寄存器地址
    registers_to_test = [
        (0x6E, "官方文档提到的播报寄存器"),
        (0x55, "协议包中的 0x55"),
        (0x01, "控制寄存器候选1"),
        (0x02, "控制寄存器候选2"),
        (0x10, "控制寄存器候选3"),
        (0x20, "控制寄存器候选4"),
    ]
    
    # 先测试"我在"命令（应该能听到声音）
    print("\n【第一轮】测试主动播报命令: '我在' (cmd=0x00, id=0x03)")
    for reg, desc in registers_to_test:
        test_register(bus, reg, 0x00, 0x03, desc)
        print("  -> 如果听到'我在'，请立即记录寄存器地址！")
    
    print("\n" + "=" * 50)
    print("第一轮测试结束。如果找到有效寄存器，继续第二轮...")
    input("按回车继续测试被动播报...")
    
    # 第二轮: 测试被动播报
    print("\n【第二轮】测试被动播报: '可回收物' (cmd=0xFF, id=0x01)")
    for reg, desc in registers_to_test:
        test_register(bus, reg, 0xFF, 0x01, desc)
        print("  -> 如果听到'可回收物'，请立即记录寄存器地址！")
    
    print("\n" + "=" * 50)
    print("测试结束。")
    print("\n请报告:")
    print("1. 哪个寄存器能播放'我在'？")
    print("2. 哪个寄存器能播放'可回收物'？")
    print("3. 是方法1还是方法2有效？")

if __name__ == "__main__":
    main()
