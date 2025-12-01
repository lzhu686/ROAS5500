#!/usr/bin/env python3
import smbus
import time

# 配置
I2C_ADDR = 0x34
BUS_ID = 4
RESULT_REG = 0x64

print(f"========================================")
print(f"WonderEcho 原始数据监听器")
print(f"Bus: {BUS_ID}, Addr: {hex(I2C_ADDR)}, Reg: {hex(RESULT_REG)}")
print(f"========================================")

try:
    bus = smbus.SMBus(BUS_ID)
    print("I2C 总线打开成功")
except Exception as e:
    print(f"严重错误: 无法打开 I2C 总线 - {e}")
    exit(1)

print("\n正在监听... 请对模块说话 (小幻小幻 / 开启垃圾分类)")
print("如果读到非 0 数据，将立即打印：")

last_val = -1

while True:
    try:
        # 尝试使用 Block Read 读取 1 个字节
        # 这是最常用的方式
        data = bus.read_i2c_block_data(I2C_ADDR, RESULT_REG, 1)
        val = data[0]
        
        # 只要读到非 0 值，就打印
        if val != 0:
            print(f"!!! 读到数据: {val} (Hex: {hex(val)}) !!!")
            
            # 尝试清除寄存器 (防止一直读到同一个值)
            # bus.write_byte_data(I2C_ADDR, RESULT_REG, 0)
            # print("   (已发送清除指令)")
            
            # 简单的防刷屏延时
            time.sleep(0.2)
        
        # 只有状态改变时才打印调试信息 (0 -> 0 不打印)
        if val != last_val and val == 0:
            # print(f"寄存器归零")
            pass
            
        last_val = val
        
        # 极短延时，保证采样率
        time.sleep(0.05)

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"读取错误: {e}")
        time.sleep(1)
