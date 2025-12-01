import smbus
import time
import os

# 配置
BUS_ID = 4
TARGET_ADDR = 0x34
REG_RESULT = 0x64  # 100

def main():
    print("MaixCam I2C 诊断工具 v3 - 深度测试")
    print("=" * 40)
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开总线 {BUS_ID}: {e}")
        return

    # 1. 连接测试
    try:
        bus.read_byte(TARGET_ADDR)
        print(f"✓ 设备 {hex(TARGET_ADDR)} 在线")
    except:
        print(f"✗ 无法连接设备 {hex(TARGET_ADDR)}")
        return

    # 2. 读写测试 (尝试写入一个值看是否能读回)
    print("\n[寄存器读写测试]")
    try:
        # 读取当前值
        val_before = bus.read_byte_data(TARGET_ADDR, REG_RESULT)
        print(f"  当前寄存器值: {val_before}")
        
        # 尝试写入 0x55 (85)
        print("  尝试写入 0x55 ...")
        bus.write_byte_data(TARGET_ADDR, REG_RESULT, 0x55)
        
        # 立即读取
        val_after = bus.read_byte_data(TARGET_ADDR, REG_RESULT)
        print(f"  写入后读取值: {val_after}")
        
        if val_after == 0x55:
            print("  ✓ 寄存器可读写 (RAM)")
            # 恢复 0
            bus.write_byte_data(TARGET_ADDR, REG_RESULT, 0x00)
        else:
            print("  ! 寄存器值未改变 (可能是只读，或被固件立即覆盖)")
            
    except Exception as e:
        print(f"  读写测试失败: {e}")

    # 3. 高速监听模式
    print("\n[高速监听模式]")
    print("请依次说出以下词语：")
    print("1. '小幻小幻' (唤醒词)")
    print("2. '开启垃圾分类' (命令词)")
    print("3. '可回收物' (命令词)")
    print("按 Ctrl+C 退出...")
    
    last_val = -1
    start_time = time.time()
    
    try:
        while True:
            # 读取寄存器 100 (0x64)
            # 使用 read_byte_data (读取单个字节)
            try:
                val = bus.read_byte_data(TARGET_ADDR, REG_RESULT)
                
                if val != 0:
                    print(f"!!! 检测到信号 !!! 值: {val} (Hex: {hex(val)})")
                    
                    # 尝试清除?
                    # bus.write_byte_data(TARGET_ADDR, REG_RESULT, 0)
                    # print("   (已尝试清除)")
                
                if val != last_val:
                    if last_val != -1: # 忽略第一次
                         print(f"   状态变化: {last_val} -> {val}")
                    last_val = val
                    
            except OSError:
                # 忽略偶尔的 I2C 错误
                pass
                
            # 极短延时，避免占用 100% CPU 但保持高速
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n停止监听")

if __name__ == "__main__":
    main()
