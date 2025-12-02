#!/usr/bin/python3
# coding=utf8
import smbus
import time

# 配置
I2C_ADDR = 0x34  # WonderEcho I2C地址（已通过 i2cdetect 确认）
BUS_ID = 4  # MaixCam 使用 Bus 4（树莓派默认是 Bus 1）

# 模块寄存器
ASR_RESULT_ADDR = 0x64  # 语音识别结果寄存器地址
ASR_SPEAK_ADDR = 0x6E   # 播报设置寄存器地址

ASR_CMDMAND = 0x00     # 播报语类型：命令词条播报语
ASR_ANNOUNCER = 0xFF   # 播报语类型：普通播报语

class ASRModule:
    def __init__(self, address, bus=4):
        # 初始化 I2C 总线和设备地址
        self.bus = smbus.SMBus(bus)
        self.address = address
        self.send = [0, 0]

    def wire_write_data_array(self, reg, val, length):
        """
        向指定寄存器写入字节数组
        """
        try:            
            self.bus.write_i2c_block_data(self.address, reg, val[:length])
            return True
        except IOError as e:
            print(f"写入失败: {e}")
            return False

    def speak(self, cmd, id):
        """
        向设备发送播报命令
        :param cmd: 0x00=命令词, 0xFF=播报语
        :param id: 播报 ID
        """
        if cmd == ASR_ANNOUNCER or cmd == ASR_CMDMAND:
            self.send[0] = cmd
            self.send[1] = id
            print(f"  -> 发送: cmd={hex(cmd)}, id={hex(id)}, 数据={[hex(b) for b in self.send]}")
            result = self.wire_write_data_array(ASR_SPEAK_ADDR, self.send, 2)
            if result:
                print("  -> 发送成功")
            else:
                print("  -> 发送失败")


if __name__ == "__main__":
    print("MaixCam 语音播报测试 (官方协议)")
    print("=" * 50)
    
    asr_module = ASRModule(I2C_ADDR, bus=BUS_ID)
    
    # 定义播报内容及其对应的ID
    announcements = [
        ("命令词: 我在", ASR_CMDMAND, 3),
        ("播报语: 可回收物", ASR_ANNOUNCER, 1),
        ("播报语: 厨余垃圾", ASR_ANNOUNCER, 2),
        ("播报语: 有害垃圾", ASR_ANNOUNCER, 3),
        ("播报语: 其他垃圾", ASR_ANNOUNCER, 4),
    ]
    
    print("\n开始播报测试...")
    print("(每次间隔 5 秒)\n")
    
    for name, cmd, id in announcements:
        print(f"[测试] {name}")
        asr_module.speak(cmd, id)
        print("  -> 等待 5 秒...")
        time.sleep(5)
    
    print("\n" + "=" * 50)
    print("测试结束。")
    print("\n如果仍然没有声音，请检查:")
    print("1. 模块是否单独 Type-C 供电（5V）")
    print("2. I2C 线路是否正确连接（SDA, SCL）")
    print("3. 模块地址是否确实是 0x34（用 i2cdetect 确认）")
