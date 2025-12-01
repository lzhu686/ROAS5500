#!/usr/bin/env python3
"""使用 MaixCam 扬声器播放垃圾分类结果

由于 WonderEcho 固件没有预置垃圾分类语音，
改用 MaixCam 自带扬声器播放 WAV 文件
"""

import os
import time

# 垃圾分类语音文件目录
AUDIO_DIR = "/root/garbage_audio"

# 分类对应的 WAV 文件名
CATEGORY_FILES = {
    "可回收物": "recyclable.wav",
    "厨余垃圾": "kitchen.wav",
    "有害垃圾": "hazardous.wav",
    "其他垃圾": "other.wav",
}

def create_audio_files():
    """创建语音文件目录"""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    print(f"语音文件目录: {AUDIO_DIR}")
    print("\n请将以下 WAV 文件放入该目录:")
    for category, filename in CATEGORY_FILES.items():
        filepath = os.path.join(AUDIO_DIR, filename)
        print(f"  {filename} -> {category}")
        if os.path.exists(filepath):
            print(f"    ✓ 已存在")
        else:
            print(f"    ✗ 缺失")

def test_playback():
    """测试 MaixCam 扬声器播放"""
    from maix import audio
    
    print("\n测试 MaixCam 扬声器...")
    
    # 检查是否有可用的 WAV 文件
    for category, filename in CATEGORY_FILES.items():
        filepath = os.path.join(AUDIO_DIR, filename)
        if os.path.exists(filepath):
            print(f"\n播放: {category} ({filename})")
            try:
                player = audio.Player()
                player.volume(85)
                player.play(filepath)
                time.sleep(2)
                print("  ✓ 播放完成")
            except Exception as e:
                print(f"  ✗ 播放失败: {e}")
        else:
            print(f"\n跳过: {category} (文件不存在)")

def generate_simple_beep():
    """生成简单的提示音作为临时替代"""
    import struct
    import wave
    
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # 生成不同频率的提示音代表不同类别
    categories = [
        ("可回收物", "recyclable.wav", 800),   # 高音
        ("厨余垃圾", "kitchen.wav", 600),      # 中高音
        ("有害垃圾", "hazardous.wav", 400),    # 中低音
        ("其他垃圾", "other.wav", 300),        # 低音
    ]
    
    sample_rate = 16000
    duration = 0.5  # 秒
    
    for category, filename, freq in categories:
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # 生成正弦波
        import math
        samples = []
        for i in range(int(sample_rate * duration)):
            t = i / sample_rate
            # 简单的正弦波
            value = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
            samples.append(value)
        
        # 写入 WAV 文件
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for sample in samples:
                wav_file.writeframes(struct.pack('<h', sample))
        
        print(f"  ✓ 生成: {filename} ({category}, {freq}Hz)")

def main():
    print("=" * 60)
    print("MaixCam 语音播放测试")
    print("=" * 60)
    
    print("\n[1] 检查语音文件...")
    create_audio_files()
    
    print("\n[2] 生成临时提示音...")
    try:
        generate_simple_beep()
    except Exception as e:
        print(f"  生成失败: {e}")
    
    print("\n[3] 测试播放...")
    try:
        test_playback()
    except Exception as e:
        print(f"  测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
