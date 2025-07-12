import serial
from cobs import cobs
import struct
from queue import Queue

SERIAL_PORT = 'COM25'
BAUD_RATE = 9600

# Open the serial port
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Create a message queue (same pattern as backend)
serial_queue = Queue()

# Signal the worker thread to stop by putting `None` in the queue
serial_queue.put(None)

# Optionally: send a shutdown message to Blot (if your firmware supports it)
def send_shutdown():
    event_bytes = 'shutdown'.encode('utf-8')
    msg_len = len(event_bytes)

    message = bytearray()
    message.append(msg_len)
    message.extend(event_bytes)
    message.append(0)
    message.append(0)

    encoded = cobs.encode(message) + b'\x00'
    ser.write(encoded)

# Uncomment if your blot supports this command
# send_shutdown()

# Close the serial port
ser.close()

print("Serial queue signaled to shut down. Serial port closed.")
