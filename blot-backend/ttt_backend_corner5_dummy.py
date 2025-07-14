from flask import Flask, request, jsonify
import time
import threading
import random
from queue import Queue
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Dummy Blot setup ---
cell_size = 20
# Move the 60x60 grid (3 cells × 20 units) so the top-left corner is at (5, 5)
grid_origin = (5, 5)

board = {i: ' ' for i in range(1, 10)}
current_turn = 'X'
game_over = False
winner = None

# --- Dummy Blot commands ---
def go(x, y):
    print(f"[DUMMY] go({x}, {y})")

def pen_up():
    print("[DUMMY] pen_up()")

def pen_down():
    print("[DUMMY] pen_down()")

def motors_on():
    print("[DUMMY] motors_on()")

def motors_off():
    print("[DUMMY] motors_off()")

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
    if not winning_cells or len(winning_cells) != 3:
        return
    centers = [cell_center(cell) for cell in winning_cells]
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
    for cell in available:
        board_copy = board.copy()
        board_copy[cell] = 'O'
        winner = check_winner_for_board(board_copy)
        if winner == 'O':
            return cell
    for cell in available:
        board_copy = board.copy()
        board_copy[cell] = 'X'
        winner = check_winner_for_board(board_copy)
        if winner == 'X':
            return cell
    return random.choice(available)

def draw_grid():
    motors_on()
    time.sleep(0.1)
    print("[DUMMY] draw_grid()")
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
    go(grid_origin[0] + 3 * cell_size + 10, grid_origin[1] + 3 * cell_size + 10)

# --- Dummy async mark draw ---
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
    time.sleep(0.1)
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
        time.sleep(0.1)
        if winning_line:
            draw_winning_line(winning_line)
        motors_off()
        return jsonify({"winner": winner, "board": board})
    return jsonify({
        "board": board,
        "current_turn": "O",
        "winner": winner
    })

@app.route("/ai-move", methods=['POST'])
def ai_move_endpoint():
    global current_turn, game_over, winner
    if game_over:
        return jsonify({"error": "Game over."}), 400
    ai = ai_move()
    if ai:
        board[ai] = 'O'
        draw_mark('O', ai)
        winner, winning_line = check_winner()
        if winner:
            game_over = True
            time.sleep(0.1)
            if winning_line:
                draw_winning_line(winning_line)
            motors_off()
    return jsonify({
        "board": board,
        "current_turn": "X",
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
    print("[DUMMY] draw_rectangle()")
    time.sleep(0.05)
    return jsonify({"message": "Rectangle drawn."})

@app.route("/draw-pixel-square", methods=['POST'])
def draw_pixel_square():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    w = data.get('w')
    h = data.get('h')
    fill = data.get('fill', False)
    print(f"[DUMMY] draw_pixel_square at ({x},{y}) size ({w},{h}) fill={fill}")
    time.sleep(0.01)
    if x is None or y is None or w is None or h is None:
        return jsonify({"error": "Missing parameters."}), 400
    if not fill:
        return jsonify({"message": "Blank square, nothing drawn."})
    return jsonify({"message": "Square drawn."})

@app.route("/draw-pixel-art-square", methods=['POST'])
def draw_pixel_art_square():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    pattern = data.get('pattern')
    print(f"[DUMMY] draw_pixel_art_square at ({x},{y}) pattern={pattern}")
    time.sleep(0.01)
    if x is None or y is None or pattern is None:
        return jsonify({"error": "Missing parameters."}), 400
    if not (isinstance(pattern, list) and len(pattern) == 5 and all(isinstance(row, list) and len(row) == 6 for row in pattern)):
        return jsonify({"error": "Pattern must be a 5x6 array."}), 400
    return jsonify({"message": "Pixel art square drawn."})

@app.route("/draw-large-area-rectangle", methods=['POST'])
def draw_large_area_rectangle():
    print("[DUMMY] draw_large_area_rectangle()")
    time.sleep(0.05)
    return jsonify({"message": "Large area rectangle drawn (dummy)."})

if __name__ == "__main__":
    print("[DUMMY] Backend running in dummy mode.")
    app.run(debug=True, use_reloader=False) 