#!/usr/bin/env python3
"""测试 MaixCam 音频播放功能

诊断语音文件播放问题
"""

import os
import time
from maix import audio

# 语音文件配置
AUDIO_DIR = "/root/garbage_audio"
TEST_FILES = {
    "可回收物": "recyclable.wav",
    "厨余垃圾": "kitchen.wav",
    "有害垃圾": "hazardous.wav",
    "其他垃圾": "other.wav",
}

def check_files():
    """检查文件是否存在"""
    print("=" * 60)
    print("检查语音文件")
    print("=" * 60)
    
    all_exist = True
    for category, filename in TEST_FILES.items():
        filepath = os.path.join(AUDIO_DIR, filename)
        exists = os.path.exists(filepath)
        
        if exists:
            size = os.path.getsize(filepath)
            print(f"✓ {category:10} {filename:20} ({size} bytes)")
        else:
            print(f"✗ {category:10} {filename:20} [文件不存在]")
            all_exist = False
    
    print("=" * 60)
    return all_exist

def test_audio_player_simple():
    """测试方法 1: 简单播放"""
    print("\n[测试 1] 简单播放方法")
    print("-" * 60)
    
    for category, filename in TEST_FILES.items():
        filepath = os.path.join(AUDIO_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"跳过 {category} (文件不存在)")
            continue
        
        print(f"\n播放: {category} ({filename})")
        player = None
        try:
            player = audio.Player(filepath)
            player.volume(85)
            player.play()
            
            print("  播放中... (等待 2 秒)")
            time.sleep(2)
            print("  ✓ 完成")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        finally:
            # 释放资源
            if player is not None:
                del player
            time.sleep(0.2)  # 短暂延时确保资源释放

def test_audio_player_loop():
    """测试方法 2: 循环等待播放完成"""
    print("\n[测试 2] 循环等待播放完成")
    print("-" * 60)
    
    for category, filename in TEST_FILES.items():
        filepath = os.path.join(AUDIO_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"跳过 {category} (文件不存在)")
            continue
        
        print(f"\n播放: {category} ({filename})")
        player = None
        try:
            player = audio.Player(filepath)
            player.volume(85)
            
            # 循环调用 play，最多 10 次
            play_count = 0
            max_loops = 10
            while play_count < max_loops:
                result = player.play()
                play_count += 1
                if result != 0:
                    print(f"  play() 返回: {result}")
                    break
                time.sleep(0.01)
            
            time.sleep(0.5)  # 等待播放完成
            print(f"  ✓ 完成 (循环 {play_count} 次)")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        finally:
            # 释放资源
            if player is not None:
                del player
            time.sleep(0.2)  # 短暂延时确保资源释放

def test_audio_recorder():
    """测试麦克风录音功能（确认音频系统正常）"""
    print("\n[测试 3] 麦克风录音测试")
    print("-" * 60)
    
    recorder = None
    player = None
    try:
        recorder = audio.Recorder(sample_rate=16000)
        print("录音 3 秒（请说话）...")
        
        data = recorder.record(16000 * 3)  # 3 秒
        
        if data and len(data) > 0:
            print(f"✓ 录音成功 ({len(data)} 字节)")
            
            # 计算音频能量
            import struct
            if isinstance(data, bytes):
                samples = struct.unpack(f'{len(data)//2}h', data)
            else:
                samples = data
            
            energy = sum(abs(s) for s in samples) / len(samples)
            print(f"  平均能量: {energy:.2f}")
            
            # 保存为 WAV 文件
            import wave
            record_path = "/tmp/test_recording.wav"
            print(f"\n保存录音到: {record_path}")
            
            with wave.open(record_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 采样率
                
                # 写入音频数据
                if isinstance(data, bytes):
                    wav_file.writeframes(data)
                else:
                    for sample in data:
                        wav_file.writeframes(struct.pack('<h', sample))
            
            print("  ✓ 录音已保存")
            
            # 等待1秒后播放录音
            print("\n等待 1 秒后播放录音...")
            time.sleep(1)
            
            print("播放录音...")
            player = audio.Player(record_path)
            player.volume(85)
            player.play()
            
            time.sleep(3.5)  # 等待播放完成（录音3秒+缓冲）
            print("  ✓ 录音播放完成")
            
        else:
            print("✗ 录音失败")
    except Exception as e:
        print(f"✗ 错误: {e}")
    finally:
        # 清理资源
        if recorder is not None:
            del recorder
        if player is not None:
            del player

def show_system_info():
    """显示系统信息"""
    print("\n[系统信息]")
    print("-" * 60)
    
    # 检查音频目录
    if os.path.exists(AUDIO_DIR):
        files = os.listdir(AUDIO_DIR)
        print(f"音频目录: {AUDIO_DIR}")
        print(f"文件列表: {files}")
    else:
        print(f"⚠️  音频目录不存在: {AUDIO_DIR}")
    
    # 检查临时目录
    print(f"临时目录: /tmp")
    if os.path.exists("/tmp"):
        tmp_wavs = [f for f in os.listdir("/tmp") if f.endswith('.wav')]
        if tmp_wavs:
            print(f"临时 WAV 文件: {tmp_wavs}")

def main():
    print("MaixCam 音频播放诊断工具")
    print("=" * 60)
    
    # 1. 检查文件
    files_ok = check_files()
    
    if not files_ok:
        print("\n⚠️  缺少语音文件！")
        print("请先运行: python prepare_audio.py")
        print("或上传真实语音文件到 /root/garbage_audio/")
        return
    
    # 2. 显示系统信息
    show_system_info()
    
    # 3. 测试播放
    test_audio_player_simple()
    
    print("\n等待 3 秒...")
    time.sleep(3)
    
    test_audio_player_loop()
    
    print("\n" + "=" * 60)
    print("诊断完成！")
    print("=" * 60)
    print("\n如果所有测试都失败:")
    print("  1. 检查 MaixCam 扬声器是否正常（硬件问题）")
    print("  2. 检查音量设置（可能被静音）")
    print("  3. 检查 WAV 文件格式（推荐: 16kHz, 单声道, 16-bit PCM）")
    print("\n如果某些方法成功:")
    print("  主程序会使用成功的方法（已自动适配）")

if __name__ == "__main__":
    main()
