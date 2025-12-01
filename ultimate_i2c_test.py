import smbus
import time

# 配置
BUS_ID = 4
TARGET_ADDR = 0x34
REG_SPEAK = 0x6E  # 110

def test_method_1(bus, sound_id):
    """方法1: write_word_data 小端序 (Low=0xFF, High=ID)"""
    word_val = 0xFF | (sound_id << 8)
    bus.write_word_data(TARGET_ADDR, REG_SPEAK, word_val)
    print(f"    -> Word值: {hex(word_val)} (预期线序: FF {hex(sound_id)})")

def test_method_2(bus, sound_id):
    """方法2: write_word_data 大端序 (Low=ID, High=0xFF)"""
    word_val = sound_id | (0xFF << 8)
    bus.write_word_data(TARGET_ADDR, REG_SPEAK, word_val)
    print(f"    -> Word值: {hex(word_val)} (预期线序: {hex(sound_id)} FF)")

def test_method_3(bus, sound_id):
    """方法3: 分两次 write_byte_data (先0xFF, 后ID)"""
    bus.write_byte_data(TARGET_ADDR, REG_SPEAK, 0xFF)
    time.sleep(0.01)
    bus.write_byte_data(TARGET_ADDR, REG_SPEAK + 1, sound_id)
    print(f"    -> 两次写入: [0x6E]=FF, [0x6F]={hex(sound_id)}")

def test_method_4(bus, sound_id):
    """方法4: write_i2c_block_data (尽管有长度字节，但试试看)"""
    data = [0xFF, sound_id]
    bus.write_i2c_block_data(TARGET_ADDR, REG_SPEAK, data)
    print(f"    -> Block写入: {[hex(d) for d in data]}")

def main():
    print("MaixCam I2C 被动播报终极诊断")
    print("=" * 50)
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开总线 {BUS_ID}: {e}")
        return

    # 只测试 ID 1 (可回收物)
    sound_id = 0x01
    
    methods = [
        ("write_word_data 小端序", test_method_1),
        ("write_word_data 大端序", test_method_2),
        ("两次 write_byte_data", test_method_3),
        ("write_i2c_block_data", test_method_4),
    ]
    
    print(f"测试播报 ID: {hex(sound_id)} (可回收物)")
    print("每种方法测试后等待 5 秒，请仔细听...")
    print("-" * 50)
    
    for i, (name, func) in enumerate(methods, 1):
        print(f"\n[方法 {i}] {name}")
        try:
            func(bus, sound_id)
            print("  -> 等待 5 秒 (请听是否有声音)...")
            time.sleep(5)
        except Exception as e:
            print(f"  -> 失败: {e}")
            time.sleep(1)
    
    print("\n" + "=" * 50)
    print("测试结束。")
    print("\n请报告:")
    print("1. 哪个方法有声音？")
    print("2. 你的模块供电电压是多少？(用万用表测量 VCC 和 GND)")

if __name__ == "__main__":
    main()
