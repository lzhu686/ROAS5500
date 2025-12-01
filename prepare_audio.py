#!/usr/bin/env python3
"""准备垃圾分类语音文件

此脚本用于：
1. 创建语音文件目录
2. 检查语音文件是否存在
3. 可选：使用 TTS 生成语音文件（如果有 pyttsx3 或其他 TTS 库）
"""

import os

# 语音文件配置（与主程序保持一致）
AUDIO_DIR = "/root/garbage_audio"
CATEGORY_FILES = {
    "可回收物": "recyclable.wav",
    "厨余垃圾": "kitchen.wav",
    "有害垃圾": "hazardous.wav",
    "其他垃圾": "other.wav",
}

def create_directory():
    """创建语音文件目录"""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    print(f"✓ 创建目录: {AUDIO_DIR}")

def check_files():
    """检查语音文件状态"""
    print("\n语音文件状态:")
    print("=" * 60)
    
    all_exist = True
    for category, filename in CATEGORY_FILES.items():
        filepath = os.path.join(AUDIO_DIR, filename)
        exists = os.path.exists(filepath)
        status = "✓ 存在" if exists else "✗ 缺失"
        print(f"  {category:8} -> {filename:20} {status}")
        if not exists:
            all_exist = False
    
    print("=" * 60)
    return all_exist

def generate_simple_wav():
    """生成简单的正弦波提示音作为临时替代"""
    import math
    import struct
    import wave
    
    print("\n生成临时提示音...")
    
    # 不同类别用不同频率
    categories = [
        ("可回收物", "recyclable.wav", 800, 2),   # 高音，2次
        ("厨余垃圾", "kitchen.wav", 600, 2),      # 中高音，2次
        ("有害垃圾", "hazardous.wav", 400, 1),    # 中低音，1次
        ("其他垃圾", "other.wav", 300, 3),        # 低音，3次
    ]
    
    sample_rate = 16000
    tone_duration = 0.3  # 每个音持续 300ms
    
    for category, filename, freq, count in categories:
        filepath = os.path.join(AUDIO_DIR, filename)
        
        samples = []
        for _ in range(count):
            # 生成正弦波
            for i in range(int(sample_rate * tone_duration)):
                t = i / sample_rate
                value = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
                samples.append(value)
            # 添加间隔
            if count > 1:
                for _ in range(int(sample_rate * 0.15)):
                    samples.append(0)
        
        # 写入 WAV 文件
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            for sample in samples:
                wav_file.writeframes(struct.pack('<h', sample))
        
        print(f"  ✓ {category}: {filename} ({freq}Hz, {count}次)")

def show_instructions():
    """显示如何准备真实语音文件的说明"""
    print("\n" + "=" * 60)
    print("如何准备真实语音文件:")
    print("=" * 60)
    print("\n方法 1: 录制真人语音")
    print("  1. 使用手机或电脑录音软件")
    print("  2. 清晰朗读: '可回收物'、'厨余垃圾'、'有害垃圾'、'其他垃圾'")
    print("  3. 转换为 WAV 格式 (16kHz, 单声道, 16-bit)")
    print("  4. 重命名并上传到 MaixCam:")
    for category, filename in CATEGORY_FILES.items():
        print(f"     {category} -> {filename}")
    
    print("\n方法 2: 使用在线 TTS (文字转语音)")
    print("  1. 访问在线 TTS 网站 (如: tts.baidu.com)")
    print("  2. 输入文字并生成语音")
    print("  3. 下载 WAV 文件")
    print("  4. 上传到 MaixCam 的 /root/garbage_audio/ 目录")
    
    print("\n方法 3: 使用当前的提示音")
    print("  运行本脚本生成的临时提示音已经可以区分不同类别")
    print("  虽然不是真人语音，但音调和次数不同，可以识别")
    
    print("\n上传文件到 MaixCam:")
    print("  使用 scp 命令:")
    print("  scp *.wav root@<MaixCam_IP>:/root/garbage_audio/")
    print("  或使用 SFTP 工具（如 FileZilla）")
    print("=" * 60)

def main():
    print("垃圾分类语音文件准备工具")
    print("=" * 60)
    
    # 1. 创建目录
    create_directory()
    
    # 2. 检查文件
    all_exist = check_files()
    
    if not all_exist:
        print("\n缺少语音文件！")
        
        # 3. 生成临时提示音
        try:
            generate_simple_wav()
            print("\n✓ 临时提示音已生成")
        except Exception as e:
            print(f"\n✗ 生成提示音失败: {e}")
        
        # 4. 显示说明
        show_instructions()
    else:
        print("\n✓ 所有语音文件已准备就绪！")
    
    print("\n程序配置:")
    print(f"  语音目录: {AUDIO_DIR}")
    print(f"  音量: 85%")
    print("\n可以运行主程序: python wondecho_voice_assistant.py")

if __name__ == "__main__":
    main()
