import serial

ports = ["/dev/serial0", "/dev/ttyAMA0", "/dev/ttyS0"]
baudrates = [9600, 38400, 57600, 115200]

for port in ports:
    for baud in baudrates:
        try:
            print(f"\nTesting {port} @ {baud}")

            gps = serial.Serial(port, baudrate=baud, timeout=2)

            for i in range(10):
                line = gps.readline().decode(errors='ignore')

                if line:
                    print(line.strip())

            gps.close()

        except Exception as e:
            print("Failed:", e)
