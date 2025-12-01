#!/usr/bin/env python3
"""
WonderEcho 语音交互垃圾分类系统 - 串口版本
使用串口发送播报命令，I2C 仅用于读取识别结果
"""

import serial
import smbus
import time

# I2C 配置（仅用于读取识别结果）
I2C_BUS = 4
I2C_ADDR = 0x34
ASR_RESULT_ADDR = 0x64

# 串口配置（用于发送播报命令）
SERIAL_PORT = "/dev/ttyS1"  # 根据实际硬件修改
BAUD_RATE = 9600

# 垃圾分类映射
GARBAGE_MAP = {
    # 假设你的固件中命令词 ID 映射如下（请根据实际调整）
    11: "可回收物",
    12: "厨余垃圾", 
    13: "有害垃圾",
    14: "其他垃圾",
}

# 播报语 ID（被动播报）
ANNOUNCE_MAP = {
    "可回收物": 0x01,
    "厨余垃圾": 0x02,
    "有害垃圾": 0x03,
    "其他垃圾": 0x04,
}

def send_uart_announce(ser, announce_id):
    """通过串口发送播报命令"""
    # 协议: AA 55 FF [ID] FB
    cmd = bytes([0xAA, 0x55, 0xFF, announce_id, 0xFB])
    ser.write(cmd)
    print(f"  -> 串口发送: {' '.join([hex(b) for b in cmd])}")

def read_i2c_result(bus):
    """通过 I2C 读取识别结果"""
    try:
        result = bus.read_i2c_block_data(I2C_ADDR, ASR_RESULT_ADDR, 1)
        return result[0]
    except:
        return 0

def main():
    print("=" * 60)
    print("WonderEcho 语音垃圾分类系统 (混合模式)")
    print("I2C: 读取识别结果 | 串口: 播报")
    print("=" * 60)
    
    # 初始化 I2C
    try:
        i2c_bus = smbus.SMBus(I2C_BUS)
        print(f"✓ I2C Bus {I2C_BUS} 已打开")
    except Exception as e:
        print(f"✗ 无法打开 I2C: {e}")
        return
    
    # 初始化串口
    try:
        uart = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✓ 串口 {SERIAL_PORT} 已打开 (波特率: {BAUD_RATE})")
    except Exception as e:
        print(f"✗ 无法打开串口: {e}")
        print(f"  提示: 请确认串口设备路径")
        i2c_bus.close()
        return
    
    print("\n系统就绪！请说出垃圾分类命令...")
    print("例如: '小幻小幻' -> '可回收物'")
    print("按 Ctrl+C 退出\n")
    
    last_result = 0
    
    try:
        while True:
            # 读取 I2C 识别结果
            result = read_i2c_result(i2c_bus)
            
            # 检测到新命令
            if result != 0 and result != last_result:
                print(f"[检测] 命令 ID: {result}")
                
                # 查找对应的垃圾分类
                if result in GARBAGE_MAP:
                    garbage_type = GARBAGE_MAP[result]
                    announce_id = ANNOUNCE_MAP[garbage_type]
                    
                    print(f"[识别] {garbage_type}")
                    print(f"[播报] 通过串口发送...")
                    
                    send_uart_announce(uart, announce_id)
                    
                    print(f"✓ 播报完成\n")
                else:
                    print(f"[未知] 命令 ID {result} 未映射\n")
                
                last_result = result
            
            # 清零检测
            elif result == 0 and last_result != 0:
                last_result = 0
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n正在退出...")
    finally:
        i2c_bus.close()
        uart.close()
        print("系统已关闭")

if __name__ == "__main__":
    main()
