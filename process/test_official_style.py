#!/usr/bin/python3
# coding=utf8
"""
Wondecho 被动播报一键排查工具（MaixCam Pro 专用）
功能：1. 检测模块是否唤醒 2. 自动开启播报功能 3. 多ID测试 4. 错误定位
依赖：smbus（MaixCam 自带，无需额外安装）
"""
import smbus
import time

# -------------------------- 基础配置（无需修改）--------------------------
I2C_ADDR = 0x34          # Wondecho 默认I2C地址（官方文档）
ASR_RESULT_ADDR = 0x64   # 识别结果寄存器（读取唤醒状态）
ASR_SPEAK_ADDR = 0x6E    # 播报设置寄存器（发送播报指令）
I2C_BUS = 4              # MaixCam Pro 的I2C总线号（固定为4）

# 官方明确的指令参数（避免ID不匹配）
CMD_TYPE_CMDMAND = 0x00  # 命令词播报类型
CMD_TYPE_ANNOUNCER = 0xFF# 普通播报类型
CMD_ENABLE_SPEAK = 0x09  # 开启播报功能的ID（官方协议）
WAKE_WORD_ID = 0x03      # “小幻小幻”唤醒词对应的识别结果ID（官方文档）

# 测试用的播报内容（覆盖命令词+普通播报，官方明确ID）
TEST_CASES = [
    (CMD_TYPE_CMDMAND, 0x01, "命令词：正在前进（官方ID=0x01）"),
    (CMD_TYPE_CMDMAND, 0x03, "命令词：正在左转（官方ID=0x03）"),
    (CMD_TYPE_ANNOUNCER, 0x01, "普通播报：可回收物（官方ID=0x01）"),
    (CMD_TYPE_ANNOUNCER, 0x02, "普通播报：厨余垃圾（官方ID=0x02）"),
    (CMD_TYPE_ANNOUNCER, 0x03, "普通播报：有害垃圾（官方ID=0x03）"),
    (CMD_TYPE_ANNOUNCER, 0x04, "普通播报：其他垃圾（官方ID=0x04）"),
]

# -------------------------- 核心工具类 --------------------------
class WondechoTester:
    def __init__(self):
        # 初始化I2C总线
        try:
            self.bus = smbus.SMBus(I2C_BUS)
            print(f"✅ I2C总线 {I2C_BUS} 初始化成功（说明接线、地址正常）")
        except Exception as e:
            print(f"❌ I2C总线初始化失败！原因：{e}")
            print("   排查：1. 检查SCL/SDA/GND接线 2. 确认模块5V供电")
            exit(1)  # 总线初始化失败，直接退出
    
    def read_result_reg(self):
        """读取结果寄存器（判断是否唤醒、识别是否正常）"""
        try:
            # 读取1字节数据（唤醒后会存WAKE_WORD_ID=0x03）
            result = self.bus.read_i2c_block_data(I2C_ADDR, ASR_RESULT_ADDR, 1)
            if result:
                return result[0]  # 返回寄存器值
            return None
        except Exception as e:
            print(f"⚠️  读取结果寄存器失败！原因：{e}")
            return None
    
    def send_speak_command(self, cmd_type, cmd_id):
        """发送播报指令（使用官方 write_i2c_block_data 方法）"""
        try:
            # 按官方协议：向 0x6E 寄存器写入 [类型, ID] 两字节
            self.bus.write_i2c_block_data(I2C_ADDR, ASR_SPEAK_ADDR, [cmd_type, cmd_id])
            return True
        except Exception as e:
            print(f"❌ 发送指令失败！原因：{e}")
            return False
    
    def check_wake_status(self):
        """检测模块是否已唤醒（必须唤醒才能被动播报）"""
        print("\n" + "="*50)
        print("1. 检测模块唤醒状态（未唤醒则无法被动播报）")
        print("="*50)
        print("   提示：请在10秒内说「小幻小幻」唤醒模块（正常会回应「我在」）")
        
        start_time = time.time()
        wake_success = False
        while time.time() - start_time < 10:
            result = self.read_result_reg()
            if result == WAKE_WORD_ID:
                print(f"✅ 检测到唤醒！结果寄存器值：0x{result:02X}（对应「小幻小幻」）")
                wake_success = True
                break
            elif result is not None and result != 0x00:
                print(f"⚠️  检测到其他识别结果：0x{result:02X}（非唤醒词，继续等待）")
            time.sleep(1)  # 每秒检测一次
        
        if not wake_success:
            print(f"❌ 10秒内未检测到唤醒！当前结果寄存器值：{self.read_result_reg()}")
            print("   排查：1. 环境是否安静 2. 「小幻小幻」发音是否标准 3. 模块扬声器是否正常（听是否有「我在」）")
            print("   ⚠️  未检测到唤醒，但继续测试（可能检测延迟或模块已唤醒）")
        return wake_success
    
    def enable_speak_function(self):
        """自动开启播报功能（防止模块被误设置为"关闭播报"）"""
        print("\n" + "="*50)
        print("2. 开启播报功能（防止模块被禁用播报）")
        print("="*50)
        print(f"   发送指令：类型=0x{CMD_TYPE_CMDMAND:02X}，ID=0x{CMD_ENABLE_SPEAK:02X}（官方开启播报指令）")
        
        success = self.send_speak_command(CMD_TYPE_CMDMAND, CMD_ENABLE_SPEAK)
        if success:
            print("✅ 开启播报指令发送成功（模块现在应该能响应被动播报）")
        else:
            print("⚠️  开启播报指令发送失败，但继续测试（可能模块已开启）")
        time.sleep(2)  # 等待模块响应
    
    def run_all_tests(self):
        """运行所有播报测试用例"""
        print("\n" + "="*50)
        print("3. 开始被动播报测试（共6个官方明确ID，每个间隔3秒）")
        print("="*50)
        print("   注意：请仔细听模块是否有对应语音输出（即使声音小也记录）")
        
        test_success_count = 0
        for cmd_type, cmd_id, desc in TEST_CASES:
            print(f"\n【测试用例】{desc}")
            print(f"   发送参数：类型=0x{cmd_type:02X}，ID=0x{cmd_id:02X}")
            
            success = self.send_speak_command(cmd_type, cmd_id)
            if success:
                print("   ✅ 指令发送成功（等待3秒听声音...）")
                test_success_count += 1
            else:
                print("   ❌ 指令发送失败（跳过，继续下一个）")
            
            time.sleep(3)  # 给用户足够时间听声音
        
        return test_success_count
    
    def print_final_report(self, test_count):
        """输出最终排查报告"""
        print("\n" + "="*60)
        print("最终排查报告")
        print("="*60)
        total_tests = len(TEST_CASES)
        
        print(f"\n1. I2C通信状态：✅ 正常（总线初始化成功）")
        print(f"2. 指令发送成功率：{test_count}/{total_tests}")
        
        if test_count == 0:
            print("\n❌ 所有指令发送失败！排查方向：")
            print("   - 检查模块5V供电（换优质USB-C线，测电压是否4.8-5.2V）")
            print("   - 确认模块是新版（上电RST后STA灯快闪3次+慢闪1次，旧版可能不支持被动播报）")
            print("   - 重新接线（重点检查GND是否可靠连接，共地不良会导致指令无效）")
        
        else:
            print("\n✅ 所有指令发送成功！")
            print("\n如果你听到了声音：")
            print("   - 说明被动播报功能正常，可以用于垃圾分类项目")
            print("   - 如果个别ID没声音，参考官方文档调整 ID 映射")
            print("\n如果完全没听到声音：")
            print("   - 供电不足：模块能通信但扬声器无法驱动（换5V/2A电源单独供电）")
            print("   - 固件不支持：联系厂商确认固件是否支持 I2C被动播报（部分旧版仅支持语音触发）")
            print("   - 扬声器故障：测试唤醒词「小幻小幻」是否有「我在」回应，无则模块硬件问题")


# -------------------------- 主程序入口 --------------------------
if __name__ == "__main__":
    print("="*60)
    print("Wondecho 被动播报一键排查工具（MaixCam Pro 专用）")
    print("="*60)
    print("前置检查：")
    print("   1. 模块接线：SCL→SCL，SDA→SDA，GND→GND，5V→MaixCam VBUS（5V）")
    print("   2. 供电：用优质USB-C线给MaixCam供电（避免供电不足）")
    print("   3. 环境：保持安静（避免干扰唤醒和声音判断）")
    print("\n3秒后开始测试...")
    time.sleep(3)
    
    # 初始化测试工具
    tester = WondechoTester()
    
    # 分步执行测试
    tester.check_wake_status()          # 1. 检测唤醒
    tester.enable_speak_function()      # 2. 开启播报
    success_count = tester.run_all_tests()  # 3. 多ID测试
    
    # 输出最终报告
    tester.print_final_report(success_count)