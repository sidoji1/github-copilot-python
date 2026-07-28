import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request

import sudoku_logic

Board = List[List[int]]
GameState = Dict[str, Optional[Board]]

app = Flask(__name__)

CURRENT: GameState = {
    'puzzle': None,
    'solution': None,
    'solved': False,
}

LEADERBOARD_FILE = Path(__file__).resolve().parent / 'leaderboard.json'
LEADERBOARD_LIMIT = 10


def get_requested_clues() -> int:
    """Return the clue count for a new puzzle based on the requested difficulty."""
    return sudoku_logic.get_clues_for_difficulty(request.args.get('difficulty'))


def find_incorrect_cells(board: Board, solution: Board) -> List[List[int]]:
    """Return coordinates of board cells that differ from the solution."""
    return [
        [row, col]
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if board[row][col] != solution[row][col]
    ]


def find_hint(board: Board, solution: Board) -> Optional[dict[str, int]]:
    """Return one hint for the first empty cell using the stored solution."""
    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            if board[row][col] == sudoku_logic.EMPTY:
                return {'row': row, 'col': col, 'value': solution[row][col]}
    return None


def normalize_elapsed_seconds(value: Any) -> int:
    """Convert a client-supplied elapsed time value into a non-negative integer."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0


def load_leaderboard() -> List[Dict[str, Any]]:
    """Load leaderboard entries from the local JSON file if it exists."""
    if not LEADERBOARD_FILE.exists():
        return []
    try:
        with LEADERBOARD_FILE.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(data, list):
        return []

    valid_entries: List[Dict[str, Any]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        elapsed_seconds = entry.get('elapsed_seconds')
        completed_at = entry.get('completed_at')
        if isinstance(elapsed_seconds, (int, float)) and not isinstance(elapsed_seconds, bool):
            valid_entries.append({
                'elapsed_seconds': int(elapsed_seconds),
                'completed_at': completed_at if isinstance(completed_at, str) else '',
            })
    return valid_entries


def save_leaderboard(entries: List[Dict[str, Any]]) -> None:
    """Persist the leaderboard entries to disk."""
    LEADERBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LEADERBOARD_FILE.open('w', encoding='utf-8') as handle:
        json.dump(entries, handle, indent=2)


def record_leaderboard_entry(elapsed_seconds: int) -> List[Dict[str, Any]]:
    """Append a new completion entry and keep only the fastest ten results."""
    entries = load_leaderboard()
    entries.append({
        'elapsed_seconds': elapsed_seconds,
        'completed_at': datetime.now(timezone.utc).isoformat(),
    })
    sorted_entries = sorted(entries, key=lambda item: (item['elapsed_seconds'], item['completed_at']))
    trimmed_entries = sorted_entries[:LEADERBOARD_LIMIT]
    save_leaderboard(trimmed_entries)
    return trimmed_entries


@app.route('/')
def index() -> str:
    """Render the main Sudoku game page."""
    return render_template('index.html')


@app.route('/new')
def new_game() -> 'flask.wrappers.Response':
    """Generate a new Sudoku puzzle and store its solution."""
    clues = get_requested_clues()
    puzzle, solution = sudoku_logic.generate_puzzle(clues)
    CURRENT['puzzle'] = puzzle
    CURRENT['solution'] = solution
    CURRENT['solved'] = False
    return jsonify({'puzzle': puzzle})


@app.route('/check', methods=['POST'])
def check_solution() -> 'flask.wrappers.Response':
    """Check the posted board against the current solution and record a win if solved."""
    data = request.json or {}
    board = data.get('board')
    solution = CURRENT.get('solution')
    if solution is None:
        return jsonify({'error': 'No game in progress'}), 400

    incorrect = find_incorrect_cells(board, solution)
    if not incorrect:
        elapsed_seconds = normalize_elapsed_seconds(data.get('elapsed_time_seconds'))
        if not CURRENT.get('solved', False):
            CURRENT['solved'] = True
            leaderboard = record_leaderboard_entry(elapsed_seconds)
            completed_at = leaderboard[-1]['completed_at'] if leaderboard else ''
            return jsonify({'incorrect': incorrect, 'completed': True, 'completed_at': completed_at, 'elapsed_seconds': elapsed_seconds})
        return jsonify({'incorrect': incorrect, 'completed': True})

    return jsonify({'incorrect': incorrect})


@app.route('/hint', methods=['POST'])
def get_hint() -> 'flask.wrappers.Response':
    """Return one solution value for a currently empty cell."""
    data = request.json or {}
    board = data.get('board')
    solution = CURRENT.get('solution')
    if solution is None:
        return jsonify({'error': 'No game in progress'}), 400
    if not isinstance(board, list):
        return jsonify({'error': 'Board data is required'}), 400

    hint = find_hint(board, solution)
    if hint is None:
        return jsonify({'error': 'No empty cells remaining'}), 400
    return jsonify(hint)


@app.route('/leaderboard')
def leaderboard() -> 'flask.wrappers.Response':
    """Return the current leaderboard sorted from fastest to slowest."""
    return jsonify(load_leaderboard())


if __name__ == '__main__':
    app.run(debug=True)