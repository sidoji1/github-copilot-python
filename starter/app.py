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

if __name__ == '__main__':
    app.run(debug=True)