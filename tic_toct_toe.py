"""
Tic Tac Toe Game - Professional Edition
Features:
  1. Professional UI with themed styling
  2. Main menu navigation
  3. Settings (sound toggle, player names, symbols, colors)
  4. Sound effects (click, place, win, draw)
  5. Winner celebrations with confetti animation
  6. Easy / Medium / Hard AI modes
  7. Game history (saved to JSON)
  8. 2-Player local or 1-Player vs Computer
"""

import json
import math
import os
import random
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# ────────────────────────────── Constants ──────────────────────────────

WINDOW_W, WINDOW_H = 560, 680

BG_DARK = "#1e272e"
BG_PANEL = "#2d3b46"
BG_BOARD = "#3d4f5c"
ACCENT = "#00b894"
ACCENT_HOVER = "#00cec9"
DANGER = "#e17055"
GOLD = "#fdcb6e"
TEXT_LIGHT = "#dfe6e9"
TEXT_DIM = "#b2bec3"
X_COLOR = "#74b9ff"
O_COLOR = "#ffeaa7"
GRID_LINE = "#636e72"

HISTORY_FILE = "tictactoe_history.json"
SETTINGS_FILE = "tictactoe_settings.json"

WIN_LINES = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6],
]

# ────────────────────────────── Sound Manager ──────────────────────────────


class SoundManager:
    """Plays simple beep-based sound effects in a background thread."""

    def __init__(self, enabled=True):
        self.enabled = enabled

    def _beep(self, freq, duration):
        if not self.enabled or not HAS_WINSOUND:
            return
        threading.Thread(
            target=lambda: winsound.Beep(freq, duration), daemon=True
        ).start()

    def click(self):
        self._beep(600, 80)

    def place(self):
        self._beep(800, 100)

    def win(self):
        if not self.enabled or not HAS_WINSOUND:
            return
        notes = [(523, 150), (659, 150), (784, 150), (1047, 250)]

        def play():
            for f, d in notes:
                winsound.Beep(f, d)

        threading.Thread(target=play, daemon=True).start()

    def draw(self):
        self._beep(300, 400)

    def toggle(self, enabled=None):
        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = not self.enabled
        return self.enabled


# ────────────────────────────── AI ──────────────────────────────


class TicTacToeAI:
    """AI opponent with three difficulty levels."""

    @staticmethod
    def get_move(board, ai_symbol, human_symbol, difficulty):
        empty = [i for i, v in enumerate(board) if v == ""]
        if not empty:
            return None
        if difficulty == "Easy":
            return random.choice(empty)
        if difficulty == "Medium":
            move = TicTacToeAI._find_winning_move(board, ai_symbol)
            if move is not None:
                return move
            move = TicTacToeAI._find_winning_move(board, human_symbol)
            if move is not None:
                return move
            if random.random() < 0.55:
                return TicTacToeAI._minimax_move(board, ai_symbol, human_symbol)
            return random.choice(empty)
        return TicTacToeAI._minimax_move(board, ai_symbol, human_symbol)

    @staticmethod
    def _find_winning_move(board, symbol):
        for line in WIN_LINES:
            vals = [board[i] for i in line]
            if vals.count(symbol) == 2 and vals.count("") == 1:
                return line[vals.index("")]
        return None

    @staticmethod
    def _minimax_move(board, ai, human):
        best_score, best_move = -math.inf, None
        for i in range(9):
            if board[i] == "":
                board[i] = ai
                score = TicTacToeAI._minimax(board, 0, False, ai, human)
                board[i] = ""
                if score > best_score:
                    best_score, best_move = score, i
        return best_move

    @staticmethod
    def _minimax(board, depth, is_max, ai, human):
        winner = TicTacToeAI._check_winner(board)
        if winner == ai:
            return 10 - depth
        if winner == human:
            return depth - 10
        if "" not in board:
            return 0
        if is_max:
            best = -math.inf
            for i in range(9):
                if board[i] == "":
                    board[i] = ai
                    best = max(best, TicTacToeAI._minimax(board, depth + 1, False, ai, human))
                    board[i] = ""
            return best
        best = math.inf
        for i in range(9):
            if board[i] == "":
                board[i] = human
                best = min(best, TicTacToeAI._minimax(board, depth + 1, True, ai, human))
                board[i] = ""
        return best

    @staticmethod
    def _check_winner(board):
        for line in WIN_LINES:
            a, b, c = line
            if board[a] and board[a] == board[b] == board[c]:
                return board[a]
        return None


# ────────────────────────────── History ──────────────────────────────


class HistoryManager:
    """Persists game results to a JSON file."""

    def __init__(self, filepath=HISTORY_FILE):
        self.filepath = filepath
        self.history = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save(self):
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.history, f, indent=2)
        except IOError:
            pass

    def add(self, record):
        self.history.append(record)
        if len(self.history) > 100:
            self.history = self.history[-100:]
        self.save()

    def clear(self):
        self.history = []
        self.save()


# ────────────────────────────── Settings Store ──────────────────────────────


class SettingsStore:
    """Persists user settings to a JSON file."""

    DEFAULTS = {
        "sound_enabled": True,
        "player1_name": "Player 1",
        "player2_name": "Player 2",
        "player1_symbol": "X",
        "win_score": 5,
    }

    def __init__(self, filepath=SETTINGS_FILE):
        self.filepath = filepath
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    saved = json.load(f)
                    merged = dict(self.DEFAULTS)
                    merged.update(saved)
                    return merged
            except (json.JSONDecodeError, IOError):
                pass
        return dict(self.DEFAULTS)

    def save(self):
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.data, f, indent=2)
        except IOError:
            pass

    def get(self, key):
        return self.data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self.data[key] = value
        self.save()


# ────────────────────────────── Confetti Canvas ──────────────────────────────


class Confetti:
    """Animated confetti celebration on a canvas overlay."""

    COLORS = ["#e17055", "#00b894", "#74b9ff", "#fdcb6e", "#ffeaa7",
              "#a29bfe", "#fab1a0", "#55efc4", "#74b9ff", "#ff7675"]

    def __init__(self, canvas, w, h, duration=4.0):
        self.canvas = canvas
        self.w = w
        self.h = h
        self.duration = duration
        self.particles = []
        self.running = False
        self.start_time = 0

    def start(self):
        self.particles = []
        for _ in range(120):
            self.particles.append({
                "x": self.w / 2 + random.uniform(-60, 60),
                "y": self.h / 2,
                "vx": random.uniform(-6, 6),
                "vy": random.uniform(-12, -4),
                "color": random.choice(self.COLORS),
                "size": random.uniform(4, 9),
                "rot": random.uniform(0, 360),
                "vr": random.uniform(-10, 10),
                "shape": random.choice(["rect", "oval"]),
            })
        self.running = True
        self.start_time = time.time()
        self._animate()

    def _animate(self):
        if not self.running:
            return
        elapsed = time.time() - self.start_time
        self.canvas.delete("confetti")
        if elapsed > self.duration:
            self.running = False
            self.canvas.delete("confetti")
            return
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.35
            p["rot"] += p["vr"]
            if p["y"] > self.h + 20:
                continue
            x, y = p["x"], p["y"]
            s = p["size"]
            if p["shape"] == "rect":
                self.canvas.create_rectangle(
                    x - s, y - s, x + s, y + s,
                    fill=p["color"], outline="", tags="confetti",
                )
            else:
                self.canvas.create_oval(
                    x - s, y - s, x + s, y + s,
                    fill=p["color"], outline="", tags="confetti",
                )
        self.canvas.after(30, self._animate)

    def stop(self):
        self.running = False
        self.canvas.delete("confetti")


# ────────────────────────────── Main Game ──────────────────────────────


class TicTacToeGame:
    """Main application controller managing all screens."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tic Tac Toe — Professional Edition")
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        self._center_window()

        self.settings = SettingsStore()
        self.sound = SoundManager(enabled=self.settings.get("sound_enabled"))
        self.history = HistoryManager()

        self.current_frame = None
        self.board = [""] * 9
        self.current_player = ""
        self.game_mode = None
        self.difficulty = "Hard"
        self.scores = {"X": 0, "O": 0, "draws": 0}
        self.game_active = False
        self.confetti = None
        self.celebration_canvas = None

        self._setup_fonts()
        self.show_main_menu()

    def _center_window(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - WINDOW_W) // 2
        y = (sh - WINDOW_H) // 2
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

    def _setup_fonts(self):
        self.f_title = tkfont.Font(family="Segoe UI", size=32, weight="bold")
        self.f_heading = tkfont.Font(family="Segoe UI", size=22, weight="bold")
        self.f_subheading = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.f_body = tkfont.Font(family="Segoe UI", size=13)
        self.f_button = tkfont.Font(family="Segoe UI", size=15, weight="bold")
        self.f_cell = tkfont.Font(family="Segoe UI", size=52, weight="bold")
        self.f_small = tkfont.Font(family="Segoe UI", size=11)
        self.f_score = tkfont.Font(family="Segoe UI", size=18, weight="bold")

    # ── Frame management ──

    def _clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()
        if self.celebration_canvas is not None:
            self.celebration_canvas.destroy()
            self.celebration_canvas = None
        self.current_frame = tk.Frame(self.root, bg=BG_DARK)
        self.current_frame.pack(fill="both", expand=True)

    def _make_button(self, parent, text, command, bg=ACCENT, fg="white",
                     font=None, width=None, height=2):
        if font is None:
            font = self.f_button
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=font,
            relief="flat", bd=0,
            activebackground=ACCENT_HOVER, activeforeground="white",
            cursor="hand2",
        )
        if width:
            btn.config(width=width)
        if height:
            btn.config(height=height)
        btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT_HOVER) if bg == ACCENT else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def _make_title(self, parent, text, font=None):
        if font is None:
            font = self.f_title
        lbl = tk.Label(parent, text=text, font=font,
                       bg=BG_DARK, fg=TEXT_LIGHT)
        lbl.pack(pady=(30, 5))
        return lbl

    def _make_subtitle(self, parent, text):
        lbl = tk.Label(parent, text=text, font=self.f_small,
                       bg=BG_DARK, fg=TEXT_DIM)
        lbl.pack(pady=(0, 20))
        return lbl

    # ────────────────────────────── Main Menu ──────────────────────────────

    def show_main_menu(self):
        self._clear_frame()
        f = self.current_frame

        self._make_title(f, "Tic Tac Toe")
        self._make_subtitle(f, "Professional Edition")

        btn_frame = tk.Frame(f, bg=BG_DARK)
        btn_frame.pack(pady=20)

        buttons = [
            ("▶  Play Game", self.show_mode_select, ACCENT),
            ("⚙  Settings", self.show_settings, BG_PANEL),
            ("📋  History", self.show_history, BG_PANEL),
            ("✕  Quit", self.root.quit, DANGER),
        ]
        for i, (text, cmd, color) in enumerate(buttons):
            btn = self._make_button(btn_frame, text, cmd, bg=color, width=18)
            btn.pack(pady=8, ipadx=10)

        footer = tk.Label(
            f, text="© 2026  •  Built with Tkinter",
            font=self.f_small, bg=BG_DARK, fg=TEXT_DIM,
        )
        footer.pack(side="bottom", pady=15)

    # ────────────────────────────── Mode Select ──────────────────────────────

    def show_mode_select(self):
        self._clear_frame()
        f = self.current_frame
        self._make_title(f, "Select Mode", font=self.f_heading)
        self._make_subtitle(f, "Choose how you want to play")

        btn_frame = tk.Frame(f, bg=BG_DARK)
        btn_frame.pack(pady=30)

        self._make_button(
            btn_frame, "🤖  vs Computer", self.show_difficulty_select,
            bg=ACCENT, width=20,
        ).pack(pady=10, ipadx=10)
        self._make_button(
            btn_frame, "👥  2 Players", lambda: self._start_game("2P"),
            bg=BG_PANEL, width=20,
        ).pack(pady=10, ipadx=10)
        self._make_button(
            btn_frame, "⬅  Back", self.show_main_menu,
            bg=DANGER, width=20,
        ).pack(pady=10, ipadx=10)

    # ────────────────────────────── Difficulty Select ──────────────────────────────

    def show_difficulty_select(self):
        self._clear_frame()
        f = self.current_frame
        self._make_title(f, "Difficulty", font=self.f_heading)
        self._make_subtitle(f, "How smart should the computer be?")

        btn_frame = tk.Frame(f, bg=BG_DARK)
        btn_frame.pack(pady=30)

        diffs = [
            ("🟢  Easy", "Easy", "#55efc4"),
            ("🟡  Medium", "Medium", GOLD),
            ("🔴  Hard", "Hard", DANGER),
        ]
        for text, diff, color in diffs:
            self._make_button(
                btn_frame, text, lambda d=diff: self._start_game("1P", d),
                bg=color, width=20,
            ).pack(pady=10, ipadx=10)

        self._make_button(
            btn_frame, "⬅  Back", self.show_mode_select,
            bg=BG_PANEL, width=20,
        ).pack(pady=10, ipadx=10)

    # ────────────────────────────── Game Screen ──────────────────────────────

    def _start_game(self, mode, difficulty="Hard"):
        self.sound.click()
        self.game_mode = mode
        self.difficulty = difficulty
        self.board = [""] * 9
        self.scores = {"X": 0, "O": 0, "draws": 0}
        p1_sym = self.settings.get("player1_symbol")
        self.current_player = p1_sym
        self.game_active = True
        self.show_game_screen()

    def show_game_screen(self):
        self._clear_frame()
        f = self.current_frame

        # Header
        header = tk.Frame(f, bg=BG_DARK)
        header.pack(fill="x", pady=(15, 5))

        mode_text = f"vs Computer ({self.difficulty})" if self.game_mode == "1P" else "2 Players"
        tk.Label(header, text=mode_text, font=self.f_subheading,
                 bg=BG_DARK, fg=ACCENT).pack()

        # Score board
        score_frame = tk.Frame(f, bg=BG_PANEL, relief="flat", bd=2)
        score_frame.pack(pady=10, padx=40, fill="x")

        p1_name = self.settings.get("player1_name")
        p2_name = "Computer" if self.game_mode == "1P" else self.settings.get("player2_name")
        p1_sym = self.settings.get("player1_symbol")
        p2_sym = "O" if p1_sym == "X" else "X"

        self.lbl_p1_score = tk.Label(
            score_frame, text=f"{p1_name} ({p1_sym})\n{self.scores[p1_sym]}",
            font=self.f_body, bg=BG_PANEL, fg=X_COLOR if p1_sym == "X" else O_COLOR,
            width=12, height=2,
        )
        self.lbl_p1_score.pack(side="left", padx=10, pady=8)

        self.lbl_draws = tk.Label(
            score_frame, text=f"Draws\n{self.scores['draws']}",
            font=self.f_body, bg=BG_PANEL, fg=TEXT_DIM,
            width=10, height=2,
        )
        self.lbl_draws.pack(side="left", padx=5, pady=8)

        self.lbl_p2_score = tk.Label(
            score_frame, text=f"{p2_name} ({p2_sym})\n{self.scores[p2_sym]}",
            font=self.f_body, bg=BG_PANEL, fg=X_COLOR if p2_sym == "X" else O_COLOR,
            width=12, height=2,
        )
        self.lbl_p2_score.pack(side="right", padx=10, pady=8)

        # Turn indicator
        self.lbl_turn = tk.Label(
            f, text=f"{p1_name}'s turn", font=self.f_subheading,
            bg=BG_DARK, fg=TEXT_LIGHT,
        )
        self.lbl_turn.pack(pady=(5, 10))

        # Board
        board_frame = tk.Frame(f, bg=BG_BOARD, relief="flat", bd=3)
        board_frame.pack(pady=10)

        self.cells = []
        cell_size = 130
        for i in range(9):
            row, col = divmod(i, 3)
            cell = tk.Button(
                board_frame, text="", font=self.f_cell,
                bg=BG_PANEL, fg=TEXT_LIGHT,
                width=3, height=1,
                relief="flat", bd=0,
                activebackground=BG_BOARD, activeforeground=TEXT_LIGHT,
                cursor="hand2",
                command=lambda idx=i: self._handle_click(idx),
            )
            cell.grid(row=row, column=col, padx=3, pady=3)
            self.cells.append(cell)

        # Bottom buttons
        bottom = tk.Frame(f, bg=BG_DARK)
        bottom.pack(side="bottom", pady=15, fill="x")
        self._make_button(
            bottom, "↻  New Round", self._new_round,
            bg=ACCENT, width=10,
        ).pack(side="left", padx=20)
        self._make_button(
            bottom, "⬅  Menu", self.show_main_menu,
            bg=DANGER, width=10,
        ).pack(side="right", padx=20)

    def _update_scores(self):
        p1_sym = self.settings.get("player1_symbol")
        p2_sym = "O" if p1_sym == "X" else "X"
        p1_name = self.settings.get("player1_name")
        p2_name = "Computer" if self.game_mode == "1P" else self.settings.get("player2_name")
        self.lbl_p1_score.config(text=f"{p1_name} ({p1_sym})\n{self.scores[p1_sym]}")
        self.lbl_p2_score.config(text=f"{p2_name} ({p2_sym})\n{self.scores[p2_sym]}")
        self.lbl_draws.config(text=f"Draws\n{self.scores['draws']}")

    def _update_turn_label(self):
        p1_sym = self.settings.get("player1_symbol")
        p2_sym = "O" if p1_sym == "X" else "X"
        p1_name = self.settings.get("player1_name")
        p2_name = "Computer" if self.game_mode == "1P" else self.settings.get("player2_name")
        if self.current_player == p1_sym:
            self.lbl_turn.config(text=f"{p1_name}'s turn", fg=X_COLOR if p1_sym == "X" else O_COLOR)
        else:
            self.lbl_turn.config(text=f"{p2_name}'s turn", fg=X_COLOR if p2_sym == "X" else O_COLOR)

    def _handle_click(self, idx):
        if not self.game_active or self.board[idx] != "":
            return
        if self.game_mode == "1P":
            p1_sym = self.settings.get("player1_symbol")
            if self.current_player != p1_sym:
                return
        self._make_move(idx, self.current_player)
        if self.game_active and self.game_mode == "1P":
            self.root.after(500, self._ai_move)

    def _ai_move(self):
        if not self.game_active:
            return
        p1_sym = self.settings.get("player1_symbol")
        ai_sym = "O" if p1_sym == "X" else "X"
        move = TicTacToeAI.get_move(self.board, ai_sym, p1_sym, self.difficulty)
        if move is not None:
            self._make_move(move, ai_sym)

    def _make_move(self, idx, symbol):
        self.board[idx] = symbol
        color = X_COLOR if symbol == "X" else O_COLOR
        self.cells[idx].config(text=symbol, fg=color, state="disabled")
        self.sound.place()

        winner = TicTacToeAI._check_winner(self.board)
        if winner:
            self._handle_win(winner)
        elif "" not in self.board:
            self._handle_draw()
        else:
            self.current_player = "O" if self.current_player == "X" else "X"
            self._update_turn_label()

    def _handle_win(self, winner):
        self.game_active = False
        self.scores[winner] += 1
        self._update_scores()
        self.sound.win()
        self._highlight_winning_line(winner)

        p1_sym = self.settings.get("player1_symbol")
        p2_sym = "O" if p1_sym == "X" else "X"
        p1_name = self.settings.get("player1_name")
        p2_name = "Computer" if self.game_mode == "1P" else self.settings.get("player2_name")
        winner_name = p1_name if winner == p1_sym else p2_name

        self.lbl_turn.config(text=f"🎉 {winner_name} wins! 🎉",
                             fg=GOLD, font=self.f_heading)

        self._record_game(winner_name, "win", winner)
        self._celebrate()

    def _handle_draw(self):
        self.game_active = False
        self.scores["draws"] += 1
        self._update_scores()
        self.sound.draw()
        self.lbl_turn.config(text="🤝 It's a Draw! 🤝", fg=TEXT_DIM, font=self.f_heading)
        self._record_game("—", "draw", None)

    def _highlight_winning_line(self, winner):
        for line in WIN_LINES:
            a, b, c = line
            if self.board[a] == self.board[b] == self.board[c] == winner:
                for idx in line:
                    self.cells[idx].config(bg=ACCENT)
                return

    def _new_round(self):
        self.sound.click()
        self.board = [""] * 9
        self.game_active = True
        p1_sym = self.settings.get("player1_symbol")
        self.current_player = p1_sym
        for cell in self.cells:
            cell.config(text="", bg=BG_PANEL, state="normal", fg=TEXT_LIGHT)
        self._update_turn_label()
        if self.celebration_canvas:
            self.celebration_canvas.destroy()
            self.celebration_canvas = None

    def _record_game(self, winner_name, result, symbol):
        p1_name = self.settings.get("player1_name")
        p2_name = "Computer" if self.game_mode == "1P" else self.settings.get("player2_name")
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mode": "vs Computer" if self.game_mode == "1P" else "2 Players",
            "difficulty": self.difficulty if self.game_mode == "1P" else "—",
            "players": f"{p1_name} vs {p2_name}",
            "result": f"{winner_name} wins" if result == "win" else "Draw",
            "scores": dict(self.scores),
        }
        self.history.add(record)

    def _celebrate(self):
        self.celebration_canvas = tk.Canvas(
            self.root, width=WINDOW_W, height=WINDOW_H,
            bg="", highlightthickness=0,
        )
        self.celebration_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.confetti = Confetti(self.celebration_canvas, WINDOW_W, WINDOW_H)
        self.confetti.start()
        self.root.after(4500, self._end_celebration)

    def _end_celebration(self):
        if self.celebration_canvas:
            self.celebration_canvas.destroy()
            self.celebration_canvas = None

    # ────────────────────────────── Settings ──────────────────────────────

    def show_settings(self):
        self._clear_frame()
        f = self.current_frame
        self._make_title(f, "Settings", font=self.f_heading)
        self._make_subtitle(f, "Customize your game")

        panel = tk.Frame(f, bg=BG_PANEL, relief="flat", bd=2)
        panel.pack(pady=10, padx=40, fill="x")

        # Sound toggle
        sound_frame = tk.Frame(panel, bg=BG_PANEL)
        sound_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(sound_frame, text="Sound Effects", font=self.f_body,
                 bg=BG_PANEL, fg=TEXT_LIGHT).pack(side="left")
        sound_var = tk.BooleanVar(value=self.settings.get("sound_enabled"))
        sound_cb = tk.Checkbutton(
            sound_frame, variable=sound_var, bg=BG_PANEL,
            activebackground=BG_PANEL, selectcolor=ACCENT,
            command=lambda: self._toggle_sound(sound_var.get()),
        )
        sound_cb.pack(side="right")

        # Player 1 name
        p1_frame = tk.Frame(panel, bg=BG_PANEL)
        p1_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(p1_frame, text="Player 1 Name", font=self.f_body,
                 bg=BG_PANEL, fg=TEXT_LIGHT).pack(side="left")
        p1_entry = tk.Entry(p1_frame, font=self.f_body, width=15)
        p1_entry.insert(0, self.settings.get("player1_name"))
        p1_entry.pack(side="right")

        # Player 2 name
        p2_frame = tk.Frame(panel, bg=BG_PANEL)
        p2_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(p2_frame, text="Player 2 Name", font=self.f_body,
                 bg=BG_PANEL, fg=TEXT_LIGHT).pack(side="left")
        p2_entry = tk.Entry(p2_frame, font=self.f_body, width=15)
        p2_entry.insert(0, self.settings.get("player2_name"))
        p2_entry.pack(side="right")

        # Symbol choice
        sym_frame = tk.Frame(panel, bg=BG_PANEL)
        sym_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(sym_frame, text="Player 1 Symbol", font=self.f_body,
                 bg=BG_PANEL, fg=TEXT_LIGHT).pack(side="left")
        sym_var = tk.StringVar(value=self.settings.get("player1_symbol"))
        tk.Radiobutton(sym_frame, text="X", variable=sym_var, value="X",
                       bg=BG_PANEL, fg=TEXT_LIGHT, selectcolor=BG_PANEL,
                       activebackground=BG_PANEL, font=self.f_body,
                       ).pack(side="right", padx=5)
        tk.Radiobutton(sym_frame, text="O", variable=sym_var, value="O",
                       bg=BG_PANEL, fg=TEXT_LIGHT, selectcolor=BG_PANEL,
                       activebackground=BG_PANEL, font=self.f_body,
                       ).pack(side="right", padx=5)

        # Save button
        def save_settings():
            self.settings.set("player1_name", p1_entry.get() or "Player 1")
            self.settings.set("player2_name", p2_entry.get() or "Player 2")
            self.settings.set("player1_symbol", sym_var.get())
            self.settings.set("sound_enabled", sound_var.get())
            self.sound.enabled = sound_var.get()
            self.sound.click()
            self.show_main_menu()

        btn_frame = tk.Frame(f, bg=BG_DARK)
        btn_frame.pack(pady=20)
        self._make_button(btn_frame, "💾  Save", save_settings,
                          bg=ACCENT, width=12).pack(side="left", padx=10)
        self._make_button(btn_frame, "⬅  Back", self.show_main_menu,
                          bg=DANGER, width=12).pack(side="right", padx=10)

    def _toggle_sound(self, enabled):
        self.sound.toggle(enabled)
        self.settings.set("sound_enabled", enabled)

    # ────────────────────────────── History ──────────────────────────────

    def show_history(self):
        self._clear_frame()
        f = self.current_frame
        self._make_title(f, "Game History", font=self.f_heading)
        self._make_subtitle(f, f"{len(self.history.history)} games played")

        # Scrollable list
        list_frame = tk.Frame(f, bg=BG_DARK)
        list_frame.pack(pady=10, padx=30, fill="both", expand=True)

        if not self.history.history:
            tk.Label(list_frame, text="No games played yet.\nStart playing to build history!",
                     font=self.f_body, bg=BG_DARK, fg=TEXT_DIM,
                     justify="center").pack(expand=True)
        else:
            canvas = tk.Canvas(list_frame, bg=BG_DARK, highlightthickness=0)
            scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
            scroll_frame = tk.Frame(canvas, bg=BG_DARK)

            scroll_frame.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            for record in reversed(self.history.history):
                self._make_history_card(scroll_frame, record)

        # Bottom buttons
        bottom = tk.Frame(f, bg=BG_DARK)
        bottom.pack(side="bottom", pady=15, fill="x")
        if self.history.history:
            self._make_button(bottom, "🗑  Clear", self._clear_history,
                              bg=DANGER, width=10).pack(side="left", padx=20)
        self._make_button(bottom, "⬅  Back", self.show_main_menu,
                          bg=BG_PANEL, width=10).pack(side="right", padx=20)

    def _make_history_card(self, parent, record):
        card = tk.Frame(parent, bg=BG_PANEL, relief="flat", bd=2)
        card.pack(fill="x", pady=4, padx=5)

        top = tk.Frame(card, bg=BG_PANEL)
        top.pack(fill="x", padx=10, pady=(5, 0))
        tk.Label(top, text=record["date"], font=self.f_small,
                 bg=BG_PANEL, fg=TEXT_DIM).pack(side="left")
        tk.Label(top, text=record["mode"], font=self.f_small,
                 bg=BG_PANEL, fg=ACCENT).pack(side="right")

        mid = tk.Frame(card, bg=BG_PANEL)
        mid.pack(fill="x", padx=10, pady=2)
        tk.Label(mid, text=record["players"], font=self.f_body,
                 bg=BG_PANEL, fg=TEXT_LIGHT).pack(side="left")
        if record["difficulty"] != "—":
            tk.Label(mid, text=f"[{record['difficulty']}]", font=self.f_small,
                     bg=BG_PANEL, fg=GOLD).pack(side="right")

        bot = tk.Frame(card, bg=BG_PANEL)
        bot.pack(fill="x", padx=10, pady=(0, 5))
        result_color = GOLD if "wins" in record["result"] else TEXT_DIM
        tk.Label(bot, text=record["result"], font=self.f_subheading,
                 bg=BG_PANEL, fg=result_color).pack(side="left")

    def _clear_history(self):
        self.sound.click()
        self.history.clear()
        self.show_history()

    # ────────────────────────────── Run ──────────────────────────────

    def run(self):
        self.root.mainloop()


# ────────────────────────────── Entry Point ──────────────────────────────

if __name__ == "__main__":
    game = TicTacToeGame()
    game.run()