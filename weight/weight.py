import serial
import time
import matplotlib.pyplot as plt
import keyboard
import sys
import threading

# Connect to Arduino
arduino = serial.Serial('COM7', 9600)
print("✅ Connected to Arduino on COM7")

# Item tracking
current_item_readings = []
items = []
item_detected = False
weight_min = 0.4      # minimum weight considered as a valid item
empty_delay = 0.01   # seconds to confirm item removed
last_above_time = 0
delay = 0.5
pause = False
running = True

class PlotData:
    def __init__(self):
        self.fig = None
        self.ax = None
        self.line = None

        self.x_data = []
        self.y_data = []
        self.start_time = None

        self.active = False

    # --- Initialize and show plot ---
    def setup(self):
        if self.fig is not None:
            return
        
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Real-Time Weight Reading")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Weight (g)")

        self.line, = self.ax.plot([], [], linewidth=2)

        self.x_data = []
        self.y_data = []
        self.start_time = time.time()
        self.active = True
        plt.show(block=False) 
        print("📈 Plot view ON")

    # --- Update graph with new weight ---
    def update(self, weight):
        if not self.active:
            return

        self.x_data.append(time.time() - self.start_time)
        self.y_data.append(weight)

        self.line.set_xdata(self.x_data)
        self.line.set_ydata(self.y_data)

        self.ax.relim()
        self.ax.autoscale_view()

        self.plt.draw(xlim=self.ax.get_xlim(), ylim=self.ax.get_ylim())
        plt.pause(0.0001)

    # --- Clear existing graph ---
    def clear(self):
        if not self.active :
            return

        self.x_data.clear()
        self.y_data.clear()

        self.line.set_xdata([])
        self.line.set_ydata([])

        self.fig.canvas.draw_idle()
        plt.pause(0.0001)
        print("🧼 Plot cleared.")

    # --- Close plot window ---
    def close(self):
        if not self.active:
            return

        plt.close(self.fig)
        self.active = False
        self.fig = None
        print("📉 Plot view OFF")
        
    def background_update(self):
        if not self.active:
            self.setup()
        
        thread = threading.Thread(target=self.background_loop, daemon=True)
        thread.start()
        
    def background_loop(self):
        while self.active:
            if self.x_data and self.y_data:
                self.fig.canvas.draw_idle()
                plt.pause(0.001)
            time.sleep(0.1)

auto_sleep = 300
sleep_mode = False
class keyboard_functions:
    plotter = PlotData()
    show_plot = False
    
    # def pause_program(self):
    #     global pause,auto_sleep,items
    #     auto_sleep = False  
    #     pause = not pause
        
    #     state = "⏸️ Paused" if pause else "▶️ Resumed"        
    #     print(f"\n{state}")

    #     if items:
    #         print(f"🧮 Summary of recorded items:{len(items)}")
    #         for i, w in enumerate(items, 1):
    #             print(f"   Item {i}: {w:.2f} g")
    #         print(f"📊 Total weight of all items: {sum(items):.2f} g")

    #     time.sleep(delay)  # debounce key press
        
            
    def clean_record(self):
        global items
        items.clear()
        print("\n🗑️ Cleared all recorded items.")
        time.sleep(delay)
        
    def quit_program(self):
        global running
        running = False
        print("\n🛑 Quitting program.")

    def show_plot(self):        
        plotter.setup()
        
        time.sleep(delay)
        
    def system_sleep(self, flag:bool):
        self.sleep = flag
        return flag
        
        
    def clear_plot(self):
        global plotter
        plotter.clear()
        time.sleep(delay)
        

show_plot = False

# keyboard.add_hotkey('space',lambda:KF.pause_program())
keyboard.add_hotkey('c',lambda:KF.clean_record())
keyboard.add_hotkey('q',lambda:KF.quit_program())   
keyboard.add_hotkey('p',lambda:KF.show_plot())
keyboard.add_hotkey('i',lambda:KF.clear_plot())

try:
    plotter = PlotData()
    KF = keyboard_functions()
    current_time = time.time()
    
    while running:
        if not pause and (time.time() - current_time) > auto_sleep and not item_detected:
            if not sleep_mode:
                sleep_mode = True
                print("\n🛌 System sleep due to inactivity.")  
                
        if pause or sleep_mode:            
            if data:
                try:
                    weight = float(data)
                    if weight >= weight_min:
                        print("\n🌅 Waking up from sleep mode.")
                        sleep_mode = False
                        last_above_time = time.time()
                        pause = False
                    
                except ValueError:
                    print("⚠️ Non-numeric data:", data)
            KF.system_sleep(True)
                
        KF.system_sleep(False)
        current_time = time.time()
            

        # --- Read Arduino data ---
        
        arduino.write(b'READ\n')
        data = arduino.readline().decode().strip()
            

        if data:
            try:
                weight = float(data)
                    
                if show_plot:
                    plotter.update(weight)
                    time.sleep(0.01)
                else:
                    time.sleep(0.001)

                # --- Item detection logic ---
                if weight >= weight_min:
                    current_item_readings.append(weight)
                    last_above_time = time.time()

                    if not item_detected:
                        item_detected = True
                        print(f"\n📦 Item detected! Counting readings...")

                elif item_detected and (time.time() - last_above_time) > empty_delay:
                    current_item_readings = current_item_readings[1:-1]
                    if not current_item_readings:
                        print("⚠️ No valid readings for item. Discarded.")
                        item_detected = False
                        continue
                    avg_weight = sum(current_item_readings) / len(current_item_readings)
                    items.append(avg_weight)
                    print(f"✅ Item {len(items)} recorded | Average weight: {avg_weight:.2f} g")
                    current_item_readings.clear()
                    item_detected = False

                # Print live weight
                print(f"Live weight: {weight:.2f} g", end='\r')

            except ValueError:
                print("⚠️ Non-numeric data:", data)

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n🛑 Stopped by user.")

finally:
# --- Summary after stopping ---
    if 'arduino' in locals() and arduino.is_open:
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
        
    sys.exit(0)
