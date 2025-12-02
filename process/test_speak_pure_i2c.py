import smbus
import time

# 配置
BUS_ID = 4
TARGET_ADDR = 0x34
REG_SPEAK = 0x6E  # 110
CMD_ANNOUNCER = 0xFF

def main():
    print("MaixCam I2C 语音播报测试工具 (Pure I2C Mode)")
    print("=" * 40)
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开总线 {BUS_ID}: {e}")
        return

    # 测试播报
    ids_to_test = [1, 2, 3, 4, 5]
    
    print(f"目标地址: {hex(TARGET_ADDR)}")
    print(f"写入寄存器: {REG_SPEAK} (0x6E)")
    print("模式: 使用 write_word_data 模拟纯 I2C 写入 (避免发送长度字节)")
    print("准备开始测试播报...")
    
    for sound_id in ids_to_test:
        print(f"\n[测试] 发送播放命令 ID: {sound_id}")
        
        # 我们需要发送两个字节: [0xFF, sound_id]
        # SMBus write_word_data 发送顺序是: [Reg] [LowByte] [HighByte]
        # 所以我们将 0xFF 设为低字节，sound_id 设为高字节
        
        word_val = CMD_ANNOUNCER | (sound_id << 8)
        
        try:
            # 使用 write_word_data
            # 预期线序: [0x34] [0x6E] [0xFF] [sound_id]
            bus.write_word_data(TARGET_ADDR, REG_SPEAK, word_val)
            
            print(f"  -> 已发送 Word 值: {hex(word_val)} (Low: {hex(CMD_ANNOUNCER)}, High: {hex(sound_id)})")
            print("  -> 等待 3 秒...")
            time.sleep(3)
            
        except Exception as e:
            print(f"  -> 发送失败: {e}")
            
    print("\n测试结束。")

if __name__ == "__main__":
    main()
