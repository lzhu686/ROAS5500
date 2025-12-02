"""MaixCam IMU 读取示例

功能：
- 读取加速度计 (Accelerometer)
- 读取陀螺仪 (Gyroscope)  
- 读取温度

硬件要求：
- MaixCAM-Pro 带有 QMI8658 IMU 传感器
- 注意：标准版 MaixCAM 没有 IMU

参考：https://wiki.sipeed.com/maixpy/doc/zh/modules/ahrs.html
"""

from maix import app, time, display, image
from maix.ext_dev import imu
import math


def calculate_tilt_angles(acc_x, acc_y, acc_z):
    """从加速度计数据计算倾斜角（简化版姿态估计）"""
    # Roll: 绕 X 轴旋转
    roll = math.atan2(acc_y, acc_z) * 180 / math.pi
    # Pitch: 绕 Y 轴旋转
    pitch = math.atan2(-acc_x, math.sqrt(acc_y**2 + acc_z**2)) * 180 / math.pi
    return pitch, roll


def main():
    """读取 IMU 数据并显示"""
    
    # 初始化显示
    disp = display.Display()
    
    # 初始化 IMU (QMI8658)
    # MaixCAM-Pro: QMI8658 在 I2C4, 地址 0x6B
    try:
        # 使用官方推荐的初始化方式
        sensor = imu.IMU("default", 
                        mode=imu.Mode.DUAL,
                        acc_scale=imu.AccScale.ACC_SCALE_2G,
                        acc_odr=imu.AccOdr.ACC_ODR_1000,
                        gyro_scale=imu.GyroScale.GYRO_SCALE_256DPS,
                        gyro_odr=imu.GyroOdr.GYRO_ODR_8000)
        print("[IMU] QMI8658 initialized successfully")
    except Exception as e:
        print(f"[IMU] Init failed: {e}")
        print("[IMU] Make sure you have MaixCAM-Pro with QMI8658 IMU")
        print("[IMU] Standard MaixCAM does NOT have IMU!")
        return
    
    # 加载陀螺仪校准数据（如果存在）
    try:
        if sensor.calib_gyro_exists():
            sensor.load_calib_gyro()
            print("[IMU] Gyro calibration loaded")
        else:
            print("[IMU] No gyro calibration found")
            print("[IMU] First run calibration is recommended!")
    except:
        print("[IMU] Calibration check skipped")
    
    print("\n[IMU] Starting data reading... Press Ctrl+C to stop\n")
    
    while not app.need_exit():
        # 读取所有 IMU 数据 (带校准)
        try:
            data = sensor.read_all(calib_gryo=True, radian=False)
        except Exception as e:
            print(f"[IMU] Read error: {e}")
            time.sleep_ms(100)
            continue
        
        # 从加速度计计算倾斜角
        pitch, roll = calculate_tilt_angles(data.acc.x, data.acc.y, data.acc.z)
        
        # 打印原始数据 (QMI8658 没有磁力计)
        print(f"--- IMU Data ---")
        print(f"Accelerometer: x={data.acc.x:7.3f}, y={data.acc.y:7.3f}, z={data.acc.z:7.3f}")
        print(f"Gyroscope:     x={data.gyro.x:7.3f}, y={data.gyro.y:7.3f}, z={data.gyro.z:7.3f}")
        print(f"Temperature:   {data.temp:.1f}C")
        print(f"Tilt Angles:   Pitch={pitch:7.2f}, Roll={roll:7.2f}")
        print()
        
        # 在屏幕上显示数据
        img = image.Image(disp.width(), disp.height(), image.Format.FMT_RGB888)
        img.draw_rect(0, 0, img.width(), img.height(), image.COLOR_BLACK, -1)
        
        y = 10
        img.draw_string(10, y, "=== IMU Data ===", image.COLOR_GREEN, 1.5)
        y += 30
        
        img.draw_string(10, y, f"Accel:", image.COLOR_WHITE, 1.2)
        y += 25
        img.draw_string(20, y, f"X:{data.acc.x:7.2f} Y:{data.acc.y:7.2f} Z:{data.acc.z:7.2f}", image.COLOR_YELLOW, 1.2)
        y += 30
        
        img.draw_string(10, y, f"Gyro:", image.COLOR_WHITE, 1.2)
        y += 25
        img.draw_string(20, y, f"X:{data.gyro.x:7.2f} Y:{data.gyro.y:7.2f} Z:{data.gyro.z:7.2f}", image.COLOR_YELLOW, 1.2)
        y += 30
        
        img.draw_string(10, y, f"Temperature: {data.temp:.1f} C", image.COLOR_CYAN, 1.2)
        y += 35
        
        img.draw_string(10, y, "=== Tilt Angles (deg) ===", image.COLOR_GREEN, 1.5)
        y += 30
        img.draw_string(20, y, f"Pitch: {pitch:7.2f}", image.COLOR_RED, 1.3)
        y += 25
        img.draw_string(20, y, f"Roll:  {roll:7.2f}", image.COLOR_RED, 1.3)
        
        disp.show(img)
        
        # 控制刷新率（约 20Hz）
        time.sleep_ms(50)


def simple_read():
    """最简单的 IMU 读取示例（无显示）"""
    
    # 初始化 IMU
    sensor = imu.IMU("default", 
                    mode=imu.Mode.DUAL,
                    acc_scale=imu.AccScale.ACC_SCALE_2G,
                    acc_odr=imu.AccOdr.ACC_ODR_1000,
                    gyro_scale=imu.GyroScale.GYRO_SCALE_256DPS,
                    gyro_odr=imu.GyroOdr.GYRO_ODR_8000)
    
    # 读取数据
    data = sensor.read_all(calib_gryo=True, radian=False)
    
    # 加速度
    print(f"Accel: x={data.acc.x}, y={data.acc.y}, z={data.acc.z}")
    
    # 陀螺仪
    print(f"Gyro: x={data.gyro.x}, y={data.gyro.y}, z={data.gyro.z}")
    
    # 温度
    print(f"Temp: {data.temp}")


def calibrate_gyro():
    """校准陀螺仪（需要将设备静置在平面上）"""
    
    sensor = imu.IMU("default", 
                    mode=imu.Mode.DUAL,
                    acc_scale=imu.AccScale.ACC_SCALE_2G,
                    acc_odr=imu.AccOdr.ACC_ODR_1000,
                    gyro_scale=imu.GyroScale.GYRO_SCALE_256DPS,
                    gyro_odr=imu.GyroOdr.GYRO_ODR_8000)
    
    print("[IMU] Starting gyro calibration...")
    print("[IMU] Place the device on a flat surface and don't move it!")
    print("[IMU] Calibrating for 10 seconds...")
    
    # 校准 10 秒（10000 毫秒）
    sensor.calib_gyro(10000)
    
    print("[IMU] Calibration complete!")
    print("[IMU] Calibration data has been saved.")


if __name__ == "__main__":
    main()
    # simple_read()  # 取消注释运行简单版本
    # calibrate_gyro()  # 取消注释运行校准
