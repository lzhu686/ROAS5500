import smbus
import time

# 配置
BUS_ID = 4
TARGET_ADDR = 0x34
REG_RESULT = 0x64  # 100

def main():
    print("MaixCam I2C 修复与监听工具")
    print("=" * 40)
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开总线 {BUS_ID}: {e}")
        return

    # 1. 尝试强制清除寄存器
    print("正在尝试清除寄存器状态...")
    try:
        # 写入 0
        bus.write_byte_data(TARGET_ADDR, REG_RESULT, 0x00)
        time.sleep(0.1)
        
        # 读取验证
        val = bus.read_byte_data(TARGET_ADDR, REG_RESULT)
        print(f"清除后寄存器值: {val}")
        
        if val == 0:
            print("✓ 寄存器已成功复位为 0")
        else:
            print(f"✗ 寄存器无法复位，当前仍为: {val}")
            print("尝试多次写入 0...")
            for _ in range(5):
                bus.write_byte_data(TARGET_ADDR, REG_RESULT, 0x00)
                time.sleep(0.05)
            val_retry = bus.read_byte_data(TARGET_ADDR, REG_RESULT)
            print(f"重试后值: {val_retry}")

    except Exception as e:
        print(f"写入失败: {e}")

    # 2. 监听模式
    print("\n[进入监听模式]")
    print("请说出 '小幻小幻'，观察数值是否变为 1, 2, 3 等...")
    print("按 Ctrl+C 退出...")
    
    last_val = -1
    
    try:
        while True:
            try:
                val = bus.read_byte_data(TARGET_ADDR, REG_RESULT)
                
                if val != 0:
                    print(f"!!! 收到信号: {val} (Hex: {hex(val)})")
                    
                    # 收到信号后，尝试手动清除，模拟“处理完毕”
                    # 注意：官方例程没有清除，但如果这是锁存寄存器，可能需要清除
                    # 我们先观察它是否会自动消失。如果一直卡在某个值，我们再开启自动清除。
                    
                    # 策略：如果值连续出现超过 10 次（约0.5秒），则强制清除
                    # 这里先简单打印
                    
                if val != last_val:
                    print(f"   [状态变更] {last_val} -> {val}")
                    last_val = val
                
                time.sleep(0.05)
                
            except OSError:
                pass
            except KeyboardInterrupt:
                break
            
    except KeyboardInterrupt:
        print("\n停止")

if __name__ == "__main__":
    main()
