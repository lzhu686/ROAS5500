import smbus
import time

# Configuration
I2C_ADDR = 0x34
BUS_ID = 4
SPEAK_REG = 0x6E

# Command Types
CMD_COMMAND = 0x00  # Play a Command Word (e.g., "Wake up")
CMD_BROADCAST = 0xFF # Play a Broadcast Word (e.g., "Welcome")

def test_broadcast(bus, cmd_type, phrase_id):
    print(f"Testing: Type={hex(cmd_type)}, ID={phrase_id}")
    try:
        # Method 1: write_i2c_block_data (Standard)
        # Sends: [Start] [Addr] [Reg] [Cmd] [Id] [Stop]
        data = [cmd_type, phrase_id]
        bus.write_i2c_block_data(I2C_ADDR, SPEAK_REG, data)
        print("  -> Command sent successfully (ACK received)")
    except Exception as e:
        print(f"  -> Failed: {e}")

def main():
    print("========================================")
    print("WonderEcho I2C Broadcast Diagnostic Tool")
    print("========================================")
    print(f"Bus: {BUS_ID}, Address: {hex(I2C_ADDR)}")
    
    try:
        bus = smbus.SMBus(BUS_ID)
    except Exception as e:
        print(f"Error opening I2C bus: {e}")
        return

    print("\n[Test 1] Testing 'Broadcast' type (0xFF)")
    print("Trying IDs 1 to 5...")
    for i in range(1, 6):
        test_broadcast(bus, CMD_BROADCAST, i)
        time.sleep(3) # Wait for audio to play

    print("\n[Test 2] Testing 'Command' type (0x00)")
    print("Trying IDs 1 to 5...")
    for i in range(1, 6):
        test_broadcast(bus, CMD_COMMAND, i)
        time.sleep(3)

    print("\n[Test 3] Testing Special IDs (10, 100)")
    test_broadcast(bus, CMD_BROADCAST, 10)
    time.sleep(3)
    test_broadcast(bus, CMD_BROADCAST, 100)
    time.sleep(3)

    print("\n========================================")
    print("Test Complete.")
    print("If you heard ANY sound, note the Type and ID.")
    print("If NO sound, the module might be in a mode that disables I2C audio,")
    print("or the firmware does not have these IDs configured.")

if __name__ == "__main__":
    main()
