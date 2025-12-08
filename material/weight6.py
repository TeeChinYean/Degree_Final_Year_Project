import serial
import time
import matplotlib.pyplot as plt
import keyboard
import sys

arduino = serial.Serial('COM7', 9600, timeout=1)
print("✅ Connected to Arduino on COM7")


# Globals 
current_item_readings = []
items = []
item_detected = False
weight_min = 0.4
empty_delay = 0.01

pause = False
running = True

show_plot_flag = False
clear_plot_flag = False

class PlotData:
    def __init__(self):
        self.fig = None
        self.ax = None
        self.line = None
        self.x_data = []
        self.y_data = []
        self.start_time = None
        self.active = False

    def setup(self):
        if self.active:
            return
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Real-Time Weight Reading")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Weight (g)")
        (self.line,) = self.ax.plot([], [], linewidth=2)
        self.x_data = []
        self.y_data = []
        self.start_time = time.time()
        self.active = True
        plt.show(block=False)
        print("📈 Plot view ON")

    def update(self, weight):
        if not self.active:
            return
        self.x_data.append(time.time() - self.start_time)
        self.y_data.append(weight)
        self.line.set_xdata(self.x_data)
        self.line.set_ydata(self.y_data)
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw_idle()
        plt.pause(0.001)

    def clear(self):
        if not self.active:
            return
        self.x_data.clear()
        self.y_data.clear()
        self.line.set_xdata([])
        self.line.set_ydata([])
        self.fig.canvas.draw_idle()
        plt.pause(0.001)
        print("🧼 Plot cleared.")

    def close(self):
        if not self.active:
            return
        plt.close(self.fig)
        self.active = False
        self.fig = None
        print("📉 Plot view OFF")

plotter = PlotData()

# -------------------------
# Hotkey callbacks
# -------------------------
def toggle_pause():
    global pause
    pause = not pause
    print("⏸️ Paused" if pause else "▶️ Resumed")

def clear_records():
    global items
    items.clear()
    print("🗑️ Cleared recorded items")

def quit_program():
    global running
    print("🛑 Quit requested")
    running = False

def toggle_plot():
    global show_plot_flag
    show_plot_flag = not show_plot_flag
    print("Toggle plot:", "ON" if show_plot_flag else "OFF")

def request_clear_plot():
    global clear_plot_flag
    clear_plot_flag = True

# Register hotkeys (these callbacks are small and safe)
keyboard.add_hotkey('space', toggle_pause)
keyboard.add_hotkey('c', clear_records)
keyboard.add_hotkey('q', quit_program) 
keyboard.add_hotkey('p', toggle_plot)
keyboard.add_hotkey('i', request_clear_plot)  

# -------------------------
# Main loop (all GUI calls here)
# -------------------------
try:
    last_above_time = 0
    start_time = time.time()
    while running:
        # handle plot flag in main thread (safe GUI calls)
        if show_plot_flag and not plotter.active:
            plotter.setup()
        if not show_plot_flag and plotter.active:
            plotter.close()
        if clear_plot_flag:
            if plotter.active:
                plotter.clear()
            clear_plot_flag = False

        # Read serial (ask and read)
        try:
            arduino.write(b'READ\n')
        except Exception as e:
            print("⚠️ Serial write failed:", e)
            time.sleep(0.2)
            continue

        raw = arduino.readline().decode(errors='ignore').strip()
        if not raw:
            # no data available; yield some time
            time.sleep(0.01)
            continue

        # Ignore non-numeric lines safely
        try:
            weight = float(raw)
        except ValueError:
            print("⚠️ Non-numeric data:", raw)
            time.sleep(0.01)
            continue

        # If plotting active, update plot (main thread)
        if plotter.active:
            plotter.update(weight)

        # Item detection logic (unchanged)
        if weight >= weight_min:
            current_item_readings.append(weight)
            last_above_time = time.time()
            if not item_detected:
                item_detected = True
                print("\n📦 Item detected! Counting readings...")

        elif item_detected and (time.time() - last_above_time) > empty_delay:
            usable = current_item_readings[1:-1] if len(current_item_readings) > 3 else list(current_item_readings)
            if usable:
                avg_weight = sum(usable) / len(usable)
                items.append(avg_weight)
                print(f"✅ Item {len(items)} recorded | Average weight: {avg_weight:.2f} g")
            else:
                print("⚠️ Not enough readings; discarded.")
            current_item_readings.clear()
            item_detected = False

        # Live weight print
        print(f"Live weight: {weight:.2f} g", end='\r')

        # tiny sleep to avoid 100% CPU and allow GUI events
        time.sleep(0.005)

except KeyboardInterrupt:
    print("\n🛑 Stopped by user.")

finally:
    # Cleanup
    if arduino and arduino.is_open:
        arduino.close()
        print("\n🔌 Disconnected from Arduino.")
    if plotter.active:
        plotter.close()

    # Summary
    if items:
        print(f"🧮 Summary of recorded items: {len(items)}")
        for i, w in enumerate(items, 1):
            print(f"   Item {i}: {w:.2f} g")
        print(f"📊 Total weight: {sum(items):.2f} g")
    else:
        print("No items were recorded.")
    sys.exit(0)
