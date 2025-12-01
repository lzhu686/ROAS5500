#!/usr/bin/env python3
"""检查和修复 WAV 文件格式"""

import os
import struct

AUDIO_DIR = "/root/garbage_audio"

def check_wav_header(filepath):
    """检查 WAV 文件头"""
    print(f"\n检查: {os.path.basename(filepath)}")
    print("-" * 60)
    
    try:
        with open(filepath, 'rb') as f:
            # 读取文件头
            header = f.read(44)
            
            if len(header) < 44:
                print(f"  ✗ 文件太小 ({len(header)} 字节)")
                return False
            
            # 检查 RIFF 标识
            riff = header[0:4]
            print(f"  文件标识: {riff}")
            
            if riff != b'RIFF':
                print(f"  ✗ 不是标准 WAV 文件 (应该是 'RIFF')")
                
                # 显示文件的前 16 字节
                print(f"  前16字节: {header[:16].hex()}")
                return False
            
            # 检查 WAVE 格式
            wave = header[8:12]
            if wave != b'WAVE':
                print(f"  ✗ 不是 WAVE 格式: {wave}")
                return False
            
            # 解析音频参数
            channels = struct.unpack('<H', header[22:24])[0]
            sample_rate = struct.unpack('<I', header[24:28])[0]
            bits_per_sample = struct.unpack('<H', header[34:36])[0]
            
            print(f"  ✓ 标准 WAV 格式")
            print(f"  声道数: {channels}")
            print(f"  采样率: {sample_rate} Hz")
            print(f"  位深度: {bits_per_sample} bit")
            
            # 检查是否符合 MaixCam 要求
            issues = []
            if channels != 1:
                issues.append(f"声道应为1 (当前{channels})")
            if sample_rate != 16000:
                issues.append(f"采样率应为16000 (当前{sample_rate})")
            if bits_per_sample != 16:
                issues.append(f"位深度应为16 (当前{bits_per_sample})")
            
            if issues:
                print(f"  ⚠️  格式问题:")
                for issue in issues:
                    print(f"      - {issue}")
                return False
            else:
                print(f"  ✓ 格式正确")
                return True
                
    except Exception as e:
        print(f"  ✗ 读取错误: {e}")
        return False

def main():
    print("WAV 文件格式检查工具")
    print("=" * 60)
    
    if not os.path.exists(AUDIO_DIR):
        print(f"✗ 目录不存在: {AUDIO_DIR}")
        return
    
    files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]
    
    if not files:
        print(f"✗ 目录中没有 WAV 文件: {AUDIO_DIR}")
        return
    
    print(f"\n找到 {len(files)} 个 WAV 文件")
    
    valid_count = 0
    for filename in files:
        filepath = os.path.join(AUDIO_DIR, filename)
        if check_wav_header(filepath):
            valid_count += 1
    
    print("\n" + "=" * 60)
    print(f"结果: {valid_count}/{len(files)} 个文件格式正确")
    print("=" * 60)
    
    if valid_count < len(files):
        print("\n建议:")
        print("  1. 重新录制或下载正确格式的 WAV 文件")
        print("  2. 使用音频转换工具转换格式:")
        print("     - 格式: WAV (PCM)")
        print("     - 采样率: 16000 Hz")
        print("     - 声道: 单声道 (Mono)")
        print("     - 位深度: 16-bit")
        print("\n  在线转换工具:")
        print("     https://www.aconvert.com/cn/audio/")
        print("     https://convertio.co/zh/")

if __name__ == "__main__":
    main()
