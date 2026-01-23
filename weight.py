import serial, time

arduino = serial.Serial('COM7', 9600)
time.sleep(2)
print("Connected to Arduino on COM7")

while True:
    arduino.write(b'READ\n')
    data = arduino.readline().decode().strip()
    if data:
        print("Weight:", data, "g")
    time.sleep(1)
