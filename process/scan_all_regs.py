import smbus
import time

BUS_ID = 4
DEVICE_ADDR = 0x34

def read_all_regs(bus):
    values = {}
    for reg in range(0, 256):
        try:
            # 尝试用标准读取
            val = bus.read_byte_data(DEVICE_ADDR, reg)
            values[reg] = val
        except:
            values[reg] = -1
    return values

def main():
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开 I2C 总线: {e}")
        return

    print(f"正在连接 WonderEcho (0x{DEVICE_ADDR:02X})...")
    
    # 1. 读取基准值
    print("正在读取基准状态 (请保持安静)...")
    base_values = read_all_regs(bus)
    print("基准读取完成。")
    print("-" * 50)
    
    # 2. 等待触发
    print("【请现在对着模块说：'小幻小幻'】")
    print("确保模块灯亮起或回答后...")
    print("3秒后自动开始扫描，请抓紧时间说话！")
    
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    # 3. 读取触发后的值
    print("正在扫描变化...")
    new_values = read_all_regs(bus)
    
    print("-" * 50)
    print(f"{'寄存器':<10} | {'旧值':<10} | {'新值':<10} | {'变化'}")
    print("-" * 50)
    
    found_candidate = False
    for reg in range(0, 256):
        old = base_values[reg]
        new = new_values[reg]
        
        # 过滤掉读取失败的
        if old == -1 or new == -1:
            continue
            
        # 我们只关心变成了 3 (唤醒) 或 100 (命令) 的寄存器
        # 或者是从 0 变成了某个非零值
        if new != old:
            # 重点关注变成 3 的寄存器
            marker = ""
            if new == 3:
                marker = "<--- 可能是唤醒词 ID !!!"
                found_candidate = True
            elif new == 100 or new == 0x64:
                marker = "<--- 可能是命令词 ID !!!"
                found_candidate = True
            elif abs(new - old) > 20:
                # 忽略大幅跳动的值（通常是噪声）
                continue
                
            print(f"0x{reg:02X} ({reg:3d}) | {old:3d}        | {new:3d}        | {marker}")

    if not found_candidate:
        print("\n未找到明显的 ID 寄存器。")
        print("可能原因：")
        print("1. 模块未识别到语音（灯没亮？）")
        print("2. 寄存器自动清零太快，扫描时已经变回 0 了")

if __name__ == "__main__":
    main()
