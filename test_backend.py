from flask import Flask, request, jsonify
import time
import threading
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Simulated game state ---
board = {i: ' ' for i in range(1, 10)}
current_turn = 'X'
game_over = False
winner = None

# --- Simulated drawing functions ---
def simulate_drawing_delay():
    """Simulate the time it takes for the Blot to draw"""
    time.sleep(0.5)

def draw_grid():
    """Simulate drawing the grid"""
    print("🖊️  Drawing grid...")
    simulate_drawing_delay()
    print("✅ Grid drawn")

def draw_mark(player, cell):
    """Simulate drawing an X or O"""
    print(f"🖊️  Drawing {player} in cell {cell}...")
    simulate_drawing_delay()
    print(f"✅ {player} drawn in cell {cell}")

def draw_winning_line(winning_cells):
    """Simulate drawing the winning line"""
    print(f"🏆 Drawing winning line through cells {winning_cells}...")
    simulate_drawing_delay()
    print("✅ Winning line drawn")

def go_to_corner():
    """Simulate moving to corner after each move"""
    print("📍 Moving to corner...")
    time.sleep(0.2)
    print("✅ At corner")

# --- Game logic functions ---
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

def async_draw_mark(player, cell):
    """Simulate async drawing (non-blocking)"""
    t = threading.Thread(target=draw_mark, args=(player, cell))
    t.start()

# --- Routes ---
@app.route("/start", methods=['POST'])
def start_game():
    global board, current_turn, game_over, winner
    print("🎮 Starting new game...")
    
    board = {i: ' ' for i in range(1, 10)}
    current_turn = 'X'
    game_over = False
    winner = None
    
    # Simulate drawing the grid
    draw_grid()
    go_to_corner()
    
    print("✅ New game started")
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

    print(f"🎯 Player {current_turn} makes move at cell {move}")
    
    board[move] = current_turn
    async_draw_mark(current_turn, move)
    winner, winning_line = check_winner()

    if winner:
        game_over = True
        time.sleep(0.5)
        if winning_line:
            draw_winning_line(winning_line)
        go_to_corner()
        print(f"🏆 Game over! Winner: {winner}")
        return jsonify({"winner": winner, "board": board})

    # AI move
    ai = ai_move()
    if ai:
        print(f"🤖 AI makes move at cell {ai}")
        board[ai] = 'O'
        async_draw_mark('O', ai)
        winner, winning_line = check_winner()
        if winner:
            game_over = True
            time.sleep(0.5)
            if winning_line:
                draw_winning_line(winning_line)
            go_to_corner()
            print(f"🏆 Game over! Winner: {winner}")

    return jsonify({
        "board": board,
        "current_turn": current_turn,
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

@app.route("/health", methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Test backend is running"})

if __name__ == "__main__":
    print("🚀 Starting Test Backend Server...")
    print("📝 This is a simulation - no physical Blot hardware will be used")
    print("🌐 Server will be available at http://localhost:5000")
    print("🔗 Frontend can connect to test the game logic")
    print("-" * 50)
    app.run(debug=True, use_reloader=False, port=5000) 