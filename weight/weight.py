import serial
import time
import matplotlib.pyplot as plt
import keyboard
import os

# Connect to Arduino
arduino = serial.Serial('COM7', 9600)
print("✅ Connected to Arduino on COM7")

# # Live plot setup
# plt.ion()
# fig, ax = plt.subplots()
# ax.set_title("Real-Time Weight Reading")
# ax.set_xlabel("Time (s)")
# ax.set_ylabel("Weight (g)")
# line, = ax.plot([], [], 'b-', linewidth=2)
# x_data, y_data = [], []
# start_time = time.time()

# Item tracking
current_item_readings = []
items = []
item_detected = False
weight_min = 0.4      # minimum weight considered as a valid item
empty_delay = 0.01   # seconds to confirm item removed
last_above_time = 0
pause = False
delay = 0.1
try:
    while True:
        # Toggle pause when spacebar pressed
        if keyboard.is_pressed('space'):
            pause = not pause
            state = "⏸️ Paused" if pause else "▶️ Resumed"
            print(f"\n{state}")

            if items:
                print(f"🧮 Summary of recorded items:{len(items)}")
                for i, w in enumerate(items, 1):
                    print(f"   Item {i}: {w:.2f} g")
                total_weight = sum(items)
                print(f"📊 Total weight of all items: {total_weight:.2f} g")

            time.sleep(delay)  # debounce key press

        if keyboard.is_pressed('c'):
            items.clear()
            print("\n🗑️ Cleared all recorded items.")
            time.sleep(delay)  # debounce key press
            
        if keyboard.is_pressed('q'):
            print("\n🛑 Quitting program.")
            break
        
        # Skip data updates if paused
        if pause:
            continue
            
        # --- Read Arduino data ---
        arduino.write(b'READ\n')
        data = arduino.readline().decode().strip()

        if data:
            try:
                weight = float(data)

                # # Update live plot
                # x_data.append(time.time() - start_time)
                # y_data.append(weight)
                # line.set_xdata(x_data)
                # line.set_ydata(y_data)
                # ax.relim()
                # ax.autoscale_view()
                # plt.draw()
                # plt.pause(0.05)

                # --- Item detection logic ---
                if weight >= weight_min:
                    current_item_readings.append(weight)
                    last_above_time = time.time()

                    if not item_detected:
                        item_detected = True
                        print(f"\n📦 Item detected! Counting readings...")

                elif item_detected and (time.time() - last_above_time) > empty_delay:
                    current_item_readings = current_item_readings[1:-1]
                    avg_weight = sum(current_item_readings) / len(current_item_readings)
                    items.append(avg_weight)
                    print(f"✅ Item {len(items)} recorded | Average weight: {avg_weight:.2f} g")
                    current_item_readings.clear()
                    item_detected = False

                # Print live weight
                print(f"Live weight: {weight:.2f} g", end='\r')

            except ValueError:
                print("⚠️ Non-numeric data:", data)

        time.sleep(0.001)

except KeyboardInterrupt:
    print("\n🛑 Stopped by user.")

# --- Summary after stopping ---
arduino.close()
print("\n🔌 Disconnected from Arduino.")


if items:
    print(f"🧮 Summary of recorded items:{len(items)}")
    for i, w in enumerate(items, 1):
        print(f"   Item {i}: {w:.2f} g")
    total_weight = sum(items)
    print(f"📊 Total weight of all items: {total_weight:.2f} g")
else:
    print("No items were recorded.")
