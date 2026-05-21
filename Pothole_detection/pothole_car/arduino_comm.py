import serial
import time

arduino = None

try:
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    time.sleep(2)

    print("Arduino connected on /dev/ttyACM0")

except Exception as e:
    print("Arduino not connected:", e)


def send_command(command):

    if arduino is not None:

        try:
            arduino.write((command + "\n").encode())

        except Exception as e:
            print("Send error:", e)
