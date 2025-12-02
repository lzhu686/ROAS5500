import smbus
import time

# === 官方配置 ===
I2C_ADDR = 0x34
ASR_RESULT_ADDR = 100  # 官方文档明确指出是 100 (0x64)

def main():
    try:
        # MaixCam 的 I2C 总线通常是 4
        bus = smbus.SMBus(4)
    except Exception as e:
        print(f"无法打开 I2C 总线: {e}")
        return

    print(f"正在监听 WonderEcho (地址 0x{I2C_ADDR:02X})...")
    print(f"正在监视寄存器: {ASR_RESULT_ADDR} (0x{ASR_RESULT_ADDR:02X})")
    print("请尝试说: '小幻小幻', '开启垃圾分类', '前进', 'Go'")
    print("-" * 40)

    last_val = 0

    while True:
        try:
            # === 关键：完全复刻官方 speech_recognition.py 的读取方式 ===
            # 官方使用的是 read_i2c_block_data，读取 1 个字节
            data = bus.read_i2c_block_data(I2C_ADDR, ASR_RESULT_ADDR, 1)
            
            if data and len(data) > 0:
                val = data[0]
                
                # 只有当值不为 0 时才打印
                if val != 0:
                    print(f"【收到指令】 ID: {val} (0x{val:02X})")
                    last_val = val
                
                # 如果之前有值，现在变回0了，说明命令结束
                elif last_val != 0:
                    # print("指令结束")
                    last_val = 0
                    
        except Exception as e:
            print(f"读取错误: {e}")
            time.sleep(1)
            
        # 极短的延时，保证不错过信号
        time.sleep(0.05)

if __name__ == "__main__":
    main()