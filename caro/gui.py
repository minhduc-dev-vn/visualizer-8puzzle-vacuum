# -*- coding: utf-8 -*-
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, scrolledtext

from algorithms import ALGORITHMS, SearchResult
from game import (
    AI,
    BOARD_SIZE,
    DRAW,
    EMPTY,
    HUMAN,
    Move,
    create_board,
    generate_candidate_moves,
    get_winner,
    move_to_text,
    place_move,
)


class CaroGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Caro - Minimax, Alpha-Beta, Expectimax")
        self.root.geometry("1050x760")
        self.root.minsize(980, 720)
        self.root.configure(bg="#f3f4f6")

        self.cell_size = 38
        self.margin = 28
        self.canvas_size = self.margin * 2 + self.cell_size * (BOARD_SIZE - 1)

        self.board = create_board()
        self.current_turn = HUMAN
        self.game_over = False
        self.last_move: Move | None = None

        self.algorithm_var = tk.StringVar(value="Alpha-Beta")
        self.depth_var = tk.IntVar(value=3)
        self.limit_var = tk.IntVar(value=10)
        self.status_var = tk.StringVar(value="Your turn: X")

        self._build_layout()
        self.draw_board()

    def _build_layout(self) -> None:
        main_frame = tk.Frame(self.root, bg="#f3f4f6")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        board_frame = tk.Frame(main_frame, bg="#ffffff", bd=1, relief=tk.SOLID)
        board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        title = tk.Label(
            board_frame,
            text="CARO 15x15 - Human X vs AI O",
            bg="#ffffff",
            fg="#111827",
            font=("Arial", 14, "bold"),
        )
        title.pack(pady=(12, 4))

        self.status_label = tk.Label(
            board_frame,
            textvariable=self.status_var,
            bg="#ffffff",
            fg="#374151",
            font=("Arial", 11),
        )
        self.status_label.pack(pady=(0, 8))

        self.canvas = tk.Canvas(
            board_frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="#fef3c7",
            highlightthickness=0,
        )
        self.canvas.pack(padx=12, pady=(0, 12))
        self.canvas.bind("<Button-1>", self.on_board_click)

        side_panel = tk.Frame(main_frame, bg="#f3f4f6", width=330)
        side_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        side_panel.pack_propagate(False)

        control_frame = tk.LabelFrame(
            side_panel,
            text="Algorithm",
            bg="#ffffff",
            fg="#111827",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=12,
        )
        control_frame.pack(fill=tk.X, pady=(0, 12))

        tk.Label(control_frame, text="Search method", bg="#ffffff", anchor=tk.W).pack(fill=tk.X)
        algorithm_menu = tk.OptionMenu(
            control_frame,
            self.algorithm_var,
            "Minimax",
            "Alpha-Beta",
            "Expectimax",
            command=self.on_algorithm_change,
        )
        algorithm_menu.configure(bg="#e5e7eb", activebackground="#d1d5db", relief=tk.FLAT)
        algorithm_menu.pack(fill=tk.X, pady=(4, 10))

        depth_row = tk.Frame(control_frame, bg="#ffffff")
        depth_row.pack(fill=tk.X, pady=4)
        tk.Label(depth_row, text="Depth", bg="#ffffff").pack(side=tk.LEFT)
        tk.Spinbox(depth_row, from_=1, to=5, textvariable=self.depth_var, width=8).pack(side=tk.RIGHT)

        limit_row = tk.Frame(control_frame, bg="#ffffff")
        limit_row.pack(fill=tk.X, pady=4)
        tk.Label(limit_row, text="Candidate limit", bg="#ffffff").pack(side=tk.LEFT)
        tk.Spinbox(limit_row, from_=4, to=20, textvariable=self.limit_var, width=8).pack(side=tk.RIGHT)

        button_frame = tk.Frame(control_frame, bg="#ffffff")
        button_frame.pack(fill=tk.X, pady=(12, 0))

        tk.Button(
            button_frame,
            text="New game",
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            relief=tk.FLAT,
            command=self.new_game,
        ).pack(fill=tk.X, pady=(0, 6))

        tk.Button(
            button_frame,
            text="AI goes first",
            bg="#059669",
            fg="#ffffff",
            activebackground="#047857",
            relief=tk.FLAT,
            command=self.ai_goes_first,
        ).pack(fill=tk.X, pady=(0, 6))

        tk.Button(
            button_frame,
            text="Ask AI for current move",
            bg="#7c3aed",
            fg="#ffffff",
            activebackground="#6d28d9",
            relief=tk.FLAT,
            command=self.run_ai_turn,
        ).pack(fill=tk.X)

        note_frame = tk.LabelFrame(
            side_panel,
            text="Notes",
            bg="#ffffff",
            fg="#111827",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=10,
        )
        note_frame.pack(fill=tk.X, pady=(0, 12))

        note = (
            "Minimax: AI maximizes score, opponent minimizes score.\n"
            "Alpha-Beta: same result idea, but prunes useless branches.\n"
            "Expectimax: opponent is modeled as a random chance node.\n\n"
            "High depth can be slow on a 15x15 board."
        )
        tk.Label(note_frame, text=note, bg="#ffffff", fg="#374151", justify=tk.LEFT, wraplength=285).pack(fill=tk.X)

        log_frame = tk.LabelFrame(
            side_panel,
            text="Search log",
            bg="#ffffff",
            fg="#111827",
            font=("Arial", 10, "bold"),
            padx=8,
            pady=8,
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=14,
            bg="#111827",
            fg="#f9fafb",
            insertbackground="#f9fafb",
            font=("Consolas", 9),
            relief=tk.FLAT,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log("Game ready. Human plays X, AI plays O.")

    def on_algorithm_change(self, selected: str) -> None:
        defaults = {
            "Minimax": (2, 10),
            "Alpha-Beta": (3, 12),
            "Expectimax": (2, 8),
        }
        depth, limit = defaults[selected]
        self.depth_var.set(depth)
        self.limit_var.set(limit)
        self.log(f"Selected {selected}: depth={depth}, candidates={limit}.")

    def new_game(self) -> None:
        self.board = create_board()
        self.current_turn = HUMAN
        self.game_over = False
        self.last_move = None
        self.status_var.set("Your turn: X")
        self.log_text.delete("1.0", tk.END)
        self.log("New game. Human plays X.")
        self.draw_board()

    def ai_goes_first(self) -> None:
        self.new_game()
        self.current_turn = AI
        self.run_ai_turn()

    def log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def board_to_canvas(self, row: int, col: int) -> tuple[int, int]:
        return self.margin + col * self.cell_size, self.margin + row * self.cell_size

    def canvas_to_board(self, x: int, y: int) -> Move | None:
        col = round((x - self.margin) / self.cell_size)
        row = round((y - self.margin) / self.cell_size)
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return None

        center_x, center_y = self.board_to_canvas(row, col)
        if abs(x - center_x) > self.cell_size / 2 or abs(y - center_y) > self.cell_size / 2:
            return None
        return row, col

    def draw_board(self) -> None:
        self.canvas.delete("all")
        start = self.margin
        end = self.margin + self.cell_size * (BOARD_SIZE - 1)

        for index in range(BOARD_SIZE):
            offset = self.margin + index * self.cell_size
            width = 2 if index in (0, BOARD_SIZE - 1) else 1
            self.canvas.create_line(start, offset, end, offset, fill="#92400e", width=width)
            self.canvas.create_line(offset, start, offset, end, fill="#92400e", width=width)

        if self.last_move:
            row, col = self.last_move
            x, y = self.board_to_canvas(row, col)
            r = self.cell_size // 2 - 2
            self.canvas.create_rectangle(x - r, y - r, x + r, y + r, outline="#16a34a", width=3)

        stone_radius = self.cell_size // 2 - 5
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell = self.board[row][col]
                if cell == EMPTY:
                    continue
                x, y = self.board_to_canvas(row, col)
                fill = "#1f2937" if cell == HUMAN else "#dc2626"
                self.canvas.create_oval(
                    x - stone_radius,
                    y - stone_radius,
                    x + stone_radius,
                    y + stone_radius,
                    fill=fill,
                    outline="#ffffff",
                    width=2,
                )
                self.canvas.create_text(
                    x,
                    y,
                    text=cell,
                    fill="#ffffff",
                    font=("Arial", 15, "bold"),
                )

    def on_board_click(self, event: tk.Event) -> None:
        if self.game_over:
            return
        if self.current_turn != HUMAN:
            self.log("Please wait for the AI move.")
            return

        move = self.canvas_to_board(event.x, event.y)
        if move is None:
            return
        row, col = move
        if self.board[row][col] != EMPTY:
            return

        place_move(self.board, move, HUMAN)
        self.last_move = move
        self.log(f"Human X -> {move_to_text(move)}")
        self.draw_board()

        if self.check_finished():
            return

        self.current_turn = AI
        self.status_var.set("AI is thinking...")
        self.root.after(150, self.run_ai_turn)

    def run_ai_turn(self) -> None:
        if self.game_over:
            return

        algorithm_name = self.algorithm_var.get()
        depth = max(1, int(self.depth_var.get()))
        candidate_limit = max(1, int(self.limit_var.get()))
        decision_function = ALGORITHMS[algorithm_name]

        self.current_turn = AI
        self.status_var.set(f"{algorithm_name} is thinking...")
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        result = decision_function(self.board, AI, depth, candidate_limit)
        self.root.config(cursor="")

        move = result.move
        if move is None:
            candidates = generate_candidate_moves(self.board, AI, limit=1)
            move = candidates[0] if candidates else None

        if move is None:
            self.game_over = True
            self.status_var.set("Draw.")
            self.log("No legal move left.")
            return

        place_move(self.board, move, AI)
        self.last_move = move
        self.log_ai_result(result)
        self.draw_board()

        if self.check_finished():
            return

        self.current_turn = HUMAN
        self.status_var.set("Your turn: X")

    def log_ai_result(self, result: SearchResult) -> None:
        parts = [
            f"{result.algorithm} O -> {move_to_text(result.move)}",
            f"score={result.score:.1f}",
            f"nodes={result.nodes}",
            f"time={result.elapsed:.3f}s",
        ]
        if result.pruned:
            parts.append(f"pruned={result.pruned}")
        self.log(" | ".join(parts))

    def check_finished(self) -> bool:
        winner = get_winner(self.board)
        if winner is None:
            return False

        self.game_over = True
        if winner == HUMAN:
            message = "Human X wins."
        elif winner == AI:
            message = "AI O wins."
        elif winner == DRAW:
            message = "Draw."
        else:
            message = f"{winner} wins."

        self.status_var.set(message)
        self.log(message)
        messagebox.showinfo("Game over", message)
        return True
