import smbus
import time
import math
from collections import deque


# Accelerometer class - sets up and returns accelerometer values as requested.
class Accelerometer:
    scaled_accel = [0, 0, 0]
    address = 0x68
    power_mgmt_1 = 0x6b
    total_accel = 0
    bus = 0

    cycle_num = 5  # number of cycles to use for maximum and average
    max_accel = 0  # maximum acceleration over the defined number of cycles.
    avg_accel = 0  # Average acceleration over cycles

    # Set up the accelerometer.  Power and sensitivity settings
    def __init__(self, cycle_num):
        # Start talking to accelerometer - standard I2C stuff.
        self.bus = smbus.SMBus(1)  # or bus = smbus.SMBus(1) for Revision 2 boards

        # Now wake the 6050 up as it starts in sleep mode
        self.bus.write_byte_data(self.address, self.power_mgmt_1, 0)

        # Write the setup to the accelerometer -value of 3 in AFS_SEL gives accel range of 16g.
        # The register to use is 1C (28 decimal)
        self.bus.write_byte_data(self.address, 0x1C, 0b00011000)

        # Assign cycle num in object to the one passed in.
        self.cycle_num = cycle_num

        # Create the queue ot recent reads.
        self.recent_reads = deque([0] * cycle_num)
        print(self.recent_reads)

    # Read word from accelerometer
    def read_word_2c(self, adr):
        high = self.bus.read_byte_data(self.address, adr)
        low = self.bus.read_byte_data(self.address, adr + 1)
        val = (high << 8) + low

        if val >= 0x8000:
            return -((65535 - val) + 1)
        else:
            return val

    # Returns the scaled values
    def get_scaled_accel_values(self):
        try:
            # Grab Accelerometer Data
            self.scaled_accel = [self.read_word_2c(0x3b) / 16384.0 * 8, self.read_word_2c(0x3d) / 16384.0 * 8,
                                 self.read_word_2c(0x3f) / 16384.0 * 8]

        except KeyboardInterrupt:
            raise

        except:
            print("** Read failed - assume 0 accel")
            self.scaled_accel = [0, 0, 0]

        # Scaling is 16g, so scale the 2 bytes to get the +/-16g
        self.total_accel = math.sqrt(self.scaled_accel[0] ** 2 + self.scaled_accel[1] ** 2 + self.scaled_accel[2] ** 2)

        self.recent_reads.append(self.total_accel)
        self.recent_reads.popleft()
        self.max_accel = max(self.recent_reads)


if __name__ == "__main__":

    # Create the accelerometer object.
    my_accel = Accelerometer(10)

    # Read continuously, refreshing the values each read.
    try:
        while (1):

            my_accel.get_scaled_accel_values()

            #if my_accel.total_accel > 4:
            print(time.time(), my_accel.total_accel, "^^", my_accel.max_accel)

    except KeyboardInterrupt:
        print("closing")

    finally:
        print("All done")
