import smbus
import time

# 配置
BUS_ID = 4
DEVICE_ADDR = 0x34

# 目标寄存器
REG_RESULT = 0x64  # 官方文档结果寄存器
REG_NOISE = 0x39   # 之前发现的噪声寄存器

def read_split(bus, addr, reg):
    """尝试使用 '分步读取' (Write Reg -> Stop -> Read Data)"""
    try:
        # 1. 写入寄存器地址 (不带数据)
        bus.write_byte(addr, reg)
        # 2. 直接读取一个字节
        return bus.read_byte(addr)
    except Exception as e:
        return -1

def main():
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开 I2C 总线: {e}")
        return

    print(f"正在监听 WonderEcho (地址 0x{DEVICE_ADDR:02X})...")
    print("尝试两种读取方式监听 0x64 (结果寄存器)")
    print("请对着模块说：'小幻小幻' 或 '开启垃圾分类'")
    print("-" * 70)
    print(f"{'时间':<10} | {'Std 0x64':<10} | {'Split 0x64':<10} | {'Reg 0x39':<10}")
    print("-" * 70)

    last_val = -1

    try:
        while True:
            # 1. 标准读取 (Repeated Start)
            try:
                std_val = bus.read_byte_data(DEVICE_ADDR, REG_RESULT)
            except:
                std_val = -1

            # 2. 分步读取 (Stop-Start)
            split_val = read_split(bus, DEVICE_ADDR, REG_RESULT)

            # 3. 读取噪声寄存器 (作为参考)
            try:
                noise_val = bus.read_byte_data(DEVICE_ADDR, REG_NOISE)
            except:
                noise_val = -1

            # 格式化
            row_str = f"{time.strftime('%H:%M:%S'):<10} | "
            row_str += f"{std_val:<10} | "
            row_str += f"{split_val:<10} | "
            row_str += f"{noise_val:<10}"

            # 只有当 0x64 有非零值时，或者每2秒打印一次心跳
            if (std_val > 0 and std_val < 255) or (split_val > 0 and split_val < 255):
                print(row_str + " <--- 收到信号！！！")
            elif int(time.time() * 10) % 20 == 0: 
                 print(row_str)
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n停止监听")

if __name__ == "__main__":
    main()
