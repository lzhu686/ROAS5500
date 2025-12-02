"""MaixCAM-Pro QMI8658 IMU 直接读取

使用 ext_dev.qmi8658 直接驱动读取 IMU 数据
MaixCAM-Pro 的 QMI8658 挂载在 I2C4 上

如果 imu.IMU("default") 失败，请尝试这个脚本
"""

from maix import ext_dev, app, time, display, image
import math


def calculate_tilt_angles(acc_x, acc_y, acc_z):
    """从加速度计数据计算倾斜角"""
    roll = math.atan2(acc_y, acc_z) * 180 / math.pi
    pitch = math.atan2(-acc_x, math.sqrt(acc_y**2 + acc_z**2)) * 180 / math.pi
    return pitch, roll


def main():
    """读取 QMI8658 IMU 数据"""
    
    disp = display.Display()
    
    # QMI8658 在 MaixCAM-Pro 上的 I2C 总线号是 4
    QMI8658_I2CBUS_NUM = 4
    
    try:
        # 直接使用 QMI8658 驱动
        imu_sensor = ext_dev.qmi8658.QMI8658(
            QMI8658_I2CBUS_NUM,
            mode=ext_dev.imu.Mode.DUAL,
            acc_scale=ext_dev.imu.AccScale.ACC_SCALE_2G,
            acc_odr=ext_dev.imu.AccOdr.ACC_ODR_1000,
            gyro_scale=ext_dev.imu.GyroScale.GYRO_SCALE_256DPS,
            gyro_odr=ext_dev.imu.GyroOdr.GYRO_ODR_8000
        )
        print("[QMI8658] Initialized successfully on I2C4")
    except Exception as e:
        print(f"[QMI8658] Init failed: {e}")
        print("[QMI8658] Please check:")
        print("  1. Make sure you have MaixCAM-Pro (not standard MaixCAM)")
        print("  2. Update MaixPy to the latest version")
        return
    
    print("\n[QMI8658] Starting data reading... Press Ctrl+C to stop\n")
    
    while not app.need_exit():
        try:
            # QMI8658.read() 返回 tuple: (acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, temp)
            data = imu_sensor.read()
            
            acc_x, acc_y, acc_z = data[0], data[1], data[2]
            gyro_x, gyro_y, gyro_z = data[3], data[4], data[5]
            temp = data[6]
            
            # 计算倾斜角
            pitch, roll = calculate_tilt_angles(acc_x, acc_y, acc_z)
            
            # 打印数据
            print(f"--- QMI8658 Data ---")
            print(f"Accel:  x={acc_x:8.4f}, y={acc_y:8.4f}, z={acc_z:8.4f}")
            print(f"Gyro:   x={gyro_x:8.4f}, y={gyro_y:8.4f}, z={gyro_z:8.4f}")
            print(f"Temp:   {temp:.1f}C")
            print(f"Angles: Pitch={pitch:7.2f}, Roll={roll:7.2f}")
            print()
            
            # 显示到屏幕
            img = image.Image(disp.width(), disp.height(), image.Format.FMT_RGB888)
            img.draw_rect(0, 0, img.width(), img.height(), image.COLOR_BLACK, -1)
            
            y = 10
            img.draw_string(10, y, "=== QMI8658 IMU ===", image.COLOR_GREEN, 1.5)
            y += 35
            
            img.draw_string(10, y, f"Accel:", image.COLOR_WHITE, 1.2)
            y += 25
            img.draw_string(20, y, f"X:{acc_x:8.3f}", image.COLOR_YELLOW, 1.2)
            y += 22
            img.draw_string(20, y, f"Y:{acc_y:8.3f}", image.COLOR_YELLOW, 1.2)
            y += 22
            img.draw_string(20, y, f"Z:{acc_z:8.3f}", image.COLOR_YELLOW, 1.2)
            y += 30
            
            img.draw_string(10, y, f"Gyro:", image.COLOR_WHITE, 1.2)
            y += 25
            img.draw_string(20, y, f"X:{gyro_x:8.3f}", image.COLOR_YELLOW, 1.2)
            y += 22
            img.draw_string(20, y, f"Y:{gyro_y:8.3f}", image.COLOR_YELLOW, 1.2)
            y += 22
            img.draw_string(20, y, f"Z:{gyro_z:8.3f}", image.COLOR_YELLOW, 1.2)
            y += 30
            
            img.draw_string(10, y, f"Temp: {temp:.1f} C", image.COLOR_CYAN, 1.2)
            y += 35
            
            img.draw_string(10, y, "=== Tilt Angles ===", image.COLOR_GREEN, 1.5)
            y += 30
            img.draw_string(20, y, f"Pitch: {pitch:7.2f} deg", image.COLOR_RED, 1.3)
            y += 25
            img.draw_string(20, y, f"Roll:  {roll:7.2f} deg", image.COLOR_RED, 1.3)
            
            disp.show(img)
            
        except Exception as e:
            print(f"[QMI8658] Read error: {e}")
        
        time.sleep_ms(50)  # ~20Hz


def simple_read():
    """简单读取一次数据"""
    QMI8658_I2CBUS_NUM = 4
    
    imu_sensor = ext_dev.qmi8658.QMI8658(
        QMI8658_I2CBUS_NUM,
        mode=ext_dev.imu.Mode.DUAL,
        acc_scale=ext_dev.imu.AccScale.ACC_SCALE_2G,
        acc_odr=ext_dev.imu.AccOdr.ACC_ODR_1000,
        gyro_scale=ext_dev.imu.GyroScale.GYRO_SCALE_256DPS,
        gyro_odr=ext_dev.imu.GyroOdr.GYRO_ODR_8000
    )
    
    data = imu_sensor.read()
    print(f"Accel: x={data[0]}, y={data[1]}, z={data[2]}")
    print(f"Gyro:  x={data[3]}, y={data[4]}, z={data[5]}")
    print(f"Temp:  {data[6]}")


if __name__ == "__main__":
    main()
    # simple_read()
