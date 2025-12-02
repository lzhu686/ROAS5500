#!/usr/bin/env python3
import smbus
import time

# 配置
I2C_ADDR = 0x34
BUS_ID = 4

print(f"========================================")
print(f"WonderEcho 全局寄存器监控器")
print(f"Bus: {BUS_ID}, Addr: {hex(I2C_ADDR)}")
print(f"========================================")

try:
    bus = smbus.SMBus(BUS_ID)
except Exception as e:
    print(f"无法打开 I2C 总线: {e}")
    exit(1)

# 初始化缓存
cache = {}
valid_registers = []

print("1. 正在扫描有效寄存器 (0x00 - 0x7F)...")
for reg in range(0x80):
    try:
        # 尝试读取
        val = bus.read_byte_data(I2C_ADDR, reg)
        cache[reg] = val
        valid_registers.append(reg)
    except:
        cache[reg] = None

print(f"   -> 发现 {len(valid_registers)} 个可读寄存器")
print(f"   -> 初始值已记录")

print("\n2. 开始实时监控...")
print("   请对模块说话 (小幻小幻 / 开启垃圾分类)")
print("   任何寄存器数值变化都会被打印出来")
print("   (按 Ctrl+C 退出)")
print("-" * 40)

try:
    while True:
        changes_found = False
        
        for reg in valid_registers:
            try:
                # 读取当前值
                val = bus.read_byte_data(I2C_ADDR, reg)
                
                # 比较变化
                if cache[reg] is not None and val != cache[reg]:
                    print(f"[变化] Reg {hex(reg)}: {hex(cache[reg])} -> {hex(val)} ({val})")
                    cache[reg] = val
                    changes_found = True
                    
            except:
                pass
        
        # 如果有变化，打印分隔符以便区分
        if changes_found:
            print("-" * 20)
            
        # 适当延时，避免占用过高 CPU，但要足够快以捕捉变化
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n监控停止")
