from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template, request

import sudoku_logic

Board = List[List[int]]
GameState = Dict[str, Optional[Board]]

app = Flask(__name__)

CURRENT: GameState = {
    'puzzle': None,
    'solution': None,
}

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
    return jsonify({'puzzle': puzzle})


@app.route('/check', methods=['POST'])
def check_solution() -> 'flask.wrappers.Response':
    """Check the posted board against the current solution."""
    data = request.json or {}
    board = data.get('board')
    solution = CURRENT.get('solution')
    if solution is None:
        return jsonify({'error': 'No game in progress'}), 400
    incorrect = find_incorrect_cells(board, solution)
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


if __name__ == '__main__':
    app.run(debug=True)