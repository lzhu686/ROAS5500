import smbus
import time

BUS_ID = 4
DEVICE_ADDR = 0x34
REG_RESULT = 0x64  # 100

def main():
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开 I2C 总线: {e}")
        return

    print(f"正在极速监听 WonderEcho (0x{DEVICE_ADDR:02X}) 的寄存器 0x{REG_RESULT:02X}...")
    print("请对着模块连续说话：'小幻小幻'、'开启垃圾分类'")
    print("如果模块灯亮了但这里没输出，说明寄存器地址不对。")
    print("-" * 50)

    last_val = -1
    count = 0

    try:
        while True:
            try:
                # 使用 read_byte_data (既然 scan_all_regs 证明它能读到数据)
                val = bus.read_byte_data(DEVICE_ADDR, REG_RESULT)
                
                # 只要不是 0，就打印！
                if val != 0:
                    print(f"【抓到了！】 寄存器 0x64 = {val} (0x{val:02X})")
                    # 简单的防抖
                    if val == last_val:
                        pass 
                    else:
                        last_val = val
                
                # 每 1000 次打印一个点，证明程序还在跑
                count += 1
                if count % 1000 == 0:
                    print(".", end="", flush=True)
                    
                # 极短延时，保证采样率
                time.sleep(0.005)

            except Exception as e:
                # 忽略偶尔的 I2C 错误
                pass

    except KeyboardInterrupt:
        print("\n停止监听")

if __name__ == "__main__":
    main()
