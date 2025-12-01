#!/usr/bin/env python3
"""
垃圾分类系统 (纯 I2C 版)
- 遵循 WonderEcho 官方技术支持提供的 Pure I2C 协议
- 解决 write_i2c_block_data 产生的额外长度字节问题
- 解决 write_word_data 字节序导致的指令错误
"""
import smbus
import time

# ================= 配置 =================
I2C_ADDR = 0x34        # 设备地址
BUS_ID = 4             # MaixCam I2C 总线
RESULT_REG = 0x64      # 识别结果寄存器
SPEAK_REG = 0x6E       # 播报控制寄存器

# 播报类型
CMD_BROADCAST = 0xFF   # 播报语 (如 "可回收物")
CMD_COMMAND = 0x00     # 命令词

# 垃圾分类 ID 映射 (根据您的固件实际情况)
# 假设: 1=可回收物, 2=厨余垃圾, 3=有害垃圾, 4=其他垃圾
GARBAGE_MAP = {
    1: "可回收物",
    2: "厨余垃圾",
    3: "有害垃圾",
    4: "其他垃圾"
}

def init_i2c():
    try:
        bus = smbus.SMBus(BUS_ID)
        return bus
    except Exception as e:
        print(f"I2C 初始化失败: {e}")
        return None

def speak_pure_i2c(bus, cmd_type, phrase_id):
    """
    使用 write_word_data 模拟 Pure I2C 写入 2 个字节
    
    目标时序: [Addr] [Reg] [Byte1] [Byte2]
    目标数据: [0x34] [0x6E] [0xFF] [ID]
    
    write_word_data 发送顺序为: LowByte, HighByte
    因此:
      LowByte  必须是 0xFF (cmd_type)
      HighByte 必须是 ID   (phrase_id)
      
    构造 16位值: (HighByte << 8) | LowByte
    """
    try:
        # 构造 16 位整数
        # 例如: cmd=0xFF, id=0x01 -> value = 0x01FF
        # 发送时: 先发 0xFF, 再发 0x01 -> 符合协议
        value = (phrase_id << 8) | cmd_type
        
        print(f"  -> 发送指令: Reg={hex(SPEAK_REG)}, Val={hex(value)} (Low={hex(cmd_type)}, High={hex(phrase_id)})")
        
        bus.write_word_data(I2C_ADDR, SPEAK_REG, value)
        return True
    except Exception as e:
        print(f"  -> 发送失败: {e}")
        return False

def main():
    print("========================================")
    print("垃圾分类系统 (纯 I2C 协议修正版)")
    print("========================================")
    
    bus = init_i2c()
    if not bus:
        return

    print("系统就绪。")
    print("请对模块说: '小幻小幻' -> '这是什么垃圾'")
    print("-" * 40)

    last_id = 0
    
    while True:
        try:
            # 1. 读取识别结果
            # read_byte_data 读取一个字节，通常比 block read 更稳定
            try:
                current_id = bus.read_byte_data(I2C_ADDR, RESULT_REG)
            except:
                # 如果读取失败，尝试忽略本次
                time.sleep(0.05)
                continue

            # 2. 处理识别结果
            if current_id != 0:
                # 只有当 ID 发生变化，或者距离上次识别已经过了一段时间（防止重复触发）
                if current_id != last_id:
                    print(f"\n[识别成功] ID: {current_id}")
                    
                    if current_id in GARBAGE_MAP:
                        text = GARBAGE_MAP[current_id]
                        print(f"  类别: {text}")
                        
                        # 发送播报指令
                        # 注意：这里发送的是 0xFF (播报语) + ID
                        speak_pure_i2c(bus, CMD_BROADCAST, current_id)
                        
                        # 重要：给予模块播放时间，防止指令重叠导致沙哑
                        # 假设播放一条语音需要 1.5 - 2 秒
                        print("  (播放中...)")
                        time.sleep(2.0) 
                        
                        # 播放完成后，清除 last_id 状态，允许再次识别同一种垃圾
                        # 或者保持 last_id 以防止一直重复播放，取决于需求
                        # 这里我们选择清空，这样用户再次询问可以再次回答
                        last_id = 0 
                        
                        # 尝试手动清空结果寄存器 (可选，视固件而定)
                        # bus.write_byte_data(I2C_ADDR, RESULT_REG, 0)
                        
                    else:
                        print(f"  未知 ID: {current_id}")
                        last_id = current_id

            else:
                # ID 为 0，表示没有识别到
                last_id = 0
            
            # 循环延时，避免占用过多 I2C 总线资源
            time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n程序停止")
            break
        except Exception as e:
            print(f"运行错误: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
