from flask import Flask, request, jsonify
import serial
from cobs import cobs
import struct
import time
import threading
import random
from queue import Queue
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Blot serial setup ---
SERIAL_PORT = 'COM25'
BAUD_RATE = 9600
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
msg_count = 0

cell_size = 20
# Move the 60x60 grid (3 cells × 20 units) so the top-left corner is at (5, 5)
grid_origin = (5, 5)

board = {i: ' ' for i in range(1, 10)}
current_turn = 'X'
game_over = False
winner = None

# --- Serial message queue setup ---
serial_queue = Queue()

def serial_worker():
    while True:
        message = serial_queue.get()
        if message is None:
            break
        ser.write(message)
        serial_queue.task_done()

serial_thread = threading.Thread(target=serial_worker, daemon=True)
serial_thread.start()

# --- Blot commands ---
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

    encoded = cobs.encode(message) + b'\x00'
    serial_queue.put(encoded)
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

def cell_center(cell):
    col = (cell - 1) % 3
    row = (cell - 1) // 3
    x = grid_origin[0] + col * cell_size + cell_size / 2
    y = grid_origin[1] + row * cell_size + cell_size / 2
    return (x, y)

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

def draw_winning_line(winning_cells):
    """Draw a line through the three winning cells"""
    if not winning_cells or len(winning_cells) != 3:
        return
    
    # Get the center coordinates of the three cells
    centers = [cell_center(cell) for cell in winning_cells]
    
    # Draw line from first to last cell
    start_x, start_y = centers[0]
    end_x, end_y = centers[2]
    
    pen_up()
    go(start_x, start_y)
    pen_down()
    go(end_x, end_y)
    pen_up()

def draw_mark(player, cell):
    x, y = cell_center(cell)
    go(x, y)
    if player == 'X':
        draw_X(x, y)
    elif player == 'O':
        draw_O(x, y)
    # Move to the opposite corner after drawing
    go(grid_origin[0] + 3 * cell_size + 10, grid_origin[1] + 3 * cell_size + 10)

def check_winner():
    lines = [
        [1, 2, 3], [4, 5, 6], [7, 8, 9],
        [1, 4, 7], [2, 5, 8], [3, 6, 9],
        [1, 5, 9], [3, 5, 7]
    ]
    for line in lines:
        if board[line[0]] == board[line[1]] == board[line[2]] and board[line[0]] != ' ':
            return board[line[0]], line
    if all(board[c] != ' ' for c in range(1, 10)):
        return 'D', None
    return None, None

def check_winner_for_board(board_state):
    """Check winner for a given board state (used by AI)"""
    lines = [
        [1, 2, 3], [4, 5, 6], [7, 8, 9],
        [1, 4, 7], [2, 5, 8], [3, 6, 9],
        [1, 5, 9], [3, 5, 7]
    ]
    for line in lines:
        if board_state[line[0]] == board_state[line[1]] == board_state[line[2]] and board_state[line[0]] != ' ':
            return board_state[line[0]]
    if all(board_state[c] != ' ' for c in range(1, 10)):
        return 'D'
    return None

def ai_move():
    available = [c for c in range(1, 10) if board[c] == ' ']
    if not available:
        return None
    
    # Check if AI can win in one move
    for cell in available:
        board_copy = board.copy()
        board_copy[cell] = 'O'
        winner = check_winner_for_board(board_copy)
        if winner == 'O':
            return cell
    
    # Check if player can win in one move and block it
    for cell in available:
        board_copy = board.copy()
        board_copy[cell] = 'X'
        winner = check_winner_for_board(board_copy)
        if winner == 'X':
            return cell
    
    # Otherwise, make a random move
    return random.choice(available)

def draw_grid():
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
    # Move to the opposite corner after drawing grid
    go(grid_origin[0] + 3 * cell_size + 10, grid_origin[1] + 3 * cell_size + 10)

# --- Draw text letters ---
def draw_text(text, start_x, start_y, spacing=8):
    x = start_x
    for char in text.upper():
        func = letter_funcs.get(char)
        if func:
            func(x, start_y)
        x += spacing

def draw_letter_Y(x, y, s=5):
    pen_down(); go(x, y + s); go(x + s/2, y + s/2)
    pen_up(); go(x + s, y + s)
    pen_down(); go(x + s/2, y + s/2); go(x + s/2, y); pen_up()

def draw_letter_O(x, y, s=5):
    pen_down(); go(x, y); go(x, y + s); go(x + s, y + s)
    go(x + s, y); go(x, y); pen_up()

def draw_letter_U(x, y, s=5):
    pen_down(); go(x, y + s); pen_up()
    go(x, y); pen_down(); go(x + s, y)
    go(x + s, y + s); pen_up()

def draw_letter_W(x, y, s=5):
    pen_down(); go(x, y + s); go(x + s/2, y)
    go(x + s, y + s); pen_up()

def draw_letter_I(x, y, s=5):
    pen_down(); go(x, y + s); pen_up()

def draw_letter_N(x, y, s=5):
    pen_down(); go(x, y); go(x, y + s); go(x + s, y)
    go(x + s, y + s); pen_up()

def draw_letter_L(x, y, s=5):
    pen_down(); go(x, y + s); pen_up()
    go(x, y); pen_down(); go(x + s, y); pen_up()

def draw_exclamation(x, y, s=5):
    pen_down(); go(x, y + s); pen_up()
    go(x, y - s/2); pen_down(); go(x, y - s/2 + 1); pen_up()

def draw_space(x, y, s=5):
    pass

letter_funcs = {
    'Y': draw_letter_Y, 'O': draw_letter_O, 'U': draw_letter_U,
    'W': draw_letter_W, 'I': draw_letter_I, 'N': draw_letter_N,
    'L': draw_letter_L, '!': draw_exclamation, ' ': draw_space
}

# --- Async mark draw ---
def async_draw_mark(player, cell):
    t = threading.Thread(target=draw_mark, args=(player, cell))
    t.start()

# --- Routes ---
@app.route("/start", methods=['POST'])
def start_game():
    global board, current_turn, game_over, winner
    board = {i: ' ' for i in range(1, 10)}
    current_turn = 'X'
    game_over = False
    winner = None
    motors_on()
    time.sleep(1)
    draw_grid()
    return jsonify({"message": "New game started."})

@app.route("/move", methods=['POST'])
def make_move():
    global current_turn, game_over, winner
    if game_over:
        return jsonify({"error": "Game over."}), 400

    data = request.get_json()
    move = data.get('move')

    if not (1 <= move <= 9) or board[move] != ' ':
        return jsonify({"error": "Invalid move."}), 400

    board[move] = current_turn
    async_draw_mark(current_turn, move)
    winner, winning_line = check_winner()

    if winner:
        game_over = True
        time.sleep(0.5)
        if winning_line:
            draw_winning_line(winning_line)
        motors_off()
        return jsonify({"winner": winner, "board": board})

    # Don't make AI move immediately - let frontend handle the delay
    # Just return the current state after player's move
    return jsonify({
        "board": board,
        "current_turn": "O",  # AI's turn next
        "winner": winner
    })

@app.route("/ai-move", methods=['POST'])
def ai_move_endpoint():
    """Separate endpoint for AI to make its move after delay"""
    global current_turn, game_over, winner
    
    if game_over:
        return jsonify({"error": "Game over."}), 400

    # AI move
    ai = ai_move()
    if ai:
        board[ai] = 'O'
        # Draw the AI move synchronously (wait for it to complete)
        draw_mark('O', ai)
        winner, winning_line = check_winner()
        if winner:
            game_over = True
            time.sleep(0.5)
            if winning_line:
                draw_winning_line(winning_line)
            motors_off()

    return jsonify({
        "board": board,
        "current_turn": "X",  # Player's turn next
        "winner": winner
    })

@app.route("/state", methods=['GET'])
def state():
    return jsonify({
        "board": board,
        "current_turn": current_turn,
        "game_over": game_over,
        "winner": winner
    })

@app.route("/draw-rectangle", methods=['POST'])
def draw_rectangle():
    # Rectangle bounds
    left = grid_origin[0] + 3 * cell_size + 3  # 3 units away from grid
    right = 120
    top = 5
    bottom = 120
    if left >= right:
        return jsonify({"error": "Not enough space for rectangle."}), 400

    motors_on()
    time.sleep(0.2)
    pen_up()
    # Outer rectangle
    go(left, top)
    pen_down()
    go(right, top)
    go(right, bottom)
    go(left, bottom)
    go(left, top)
    pen_up()
    # Inner rectangle (1 unit in)
    go(left + 1, top + 1)
    pen_down()
    go(right - 1, top + 1)
    go(right - 1, bottom - 1)
    go(left + 1, bottom - 1)
    go(left + 1, top + 1)
    pen_up()
    go(grid_origin[0] + 3 * cell_size + 10, grid_origin[1] + 3 * cell_size + 10)  # Resting position
    motors_off()
    return jsonify({"message": "Rectangle drawn."})

@app.route("/draw-pixel-square", methods=['POST'])
def draw_pixel_square():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    w = data.get('w')
    h = data.get('h')
    fill = data.get('fill', False)
    if x is None or y is None or w is None or h is None:
        return jsonify({"error": "Missing parameters."}), 400
    if not fill:
        return jsonify({"message": "Blank square, nothing drawn."})
    motors_on()
    time.sleep(0.1)
    pen_up()
    go(x, y)
    pen_down()
    go(x + w, y)
    go(x + w, y + h)
    go(x, y + h)
    go(x, y)
    pen_up()
    go(grid_origin[0] + 3 * cell_size + 10, grid_origin[1] + 3 * cell_size + 10)  # Resting position
    motors_off()
    return jsonify({"message": "Square drawn."})

@app.route("/draw-pixel-art-square", methods=['POST'])
def draw_pixel_art_square():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    pattern = data.get('pattern')
    if x is None or y is None or pattern is None:
        return jsonify({"error": "Missing parameters."}), 400
    if not (isinstance(pattern, list) and len(pattern) == 5 and all(isinstance(row, list) and len(row) == 6 for row in pattern)):
        return jsonify({"error": "Pattern must be a 5x6 array."}), 400
    # Mosaic region offset
    margin = 5
    left = max(grid_origin[0] + 3 * cell_size + margin, margin)
    top = 5
    motors_on()
    time.sleep(0.1)
    pen_up()
    for row in range(5):
        for col in range(6):
            if pattern[row][col]:
                # Rotate 90 degrees: (row, col) -> (col, 4-row)
                px = left + x + col
                py = top + y + (4 - row)
                for pass_num in range(2):  # Draw each square twice
                    print(f"Drawing square at ({px}, {py}), pass {pass_num+1}, pen_down")
                    go(px, py)
                    pen_down()
                    time.sleep(0.3)
                    go(px + 1, py)
                    print(f"  Line to ({px+1}, {py})")
                    time.sleep(0.3)
                    go(px + 1, py + 1)
                    print(f"  Line to ({px+1}, {py+1})")
                    time.sleep(0.3)
                    go(px, py + 1)
                    print(f"  Line to ({px}, {py+1})")
                    time.sleep(0.3)
                    go(px, py)
                    print(f"  Line to ({px}, {py})")
                    time.sleep(0.3)
                    if pass_num == 1:
                        pen_up()
                        print(f"Pen up after second pass at ({px}, {py})")
                        time.sleep(0.3)  # Only lift pen after second pass
    go(grid_origin[0] + 3 * cell_size + 10, grid_origin[1] + 3 * cell_size + 10)  # Resting position
    print("Resting position reached, pen up.")
    motors_off()
    return jsonify({"message": "Pixel art square drawn."})

@app.route("/draw-large-area-rectangle", methods=['POST'])
def draw_large_area_rectangle():
    margin = 5
    left = max(grid_origin[0] + 3 * cell_size + margin, margin)  # 70
    right = 125 - margin  # 120
    width = right - left  # 50
    top = margin  # 5
    bottom = top + 108  # 113
    if bottom > 125 - margin:
        bottom = 120
        top = bottom - 108
    motors_on()
    time.sleep(0.2)
    pen_up()
    go(left, top)
    pen_down()
    go(right, top)
    go(right, bottom)
    go(left, bottom)
    go(left, top)
    pen_up()
    go(grid_origin[0] + 3 * cell_size + 10, grid_origin[1] + 3 * cell_size + 10)  # Resting position
    motors_off()
    return jsonify({"message": f"Large area rectangle drawn at ({left}, {top}) to ({right}, {bottom})"})

if __name__ == "__main__":
    motors_on()
    pen_up()  # Raise the pen at startup
    time.sleep(0.5)
    app.run(debug=True, use_reloader=False) 