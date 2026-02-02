import uuid
from datetime import datetime
from flask import Flask, request, jsonify


# --- Kernlogik: TicTacToe-Klasse ---
class TicTacToe:
    def __init__(self):
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.game_over = False
        self.winner = None
        self.move_count = 0

    def available_moves(self):
        return [(r, c) for r in range(3) for c in range(3) if self.board[r][c] == ' ']

    def make_move(self, row, col):
        if self.game_over:
            return {'success': False, 'message': 'Game is already over!'}
        if not (0 <= row < 3 and 0 <= col < 3) or self.board[row][col] != ' ':
            return {'success': False, 'message': 'Invalid move! Cell is occupied or out of bounds'}
        self.board[row][col] = self.current_player
        self.move_count += 1
        if self.check_winner(row, col):
            self.game_over = True
            self.winner = self.current_player
            return {'success': True, 'message': f'Player {self.current_player} wins!', 'game_over': True, 'winner': self.current_player}
        if self.move_count == 9:
            self.game_over = True
            return {'success': True, 'message': 'Draw!', 'game_over': True, 'winner': None}
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        return {'success': True, 'message': f'Move successful! Next player: {self.current_player}', 'game_over': False, 'winner': None}

    def check_winner(self, row, col):
        b, p = self.board, self.current_player
        return (
            all(b[row][c] == p for c in range(3)) or
            all(b[r][col] == p for r in range(3)) or
            (row == col and all(b[i][i] == p for i in range(3))) or
            (row + col == 2 and all(b[i][2 - i] == p for i in range(3)))
        )

    def serialize(self):
        return {
            'board': self.board,
            'current_player': self.current_player,
            'game_over': self.game_over,
            'winner': self.winner,
            'move_count': self.move_count,
            'available_moves': self.available_moves(),
            'board_string': self.pretty_board()
        }

    def pretty_board(self):
        lines = ["  0   1   2"]
        for r in range(3):
            row = f"{r} " + " | ".join(self.board[r])
            lines.append(row)
            if r < 2:
                lines.append("  ---|---|---")
        return "\n".join(lines)

# --- Sitzungsmanagement ---
class SessionManager:
    def __init__(self):
        self.sessions = {}

    def new_session(self):
        sid = str(uuid.uuid4())
        self.sessions[sid] = {
            'game': TicTacToe(),
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'player_count': 0
            }
        }
        return sid

    def get_game(self, sid):
        session = self.sessions.get(sid)
        if session:
            session['metadata']['last_accessed'] = datetime.now().isoformat()
            return session['game']
        return None

    def list_sessions(self):
        return {
            sid: {
                'game_over': s['game'].game_over,
                'current_player': s['game'].current_player,
                'move_count': s['game'].move_count,
                'winner': s['game'].winner,
                'metadata': s['metadata']
            }
            for sid, s in self.sessions.items()
        }

# --- Flask API ---
app = Flask(__name__)
manager = SessionManager()

@app.route('/new_game', methods=['POST'])
def new_game():
    sid = manager.new_session()
    game = manager.get_game(sid)
    return jsonify({
        'success': True,
        'data': {
            'session_id': sid,
            'message': 'New game created successfully',
            'game_state': game.serialize(),
            'metadata': manager.sessions[sid]['metadata']
        }
    })

@app.route('/get_state', methods=['GET'])
def get_state():
    sid = request.args.get('session_id')
    game = manager.get_game(sid)
    if not game:
        return jsonify({'success': False, 'message': 'Invalid session_id'}), 404
    return jsonify({
        'success': True,
        'data': {
            'session_id': sid,
            'game_state': game.serialize(),
            'metadata': manager.sessions[sid]['metadata']
        }
    })

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.json
    sid = data.get('session_id')
    row, col = data.get('row'), data.get('col')
    game = manager.get_game(sid)
    if not game:
        return jsonify({'success': False, 'message': 'Invalid session_id'}), 404
    result = game.make_move(row, col)
    return jsonify({
        'success': True,
        'data': {
            'session_id': sid,
            'move_result': result,
            'game_state': game.serialize()
        }
    })

@app.route('/list_sessions', methods=['GET'])
def list_sessions():
    return jsonify({
        'success': True,
        'data': {
            'total_sessions': len(manager.sessions),
            'sessions': manager.list_sessions()
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
