import smbus
import time

# === 配置 ===
BUS_ID = 4
DEVICE_ADDR = 0x34
REG_SPEAK = 0x6E

# 播报类型
TYPE_CMD = 0x00       # 命令词回复
TYPE_BROADCAST = 0xFF # 普通播报词

def speak_pure_i2c(bus, phrase_id):
    """
    使用 write_word_data 模拟 "纯 I2C" 写操作。
    
    目标时序: [地址] [寄存器0x6E] [0xFF] [ID]
    
    write_word_data 的标准时序:
    [地址] [寄存器] [低8位] [高8位]
    
    因此我们需要构造一个 16位整数:
    低8位 = 0xFF (播报类型)
    高8位 = ID   (词条编号)
    """
    try:
        # 构造数据: Low=0xFF, High=ID
        # 比如 ID=1, value = 0x01FF
        value = (phrase_id << 8) | TYPE_BROADCAST
        
        print(f"发送指令: Reg=0x{REG_SPEAK:02X}, Val=0x{value:04X} (Low=0xFF, High=0x{phrase_id:02X})")
        
        # 这会发送: [0x34] [0x6E] [0xFF] [ID]
        bus.write_word_data(DEVICE_ADDR, REG_SPEAK, value)
        return True
    except Exception as e:
        print(f"写入失败: {e}")
        return False

def main():
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开 I2C 总线: {e}")
        return

    print("=== WonderEcho 纯 I2C 播报测试 ===")
    print("注意：请确保模块供电电压为 5V，否则扬声器可能沙哑或不工作")
    print("-" * 40)

    # 测试几个常用的 ID
    # 假设: 1=可回收物, 2=厨余垃圾 (具体ID需参考你的固件列表)
    test_ids = [1, 2, 3] 

    for pid in test_ids:
        print(f"\n正在请求播报 ID: {pid}")
        speak_pure_i2c(bus, pid)
        
        # 给它一点时间说完
        time.sleep(3)

    print("\n测试结束")

if __name__ == "__main__":
    main()
