import smbus
import time
import os

# 配置
BUS_ID = 4
TARGET_ADDR = 0x34
REG_RESULT = 0x64

def scan_bus(bus_num):
    print(f"\n[扫描] 正在扫描 I2C 总线 {bus_num} ...")
    try:
        bus = smbus.SMBus(bus_num)
    except Exception as e:
        print(f"  无法打开总线 {bus_num}: {e}")
        return []

    found_devices = []
    # 扫描标准地址范围
    for addr in range(0x03, 0x78):
        try:
            # 尝试读取一个字节来检测设备
            bus.read_byte(addr)
            found_devices.append(addr)
        except:
            pass
            
    if found_devices:
        print(f"  发现设备: {[hex(d) for d in found_devices]}")
    else:
        print("  未发现设备")
        
    return found_devices

def test_register_read(bus_num, addr):
    print(f"\n[测试] 监听设备 {hex(addr)} 寄存器 {hex(REG_RESULT)} ...")
    print("请对着模块说 '小幻小幻' ... (持续 10 秒)")
    
    try:
        bus = smbus.SMBus(bus_num)
    except:
        return

    start_time = time.time()
    while time.time() - start_time < 10:
        try:
            # 方法 1: read_i2c_block_data
            block = bus.read_i2c_block_data(addr, REG_RESULT, 1)
            val1 = block[0] if block else None
            
            # 方法 2: read_byte_data
            try:
                val2 = bus.read_byte_data(addr, REG_RESULT)
            except:
                val2 = None
                
            if (val1 is not None and val1 != 0) or (val2 is not None and val2 != 0):
                print(f"  !!! 读到数据 !!! Block: {val1}, Byte: {val2}")
            
            # 稍微延时
            time.sleep(0.05)
            
        except Exception as e:
            print(f"  读取错误: {e}")
            time.sleep(0.5)
            
    print("监听结束")

def main():
    print("MaixCam I2C 诊断工具 v2")
    print("=" * 40)
    
    # 1. 扫描总线 4
    devices = scan_bus(BUS_ID)
    
    if TARGET_ADDR in devices:
        print(f"\n✓ 成功找到 WonderEcho 模块 (地址 {hex(TARGET_ADDR)})")
        print("通信链路正常！")
        
        # 2. 尝试读取数据
        test_register_read(BUS_ID, TARGET_ADDR)
        
    else:
        print(f"\n✗ 未找到 WonderEcho 模块 (地址 {hex(TARGET_ADDR)})")
        print("可能原因：")
        print("1. 接线松动或接错 (SDA/SCL 接反？)")
        print("2. 模块未供电")
        print("3. 总线编号错误 (尝试扫描其他总线...)")
        
        # 尝试扫描其他可能的总线
        for b in [0, 1, 2, 3, 5]:
            devs = scan_bus(b)
            if TARGET_ADDR in devs:
                print(f"\n!!! 在总线 {b} 上找到了设备！请修改代码中的 bus_id = {b}")

if __name__ == "__main__":
    main()
