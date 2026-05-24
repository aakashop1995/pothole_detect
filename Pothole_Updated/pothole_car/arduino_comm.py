import serial
import time

arduino = None
last_command_time = 0
last_command = None

try:
    arduino = serial.Serial(
        '/dev/ttyACM0',
        9600,
        timeout=1,
        write_timeout=1
    )
    time.sleep(2)
    print("Arduino connected on /dev/ttyACM0")
except Exception as e:
    print("Arduino not connected:", e)


def send_ready():
    if arduino is None:
        return
    try:
        arduino.write("READY\n".encode())
        print("Sent READY to Arduino")
    except Exception as e:
        print("Send ready error:", e)


def send_command(command):
    global last_command_time, last_command
    if arduino is None:
        return
    current_time = time.time()
    if command != last_command or current_time - last_command_time > 0.5:
        try:
            arduino.write((command + "\n").encode())
            last_command = command
            last_command_time = current_time
        except serial.SerialTimeoutException:
            print("Arduino write timeout - skipping")
        except Exception as e:
            print("Send error:", e)
