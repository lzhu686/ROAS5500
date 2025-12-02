import serial
import time

# 配置串口
# MaixCam 串口设备通常是 /dev/ttyS0 或 /dev/ttyS1
# 请根据实际硬件连接修改
SERIAL_PORT = "/dev/ttyS1"  # 修改为你的串口设备
BAUD_RATE = 9600  # 根据官方文档，通常是 9600

def send_command(ser, cmd_bytes):
    """发送命令到语音模块"""
    ser.write(cmd_bytes)
    print(f"  -> 已发送: {' '.join([hex(b) for b in cmd_bytes])}")

def main():
    print("MaixCam 串口语音播报测试工具")
    print("=" * 40)
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✓ 串口 {SERIAL_PORT} 已打开 (波特率: {BAUD_RATE})")
    except Exception as e:
        print(f"✗ 无法打开串口: {e}")
        print("提示: 请确认串口设备路径和权限")
        return
    
    # 测试播报语（被动播报）
    # 根据协议表: AA 55 FF [ID] FB
    
    播报测试 = [
        (0x01, "可回收物"),
        (0x02, "厨余垃圾"),
        (0x03, "有害垃圾"),
        (0x04, "其他垃圾"),
    ]
    
    print("\n开始测试被动播报...")
    
    for sound_id, name in 播报测试:
        print(f"\n[测试] {name} (ID: {hex(sound_id)})")
        
        # 构造协议: AA 55 FF [ID] FB
        cmd = bytes([0xAA, 0x55, 0xFF, sound_id, 0xFB])
        
        send_command(ser, cmd)
        print("  -> 等待 3 秒...")
        time.sleep(3)
    
    # 测试控制性命令（主动播报）
    print("\n\n开始测试控制命令...")
    
    控制测试 = [
        (0x01, "欢迎语"),
        (0x03, "我在（模拟唤醒响应）"),
    ]
    
    for sound_id, name in 控制测试:
        print(f"\n[测试] {name} (ID: {hex(sound_id)})")
        
        # 构造协议: AA 55 [ID] 00 FB
        cmd = bytes([0xAA, 0x55, sound_id, 0x00, 0xFB])
        
        send_command(ser, cmd)
        print("  -> 等待 3 秒...")
        time.sleep(3)
    
    ser.close()
    print("\n测试结束。")

if __name__ == "__main__":
    main()
