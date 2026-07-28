import copy
import random
from typing import List, Optional, Tuple

SIZE = 9
EMPTY = 0
Board = List[List[int]]


def find_next_empty_cell(board: Board) -> Optional[Tuple[int, int]]:
    """Return the next empty cell position in the board, if one exists."""
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                return row, col
    return None


def count_solutions(board: Board) -> int:
    """Return the number of valid Sudoku solutions for the provided board.

    The count stops at two solutions for efficiency, which is sufficient to
    determine whether a puzzle has a unique solution.
    """
    def backtrack(current_board: Board) -> int:
        next_empty_cell = find_next_empty_cell(current_board)
        if next_empty_cell is None:
            return 1

        row, col = next_empty_cell
        total_solutions = 0
        for candidate in random.sample(range(1, SIZE + 1), SIZE):
            if not is_safe(current_board, row, col, candidate):
                continue

            current_board[row][col] = candidate
            total_solutions += backtrack(current_board)
            current_board[row][col] = EMPTY
            if total_solutions >= 2:
                return 2

        return total_solutions

    return backtrack(deep_copy(board))

# Difficulty settings map each level to a target clue count.
# More clues means a easier puzzle because fewer cells are removed.
DIFFICULTY_SETTINGS = {
    'easy': 40,
    'medium': 35,
    'hard': 25,
}
DEFAULT_DIFFICULTY = 'medium'


def deep_copy(board: Board) -> Board:
    """Return a deep copy of the board."""
    return copy.deepcopy(board)


def create_empty_board() -> Board:
    """Create an empty 9x9 Sudoku board."""
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]


def get_subgrid_start(index: int) -> int:
    """Return the starting index for the 3x3 subgrid containing the given position."""
    return index - index % 3


def is_safe(board: Board, row: int, col: int, num: int) -> bool:
    """Return True if placing num at (row, col) is valid on the current board."""
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    start_row = get_subgrid_start(row)
    start_col = get_subgrid_start(col)
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True


def fill_board(board: Board) -> bool:
    """Fill the board with a complete valid Sudoku solution."""
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                for candidate in random.sample(range(1, SIZE + 1), SIZE):
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True


def remove_cells(board: Board, clues: int) -> None:
    """Remove cells from the board while preserving a unique solution."""
    cells_to_remove = SIZE * SIZE - clues
    removed = 0
    positions = [(row, col) for row in range(SIZE) for col in range(SIZE)]
    random.shuffle(positions)

    for row, col in positions:
        if removed >= cells_to_remove:
            break
        if board[row][col] == EMPTY:
            continue

        value = board[row][col]
        board[row][col] = EMPTY
        if count_solutions(board) != 1:
            board[row][col] = value
            continue

        removed += 1


def get_clues_for_difficulty(difficulty: str | None = None) -> int:
    """Return the clue count for the requested difficulty, defaulting to medium."""
    normalized_difficulty = (difficulty or DEFAULT_DIFFICULTY).strip().lower()
    if normalized_difficulty not in DIFFICULTY_SETTINGS:
        normalized_difficulty = DEFAULT_DIFFICULTY
    return DIFFICULTY_SETTINGS[normalized_difficulty]


def generate_puzzle(clues: int = DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY]) -> Tuple[Board, Board]:
    """Generate a Sudoku puzzle and its full solution."""
    board = create_empty_board()
    fill_board(board)
    solution = deep_copy(board)
    remove_cells(board, clues)
    puzzle = deep_copy(board)
    return puzzle, solution
