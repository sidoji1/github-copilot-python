import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = REPO_ROOT / "starter"
if str(STARTER_DIR) not in sys.path:
    sys.path.insert(0, str(STARTER_DIR))


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
