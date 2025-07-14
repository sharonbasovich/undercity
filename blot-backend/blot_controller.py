import serial
from cobs import cobs
import struct
import time

# Change this to your actual serial port (check with Arduino IDE Tools > Port)
SERIAL_PORT = 'COM25'
BAUD_RATE = 9600

# Open serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

msg_count = 0

def send_message(event, payload_bytes=b''):
    global msg_count
    event_bytes = event.encode('utf-8')
    msg_len = len(event_bytes)
    payload_len = len(payload_bytes)

    message = bytearray()
    message.append(msg_len)
    message.extend(event_bytes)
    message.append(payload_len)
    message.extend(payload_bytes)
    message.append(msg_count)

    # COBS encode
    encoded = cobs.encode(message)
    # Add 0x00 delimiter at end
    ser.write(encoded + b'\x00')

    msg_count = (msg_count + 1) % 256


def go(x, y):
    payload = struct.pack('<ff', x, y)
    send_message('go', payload)

def pen_up():
    send_message('servo', struct.pack('<i', 500))  # high pulse for pen up

def pen_down():
    send_message('servo', struct.pack('<i', 2500))   # low pulse for pen down

def motors_on():
    send_message('motorsOn')

def motors_off():
    send_message('motorsOff')


# Example program to draw a simple square
def draw_square(size):
    motors_on()
    time.sleep(0.5)

    pen_down()
    go(0, size)
    time.sleep(1)

    go(size, size)
    time.sleep(1)

    go(size, 0)
    time.sleep(1)

    go(0, 0)
    time.sleep(1)

    pen_up()
    motors_off()


if __name__ == '__main__':
    input("Press Enter to start...")
    # draw_square(50)
# 125, 
    motors_on()
    # motors_off()
    # time.sleep(0.5)
    # go(0, 125)
    # time.sleep(6)
    # go(120, 120)
    pen_down()
    time.sleep(0.1)
    print("Done.")
    ser.close()
