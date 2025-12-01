import smbus
import time

# 配置
BUS_ID = 4
TARGET_ADDR = 0x34
REG_SPEAK = 0x6E  # 110
CMD_ANNOUNCER = 0xFF

def main():
    print("MaixCam I2C 语音播报测试工具")
    print("=" * 40)
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开总线 {BUS_ID}: {e}")
        return

    # 测试播报
    # 尝试播放 ID 1 到 5
    # 通常 ID 1 是 "我在" 或 "你好"
    # ID 2 是 "操作成功" 等
    
    ids_to_test = [1, 2, 3, 4, 5]
    
    print(f"目标地址: {hex(TARGET_ADDR)}")
    print(f"写入寄存器: {REG_SPEAK} (0x6E)")
    print("准备开始测试播报...")
    
    for sound_id in ids_to_test:
        print(f"\n[测试] 发送播放命令 ID: {sound_id}")
        
        # 构造数据: [命令类型, 词条ID]
        data = [CMD_ANNOUNCER, sound_id]
        
        try:
            # 使用 write_i2c_block_data 发送
            # 对应官方: wire_write_data_array(ASR_SPEAK_ADDR, [cmd, id], 2)
            bus.write_i2c_block_data(TARGET_ADDR, REG_SPEAK, data)
            print(f"  -> 已发送数据: {data}")
            print("  -> 等待 3 秒 (请听是否有声音)...")
            time.sleep(3)
            
        except Exception as e:
            print(f"  -> 发送失败: {e}")
            
    print("\n测试结束。")

if __name__ == "__main__":
    main()
