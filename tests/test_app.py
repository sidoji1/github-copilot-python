import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = REPO_ROOT / "starter"
if str(STARTER_DIR) not in sys.path:
    sys.path.insert(0, str(STARTER_DIR))

import sudoku_logic


def test_flask_app_loads():
    """Verify the Flask app can be imported successfully."""
    app_module = importlib.import_module("app")
    assert app_module.app is not None


def test_new_game_defaults_to_medium_difficulty(monkeypatch):
    """Verify a new game uses the medium difficulty when none is requested."""
    app_module = importlib.import_module("app")
    captured = {}

    def fake_generate_puzzle(clues):
        captured['clues'] = clues
        return [[0] * 9 for _ in range(9)], [[1] * 9 for _ in range(9)]

    monkeypatch.setattr(app_module.sudoku_logic, "generate_puzzle", fake_generate_puzzle)
    client = app_module.app.test_client()

    response = client.get('/new')

    assert response.status_code == 200
    assert captured['clues'] == app_module.sudoku_logic.DIFFICULTY_SETTINGS['medium']


def test_new_game_uses_requested_difficulty(monkeypatch):
    """Verify a requested difficulty maps to the expected clue count."""
    app_module = importlib.import_module("app")
    captured = {}

    def fake_generate_puzzle(clues):
        captured['clues'] = clues
        return [[0] * 9 for _ in range(9)], [[1] * 9 for _ in range(9)]

    monkeypatch.setattr(app_module.sudoku_logic, "generate_puzzle", fake_generate_puzzle)
    client = app_module.app.test_client()

    response = client.get('/new?difficulty=hard')

    assert response.status_code == 200
    assert captured['clues'] == app_module.sudoku_logic.DIFFICULTY_SETTINGS['hard']


def test_generated_puzzles_have_unique_solution():
    """Verify generated puzzles have exactly one valid solution."""
    puzzle, _ = sudoku_logic.generate_puzzle(clues=sudoku_logic.DIFFICULTY_SETTINGS['medium'])

    solution_count = sudoku_logic.count_solutions(puzzle)

    assert solution_count == 1


def test_hint_endpoint_returns_one_value_from_the_stored_solution():
    """Verify the hint endpoint reveals one value from the stored solution."""
    app_module = importlib.import_module("app")
    app_module.CURRENT['solution'] = [[1 + (row * 3 + col) % 9 for col in range(9)] for row in range(9)]
    app_module.CURRENT['puzzle'] = [[0] * 9 for _ in range(9)]

    client = app_module.app.test_client()
    response = client.post('/hint', json={'board': [[0] * 9 for _ in range(9)]})

    assert response.status_code == 200
    assert response.get_json() == {'row': 0, 'col': 0, 'value': 1}


def test_hint_endpoint_skips_player_filled_cells():
    """Verify the hint endpoint chooses an empty cell instead of a player-filled one."""
    app_module = importlib.import_module("app")
    app_module.CURRENT['solution'] = [[1 + (row * 3 + col) % 9 for col in range(9)] for row in range(9)]
    app_module.CURRENT['puzzle'] = [[0] * 9 for _ in range(9)]

    client = app_module.app.test_client()
    board = [[0] * 9 for _ in range(9)]
    board[0][0] = 5
    response = client.post('/hint', json={'board': board})

    assert response.status_code == 200
    assert response.get_json() == {'row': 0, 'col': 1, 'value': 2}


def test_check_endpoint_records_completion_time_and_persists(monkeypatch, tmp_path):
    """Verify a solved board records a leaderboard entry and persists it."""
    app_module = importlib.import_module("app")
    leaderboard_path = tmp_path / "leaderboard.json"
    app_module.LEADERBOARD_FILE = leaderboard_path
    app_module.CURRENT['solution'] = [[1 + (row * 3 + col) % 9 for col in range(9)] for row in range(9)]
    app_module.CURRENT['puzzle'] = [[0] * 9 for _ in range(9)]

    client = app_module.app.test_client()
    solved_board = [[1 + (row * 3 + col) % 9 for col in range(9)] for row in range(9)]
    response = client.post('/check', json={'board': solved_board, 'elapsed_time_seconds': 45})

    assert response.status_code == 200
    assert response.get_json()['completed'] is True
    assert leaderboard_path.exists()

    reloaded_module = importlib.reload(app_module)
    reloaded_module.LEADERBOARD_FILE = leaderboard_path
    leaderboard_response = reloaded_module.app.test_client().get('/leaderboard')

    assert leaderboard_response.status_code == 200
    assert leaderboard_response.get_json() == [{'elapsed_seconds': 45, 'completed_at': response.get_json()['completed_at']}]


def test_check_endpoint_keeps_only_the_top_ten_fastest_times(monkeypatch, tmp_path):
    """Verify the leaderboard keeps only the fastest ten completion entries."""
    app_module = importlib.import_module("app")
    leaderboard_path = tmp_path / "leaderboard.json"
    app_module.LEADERBOARD_FILE = leaderboard_path
    app_module.CURRENT['solution'] = [[1 + (row * 3 + col) % 9 for col in range(9)] for row in range(9)]
    app_module.CURRENT['puzzle'] = [[0] * 9 for _ in range(9)]

    client = app_module.app.test_client()
    solved_board = [[1 + (row * 3 + col) % 9 for col in range(9)] for row in range(9)]
    for elapsed_seconds in range(100, 111):
        app_module.CURRENT['solved'] = False
        client.post('/check', json={'board': solved_board, 'elapsed_time_seconds': elapsed_seconds})

    leaderboard_response = client.get('/leaderboard')
    leaderboard = leaderboard_response.get_json()

    assert leaderboard_response.status_code == 200
    assert len(leaderboard) == 10
    assert [entry['elapsed_seconds'] for entry in leaderboard] == list(range(100, 110))


def test_check_endpoint_preserves_existing_incorrect_cell_reporting():
    """Verify the existing /check behavior remains intact for incomplete boards."""
    app_module = importlib.import_module("app")
    app_module.CURRENT['solution'] = [[1 + (row * 3 + col) % 9 for col in range(9)] for row in range(9)]
    app_module.CURRENT['puzzle'] = [[0] * 9 for _ in range(9)]

    client = app_module.app.test_client()
    board = [[0] * 9 for _ in range(9)]
    board[0][0] = 5
    response = client.post('/check', json={'board': board, 'elapsed_time_seconds': 30})

    assert response.status_code == 200
    assert response.get_json()['incorrect']
    assert 'completed' not in response.get_json()
