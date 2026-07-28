// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const THEME_STORAGE_KEY = 'sudoku-theme';
let puzzle = [];
let elapsedSeconds = 0;
let timerInterval = null;

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function updateTimerDisplay() {
  const timerElement = document.getElementById('game-timer');
  if (timerElement) {
    timerElement.textContent = formatTime(elapsedSeconds);
  }
}

function startTimer() {
  // Ensure only one timer interval is active at a time.
  clearInterval(timerInterval);
  elapsedSeconds = 0;
  updateTimerDisplay();
  timerInterval = window.setInterval(() => {
    elapsedSeconds += 1;
    updateTimerDisplay();
  }, 1000);
}

function stopTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const toggleButton = document.getElementById('theme-toggle');
  if (toggleButton) {
    toggleButton.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    toggleButton.setAttribute('aria-pressed', String(theme === 'dark'));
  }
  localStorage.setItem(THEME_STORAGE_KEY, theme);
}

function initializeTheme() {
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = savedTheme === 'dark' || savedTheme === 'light'
    ? savedTheme
    : (prefersDark ? 'dark' : 'light');
  applyTheme(theme);
}

function clearBoardHighlights() {
  const boardDiv = document.getElementById('sudoku-board');
  if (!boardDiv) {
    return;
  }

  const inputs = boardDiv.getElementsByTagName('input');
  for (let idx = 0; idx < inputs.length; idx++) {
    inputs[idx].classList.remove('invalid', 'incorrect');
  }
}

function getCellIndicesForRowCol(row, col) {
  return row * SIZE + col;
}

function getPeerIndices(row, col) {
  const indices = new Set();

  for (let currentCol = 0; currentCol < SIZE; currentCol++) {
    if (currentCol !== col) {
      indices.add(getCellIndicesForRowCol(row, currentCol));
    }
  }

  for (let currentRow = 0; currentRow < SIZE; currentRow++) {
    if (currentRow !== row) {
      indices.add(getCellIndicesForRowCol(currentRow, col));
    }
  }

  const startRow = Math.floor(row / 3) * 3;
  const startCol = Math.floor(col / 3) * 3;
  for (let currentRow = startRow; currentRow < startRow + 3; currentRow++) {
    for (let currentCol = startCol; currentCol < startCol + 3; currentCol++) {
      if (currentRow !== row || currentCol !== col) {
        indices.add(getCellIndicesForRowCol(currentRow, currentCol));
      }
    }
  }

  return Array.from(indices);
}

function updateInvalidHighlights() {
  const boardDiv = document.getElementById('sudoku-board');
  if (!boardDiv) {
    return;
  }

  const inputs = Array.from(boardDiv.getElementsByTagName('input'));
  clearBoardHighlights();

  const board = [];
  for (let row = 0; row < SIZE; row++) {
    board[row] = [];
    for (let col = 0; col < SIZE; col++) {
      const idx = getCellIndicesForRowCol(row, col);
      const value = inputs[idx].value ? parseInt(inputs[idx].value, 10) : 0;
      board[row][col] = value;
    }
  }

  const highlightedIndices = new Set();
  inputs.forEach((input, idx) => {
    if (input.disabled) {
      return;
    }

    const row = Math.floor(idx / SIZE);
    const col = idx % SIZE;
    const value = board[row][col];
    if (!value) {
      return;
    }

    for (const peerIndex of getPeerIndices(row, col)) {
      const peerRow = Math.floor(peerIndex / SIZE);
      const peerCol = peerIndex % SIZE;
      const peerValue = board[peerRow][peerCol];
      if (peerValue === value && peerIndex !== idx) {
        highlightedIndices.add(idx);
        if (!inputs[peerIndex].disabled) {
          highlightedIndices.add(peerIndex);
        }
      }
    }
  });

  highlightedIndices.forEach((idx) => {
    inputs[idx].classList.add('invalid');
  });
}

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      input.addEventListener('input', (e) => {
        if (e.target.disabled) {
          e.target.value = '';
          return;
        }

        const val = e.target.value.replace(/[^1-9]/g, '');
        e.target.value = val;
        updateInvalidHighlights();
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      inp.classList.remove('prefilled', 'invalid', 'incorrect');
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.classList.add('prefilled');
      } else {
        inp.value = '';
        inp.disabled = false;
      }
    }
  }

  clearBoardHighlights();
}

function renderLeaderboard(entries) {
  const leaderboardList = document.getElementById('leaderboard-list');
  if (!leaderboardList) {
    return;
  }

  leaderboardList.innerHTML = '';
  if (!entries.length) {
    const emptyItem = document.createElement('li');
    emptyItem.className = 'leaderboard-empty';
    emptyItem.textContent = 'No completed games yet.';
    leaderboardList.appendChild(emptyItem);
    return;
  }

  entries.forEach((entry, index) => {
    const item = document.createElement('li');
    item.className = 'leaderboard-item';
    item.textContent = `#${index + 1} ${entry.elapsed_seconds}s — ${entry.completed_at}`;
    leaderboardList.appendChild(item);
  });
}

async function loadLeaderboard() {
  const res = await fetch('/leaderboard');
  const entries = await res.json();
  renderLeaderboard(entries);
}

async function newGame() {
  const difficultySelect = document.getElementById('difficulty-select');
  const difficulty = difficultySelect ? difficultySelect.value : 'medium';
  startTimer();
  const res = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
  const data = await res.json();
  renderPuzzle(data.puzzle);
  document.getElementById('message').innerText = '';
  await loadLeaderboard();
}

async function checkSolution() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = inputs[idx].value;
      board[i][j] = val ? parseInt(val, 10) : 0;
    }
  }
  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board, elapsed_time_seconds: elapsedSeconds})
  });
  const data = await res.json();
  const msg = document.getElementById('message');
  if (data.error) {
    msg.style.color = '#d32f2f';
    msg.innerText = data.error;
    return;
  }
  const incorrect = new Set(data.incorrect.map(x => x[0]*SIZE + x[1]));
  for (let idx = 0; idx < inputs.length; idx++) {
    const inp = inputs[idx];
    if (inp.disabled) continue;
    inp.classList.remove('incorrect');
    if (incorrect.has(idx)) {
      inp.classList.add('incorrect');
    }
  }
  if (data.completed) {
    stopTimer();
    await loadLeaderboard();
    msg.style.color = '#388e3c';
    msg.innerText = 'Congratulations! You solved it!';
  } else {
    msg.style.color = '#d32f2f';
    msg.innerText = 'Some cells are incorrect.';
  }
}

async function getHint() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = inputs[idx].value;
      board[i][j] = val ? parseInt(val, 10) : 0;
    }
  }

  const res = await fetch('/hint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board})
  });
  const data = await res.json();
  const msg = document.getElementById('message');

  if (data.error) {
    msg.style.color = '#d32f2f';
    msg.innerText = data.error;
    return;
  }

  const idx = data.row * SIZE + data.col;
  const inp = inputs[idx];
  if (!inp) {
    return;
  }

  if (inp.value === '') {
    // Treat hinted cells as permanently locked, matching the existing prefilled-cell behavior.
    inp.value = data.value;
    inp.disabled = true;
    inp.classList.add('prefilled');
    inp.classList.remove('invalid', 'incorrect');
    clearBoardHighlights();
    msg.style.color = '#388e3c';
    msg.innerText = 'Hint applied.';
  } else {
    msg.style.color = '#d32f2f';
    msg.innerText = 'That cell is already filled.';
  }
}

// Wire buttons
window.addEventListener('load', () => {
  initializeTheme();

  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(currentTheme);
    });
  }

  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('hint').addEventListener('click', getHint);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  // initialize
  newGame();
});