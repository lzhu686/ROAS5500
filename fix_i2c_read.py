import smbus
import time

# 配置
BUS_ID = 4
DEVICE_ADDR = 0x34
REG_RESULT = 0x64  # 100

def arduino_style_read(bus, addr, reg):
    """
    模拟 Arduino 的读取方式：
    1. 发送寄存器地址 + STOP 信号
    2. 发送读取请求
    
    标准 SMBus read_byte_data 使用 Repeated Start (中间没有 STOP)，
    很多单片机模拟的 I2C 从机处理不过来，必须用这种分步方式。
    """
    try:
        # 第一步：写入寄存器地址 (相当于 Arduino 的 beginTransmission + write + endTransmission)
        # 这会产生一个 STOP 信号，告诉模块"我要操作这个寄存器了，请准备好"
        bus.write_byte(addr, reg)
        
        # 稍微等一下，给模块反应时间
        time.sleep(0.001)
        
        # 第二步：直接读取 (相当于 Arduino 的 requestFrom)
        # 这会发起一个新的 START 信号读取数据
        val = bus.read_byte(addr)
        return val
    except Exception as e:
        # print(f"I2C Error: {e}")
        return 0

def main():
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开 I2C 总线: {e}")
        return

    print(f"正在监听 WonderEcho (地址 0x{DEVICE_ADDR:02X})...")
    print(f"使用 [Arduino 分步读取模式] 监视寄存器 0x{REG_RESULT:02X}")
    print("请尝试说: '小幻小幻' (预期 ID: 3) 或 '开启垃圾分类' (预期 ID: 100)")
    print("-" * 60)

    last_val = 0
    
    try:
        while True:
            # 使用分步读取
            val = arduino_style_read(bus, DEVICE_ADDR, REG_RESULT)
            
            if val != 0:
                print(f"【收到指令】 ID: {val} (0x{val:02X})")
                last_val = val
                # 简单的防抖，避免刷屏
                time.sleep(0.2)
            
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n停止监听")

if __name__ == "__main__":
    main()
