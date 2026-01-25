import serial
import time
import matplotlib.pyplot as plt
from collections import deque

# Connect to Arduino
arduino = serial.Serial('COM7', 9600)
time.sleep(2)
print("✅ Connected to Arduino on COM7")

# Set up live plot
plt.ion()
fig, ax = plt.subplots()
ax.set_title("Real-Time Weight Reading")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Weight (g)")
line, = ax.plot([], [], 'b-', linewidth=2)

# Data containers
x_data, y_data = [], []
weights = deque(maxlen=5)  # keep last 5 readings for smoothing
start_time = time.time()

while True:
    try:
        arduino.write(b'READ\n')
        data = arduino.readline().decode().strip()

        if data:
            try:
                weight = float(data)

                # Filter small noise — only accept >0.4 g
                if weight >= 0.4:
                    weights.append(weight)
                    smoothed = sum(weights) / len(weights)

                    print(f"Weight: {weight:.2f} g | Smoothed: {smoothed:.2f} g")

                    # Update plot data
                    x_data.append(time.time() - start_time)
                    y_data.append(smoothed)

                    # Live plot update
                    line.set_xdata(x_data)
                    line.set_ydata(y_data)
                    ax.relim()
                    ax.autoscale_view()
                    plt.draw()
                    plt.pause(0.05)

                else:
                    print(f"⚠️ Ignored low value: {weight:.2f} g")

            except ValueError:
                print("⚠️ Non-numeric data:", data)

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
        break

# Clean up
arduino.close()

if len(weights) > 0:
    avg_weight = sum(weights) / len(weights)
    print(f"Average of last readings: {avg_weight:.2f} g")
else:
    print("No valid weight readings recorded.")
print("🔌 Disconnected from Arduino.")
