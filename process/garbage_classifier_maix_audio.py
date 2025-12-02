#!/usr/bin/env python3
"""
垃圾分类系统 (MaixCam 音频版)
- 输入: WonderEcho 语音识别 (I2C)
- 输出: MaixCam 本地扬声器播放 (WAV)

此方案无需 WonderEcho 播报，直接利用 MaixCam 的音频能力。
"""
import smbus
import time
import os
import struct
import wave
import math

# 尝试导入 maix.audio，如果失败则提示
try:
    from maix import audio
    MAIX_AUDIO_AVAILABLE = True
except ImportError:
    print("警告: 未找到 maix 模块，将无法播放音频")
    MAIX_AUDIO_AVAILABLE = False

# 配置
I2C_ADDR = 0x34
BUS_ID = 4
RESULT_REG = 0x64

# 垃圾分类映射 (ID -> 类别名称)
# 请根据实际固件修改 ID
GARBAGE_MAP = {
    1: "可回收物",
    2: "厨余垃圾",
    3: "有害垃圾",
    4: "其他垃圾"
}

# 音频文件目录
AUDIO_DIR = "/root/garbage_audio"
AUDIO_FILES = {
    1: "recyclable.wav",
    2: "kitchen.wav",
    3: "hazardous.wav",
    4: "other.wav"
}

def generate_beeps():
    """如果没有WAV文件，生成简单的提示音"""
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
        
    sample_rate = 16000
    duration = 0.5
    
    freqs = {1: 800, 2: 600, 3: 400, 4: 300}
    
    for id, filename in AUDIO_FILES.items():
        filepath = os.path.join(AUDIO_DIR, filename)
        if not os.path.exists(filepath):
            print(f"生成临时音频: {filename}")
            freq = freqs.get(id, 500)
            samples = []
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                value = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
                samples.append(value)
            
            with wave.open(filepath, 'w') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(sample_rate)
                for s in samples:
                    f.writeframes(struct.pack('<h', s))

def play_audio(id):
    """播放对应ID的音频"""
    if not MAIX_AUDIO_AVAILABLE:
        print("  [模拟播放] (maix 模块不可用)")
        return

    filename = AUDIO_FILES.get(id)
    if filename:
        filepath = os.path.join(AUDIO_DIR, filename)
        if os.path.exists(filepath):
            try:
                p = audio.Player()
                p.play(filepath)
                print(f"  正在播放: {filepath}")
                # 等待播放完成（简单延时）
                time.sleep(0.5) 
            except Exception as e:
                print(f"  播放失败: {e}")
        else:
            print(f"  文件不存在: {filepath}")

def main():
    print("========================================")
    print("垃圾分类系统 (MaixCam 音频版)")
    print("========================================")
    
    print("1. 初始化 I2C...")
    try:
        bus = smbus.SMBus(BUS_ID)
        print(f"   Bus {BUS_ID} 打开成功")
    except Exception as e:
        print(f"   I2C 初始化失败: {e}")
        return

    print("2. 检查音频文件...")
    generate_beeps()
    
    print("\n系统就绪! 请对 WonderEcho 说:")
    print("  '小幻小幻' -> (唤醒)")
    print("  '这是什么垃圾' -> (触发识别)")
    print("-" * 40)
    
    last_id = 0
    
    while True:
        try:
            # 读取识别结果
            # 注意：有些固件读取一次后会自动清零，有些需要手动清零
            # 这里假设读取到非零值即为识别结果
            result = bus.read_i2c_block_data(I2C_ADDR, RESULT_REG, 1)
            current_id = result[0]
            
            if current_id != 0 and current_id != last_id:
                print(f"\n[识别到 ID: {current_id}]")
                
                if current_id in GARBAGE_MAP:
                    category = GARBAGE_MAP[current_id]
                    print(f"  分类结果: {category}")
                    play_audio(current_id)
                else:
                    print(f"  未知 ID: {current_id}")
                
                last_id = current_id
                
            elif current_id == 0:
                last_id = 0
                
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"读取错误: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
