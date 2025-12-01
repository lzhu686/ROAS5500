#!/usr/bin/env python3
import smbus
import time
import os

# 配置
I2C_ADDR = 0x34
BUS_ID = 4

def clear_screen():
    print("\033[H\033[J", end="")

def main():
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"无法打开 I2C 总线: {e}")
        return

    print("========================================")
    print("WonderEcho 隐藏 ID 寻找工具")
    print("========================================")
    print("原理: 对比[静默状态]和[说话状态]的寄存器差异")
    print("目标: 找到那个变成 3 (小幻小幻) 或 100 (开启垃圾分类) 的寄存器")
    print("-" * 40)

    # 1. 采样静默状态
    print("请保持环境安静，3秒后开始采样基准值...")
    time.sleep(3)
    print("正在采样 (3秒)...")
    
    baseline = {}
    # 扫描 0x00 - 0x7F
    for _ in range(10): # 多次采样取平均或最后值
        for reg in range(0x80):
            try:
                val = bus.read_byte_data(I2C_ADDR, reg)
                baseline[reg] = val
            except:
                pass
        time.sleep(0.1)
    
    print("基准值采样完成。")
    print("-" * 40)

    # 2. 实时寻找目标
    print("现在，请不断重复说: '小幻小幻'")
    print("程序将寻找值为 3 (0x03) 的寄存器...")
    print("(按 Ctrl+C 退出)")
    time.sleep(2)

    try:
        while True:
            candidates = []
            
            # 快速扫描所有寄存器
            for reg in range(0x80):
                try:
                    val = bus.read_byte_data(I2C_ADDR, reg)
                    
                    # 过滤条件:
                    # 1. 值必须是 3 (唤醒词 ID)
                    # 2. 或者是 100 (命令词 ID)
                    # 3. 且该寄存器在静默时不是这个值 (排除固定版本号等)
                    
                    if val in [3, 100]:
                        # 检查基准值
                        base_val = baseline.get(reg, -1)
                        if base_val != val:
                            candidates.append((reg, val, base_val))
                            
                except:
                    pass
            
            # 显示结果
            if candidates:
                print(f"\n[发现疑似目标] 时间: {time.time()}")
                for reg, val, base in candidates:
                    print(f"  寄存器 {hex(reg)}: 当前值={val} (基准值={base})")
                    if val == 3:
                        print(f"    -> 可能是唤醒词 ID!")
                    if val == 100:
                        print(f"    -> 可能是命令词 ID!")
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n停止")

if __name__ == "__main__":
    main()
