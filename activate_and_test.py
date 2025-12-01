import smbus
import time

# 配置
BUS_ID = 4
TARGET_ADDR = 0x34
REG_SPEAK = 0x6E  # 110

def send_speak_command(bus, cmd_type, sound_id):
    """发送播报命令
    cmd_type: 0x00=控制命令, 0xFF=播报语
    """
    word_val = cmd_type | (sound_id << 8)
    bus.write_word_data(TARGET_ADDR, REG_SPEAK, word_val)
    print(f"    -> 已发送: [{hex(cmd_type)}, {hex(sound_id)}]")

def main():
    print("MaixCam I2C 播报功能激活测试")
    print("=" * 50)
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开总线 {BUS_ID}: {e}")
        return

    print("策略: 先发送控制命令激活播报，再测试被动播报\n")
    
    # 步骤 1: 尝试"开启播报"命令 (ID 9)
    print("[步骤 1] 发送'开启播报'命令 (ID=0x09)")
    try:
        send_speak_command(bus, 0x00, 0x09)  # AA 55 00 09 FB 对应
        print("  -> 等待 2 秒...")
        time.sleep(2)
    except Exception as e:
        print(f"  -> 失败: {e}")
    
    # 步骤 2: 尝试"最大音量"命令 (ID 6)
    print("\n[步骤 2] 发送'最大音量'命令 (ID=0x06)")
    try:
        send_speak_command(bus, 0x00, 0x06)  # AA 55 00 06 FB 对应
        print("  -> 等待 2 秒...")
        time.sleep(2)
    except Exception as e:
        print(f"  -> 失败: {e}")
    
    # 步骤 3: 发送"我在"命令（模拟唤醒词响应）
    print("\n[步骤 3] 发送'我在'命令 (ID=0x03, 模拟唤醒)")
    try:
        send_speak_command(bus, 0x00, 0x03)  # AA 55 00 03 FB 对应
        print("  -> 等待 3 秒 (应该听到'我在')...")
        time.sleep(3)
    except Exception as e:
        print(f"  -> 失败: {e}")
    
    # 步骤 4: 测试被动播报
    print("\n[步骤 4] 测试被动播报")
    
    播报列表 = [
        (0x01, "可回收物"),
        (0x02, "厨余垃圾"),
        (0x03, "有害垃圾"),
        (0x04, "其他垃圾"),
    ]
    
    for sound_id, name in 播报列表:
        print(f"\n  -> 播报: {name} (ID={hex(sound_id)})")
        try:
            send_speak_command(bus, 0xFF, sound_id)  # AA 55 FF [ID] FB 对应
            print("     等待 3 秒...")
            time.sleep(3)
        except Exception as e:
            print(f"     失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试结束。")
    print("\n请报告:")
    print("1. 步骤 3 能听到'我在'吗?")
    print("2. 步骤 4 能听到垃圾分类播报吗?")
    print("3. 如果都没声音，模块单独 Type-C 供电时能正常唤醒和播报吗?")

if __name__ == "__main__":
    main()
