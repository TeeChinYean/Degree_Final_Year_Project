import RPi.GPIO as GPIO
import time
import statistics

class HX711:
    def __init__(self, dout_pin, sck_pin, gain_channel_A=128):
        """
        Initialize the HX711 module.
        Args:
            dout_pin (int): The BCM pin number for the data (DOUT) pin.
            sck_pin (int): The BCM pin number for the clock (SCK) pin.
            gain_channel_A (int): The gain for channel A. Can be 128 or 64.
                                  Channel B has a fixed gain of 32.
        """
        self.SCK_PIN = sck_pin
        self.DOUT_PIN = dout_pin
        
        # Make sure RPi.GPIO is in BCM mode
        if GPIO.getmode() != GPIO.BCM:
            try:
                GPIO.setmode(GPIO.BCM)
            except Exception as e:
                print(f"Warning: Could not set GPIO mode to BCM. Error: {e}")
                print("Please ensure GPIO.setmode(GPIO.BCM) is called at the start of your main script.")

        GPIO.setup(self.SCK_PIN, GPIO.OUT)
        GPIO.setup(self.DOUT_PIN, GPIO.IN)

        self.GAIN = 0
        self.OFFSET = 0
        self.REFERENCE_UNIT = 1  # Default reference unit

        self.set_gain(gain_channel_A)
        
        # The library is ready, but not tared yet.
        # Call tare() or set_offset() before getting weights.

    def set_gain(self, gain):
        """
        Set the gain and channel.
        Args:
            gain (int): Gain for channel A (128 or 64). Channel B (32) is selected by setting gain to 32.
        """
        if gain == 128:
            self.GAIN = 1  # Channel A, gain 128
        elif gain == 64:
            self.GAIN = 3  # Channel A, gain 64
        elif gain == 32:
            self.GAIN = 2  # Channel B, gain 32
        else:
            raise ValueError("Invalid gain. Must be 128, 64, or 32.")
            
        # After changing gain, the next reading will be incorrect.
        # We read once to "prime" the new gain setting.
        self.read()

    def is_ready(self):
        """Check if the HX711 is ready to send data."""
        return GPIO.input(self.DOUT_PIN) == 0

    def read(self):
        """
        Read a single raw value from the HX711.
        This blocks until the data is ready.
        """
        # Wait for the DOUT pin to go low
        while not self.is_ready():
            time.sleep(0.001) # Small delay to prevent busy-waiting

        raw_data = 0
        
        # Clock out the 24 bits of data
        for _ in range(24):
            GPIO.output(self.SCK_PIN, True)
            GPIO.output(self.SCK_PIN, False)
            raw_data = (raw_data << 1) | GPIO.input(self.DOUT_PIN)

        # Send clock pulses to set the gain for the next reading
        for _ in range(self.GAIN):
            GPIO.output(self.SCK_PIN, True)
            GPIO.output(self.SCK_PIN, False)

        # The 24th bit is the sign bit. If it's 1, the number is negative.
        # Perform two's complement conversion
        if (raw_data & 0x800000): # Check if the 24th bit (sign bit) is set
            raw_data |= ~0xFFFFFF # Extend the sign bit to 32 bits
            
        return raw_data

    def read_average(self, times=5):
        """
        Read the average of multiple raw values.
        Args:
            times (int): The number of readings to average.
        Returns:
            float: The average raw value.
        """
        values = []
        for _ in range(times):
            values.append(self.read())
            time.sleep(0.01) # Short delay between readings
        
        # Use statistics.mean for a robust average
        return statistics.mean(values)
        
    def read_median(self, times=5):
        """
        Read the median of multiple raw values.
        This is good for filtering out occasional noise spikes.
        Args:
            times (int): The number of readings to take. Must be odd (or will be incremented).
        Returns:
            float: The median raw value.
        """
        if times % 2 == 0:
            times += 1 # Ensure odd number for a true median
            
        values = []
        for _ in range(times):
            values.append(self.read())
            time.sleep(0.01)
            
        return statistics.median(values)

    def get_value(self, times=5):
        """
        Get the raw value, adjusted for the offset (tare).
        Args:
            times (int): The number of readings to average.
        Returns:
            float: The tared (offset-adjusted) value.
        """
        return self.read_average(times) - self.OFFSET

    def get_weight(self, times=5):
        """
        Get the weight in the calibrated units.
        Args:
            times (int): The number of readings to average.
        Returns:
            float: The weight.
        """
        value = self.get_value(times)
        return value / self.REFERENCE_UNIT

    def tare(self, times=15):
        """
        Tares the scale by setting the current reading as the offset (zero).
        Args:
            times (int): The number of readings to average for a stable tare.
        """
        self.set_offset(self.read_average(times))

    def set_offset(self, offset):
        """
        Set the offset (tare) value directly.
        Args:
            offset (float): The raw value to be considered zero.
        """
        self.OFFSET = offset

    def get_offset(self):
        """Get the current offset (tare) value."""
        return self.OFFSET

    def set_reference_unit(self, reference_unit):
        """
        Set the calibration factor (reference unit).
        This is (Raw Value - Offset) / Weight.
        Args:
            reference_unit (float): The calibration factor.
        """
        if reference_unit == 0:
            raise ValueError("Reference unit cannot be zero.")
        self.REFERENCE_UNIT = reference_unit

    def get_reference_unit(self):
        """Get the current reference unit."""
        return self.REFERENCE_UNIT

    def power_down(self):
        """Put the HX711 into power-down mode."""
        GPIO.output(self.SCK_PIN, False)
        GPIO.output(self.SCK_PIN, True)
        time.sleep(0.0001) # Must be held high for at least 60 microseconds

    def power_up(self):
        """Wake the HX711 from power-down mode."""
        GPIO.output(self.SCK_PIN, False)
        # The chip will wake up on the next read() call.

    def reset(self):
        """Resets the chip."""
        self.power_down()
        self.power_up()
