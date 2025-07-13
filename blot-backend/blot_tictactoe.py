import serial
from cobs import cobs
import struct
import time
import random

SERIAL_PORT = 'COM25'
BAUD_RATE = 9600

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
msg_count = 0

cell_size = 20
grid_origin = (0, 0)

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

    encoded = cobs.encode(message)
    ser.write(encoded + b'\x00')
    msg_count = (msg_count + 1) % 256

def go(x, y):
    payload = struct.pack('<ff', x, y)
    send_message('go', payload)

def pen_up():
    send_message('servo', struct.pack('<i', 500))

def pen_down():
    send_message('servo', struct.pack('<i', 2500))

def motors_on():
    send_message('motorsOn')

def motors_off():
    send_message('motorsOff')

def draw_X(x, y):
    pen_down()
    go(x - 5, y - 5)
    go(x + 5, y + 5)
    pen_up()
    go(x - 5, y + 5)
    pen_down()
    go(x + 5, y - 5)
    pen_up()

def draw_O(x, y):
    pen_down()
    go(x - 5, y)
    go(x, y + 5)
    go(x + 5, y)
    go(x, y - 5)
    go(x - 5, y)
    pen_up()

def cell_center(cell):
    col = (cell - 1) % 3
    row = (cell - 1) // 3
    x = grid_origin[0] + col * cell_size + cell_size / 2
    y = grid_origin[1] + row * cell_size + cell_size / 2
    return (x, y)

def draw_mark(player, cell):
    x, y = cell_center(cell)
    go(x, y)
    if player == 'X':
        draw_X(x, y)
    elif player == 'O':
        draw_O(x, y)
    
    # Move blot to bottom-left corner after move
    go(grid_origin[0] - 10, grid_origin[1] - 10)

def check_winner(board):
    lines = [
        [1,2,3],[4,5,6],[7,8,9],
        [1,4,7],[2,5,8],[3,6,9],
        [1,5,9],[3,5,7]
    ]
    for line in lines:
        if board[line[0]] == board[line[1]] == board[line[2]] and board[line[0]] != ' ':
            return board[line[0]]
    if all(board[c] != ' ' for c in range(1,10)):
        return 'D'
    return None

def draw_grid():
    print("Drawing grid...")
    motors_on()
    time.sleep(0.5)

    for i in range(1, 3):
        x = grid_origin[0] + i * cell_size
        go(x, grid_origin[1])
        pen_down()
        go(x, grid_origin[1] + 3 * cell_size)
        pen_up()

    for i in range(1, 3):
        y = grid_origin[1] + i * cell_size
        go(grid_origin[0], y)
        pen_down()
        go(grid_origin[0] + 3 * cell_size, y)
        pen_up()

    print("Grid drawn.")

def ai_move(board):
    available = [c for c in range(1, 10) if board[c] == ' ']
    return random.choice(available)

def print_board(board):
    print("\n")
    for r in [1,4,7]:  # <-- corrected to match blot's drawing order
        print(f" {board[r]} | {board[r+1]} | {board[r+2]}")
        if r != 7:
            print("---+---+---")
    print("\n")

def main():
    motors_on()
    time.sleep(1)
    draw_grid()

    board = {i:' ' for i in range(1,10)}
    print("Tic Tac Toe — you are X. Enter 1-9 for your move (like a numpad):")

    try:
        winner = None
        while not winner:
            print_board(board)
            while True:
                try:
                    move = int(input("Your move (1-9): "))
                    if 1 <= move <=9 and board[move] == ' ':
                        break
                    else:
                        print("Invalid move, try again.")
                except ValueError:
                    print("Invalid input, try again.")

            board[move] = 'X'
            draw_mark('X', move)
            time.sleep(0.5)

            winner = check_winner(board)
            if winner:
                break

            ai = ai_move(board)
            board[ai] = 'O'
            print(f"Blot chooses {ai}.")
            draw_mark('O', ai)
            time.sleep(0.5)

            winner = check_winner(board)

        print_board(board)
        if winner == 'X':
            print("You win!")
        elif winner == 'O':
            print("Blot wins!")
        else:
            print("It's a draw!")

    except KeyboardInterrupt:
        print("\nGame interrupted. Stopping blot...")

    finally:
        pen_up()
        go(0, 0)
        motors_off()
        ser.close()
        print("Blot safely stopped.")

if __name__ == "__main__":
    main()
