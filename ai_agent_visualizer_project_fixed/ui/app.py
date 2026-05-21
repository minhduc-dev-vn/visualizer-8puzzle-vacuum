from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Dict, List, Optional, Tuple

from algorithms import ALGORITHMS
from algorithms.common import SearchNode, SearchResult, TraceEntry
from problems.puzzle import PuzzleProblem, PuzzleState
from problems.vacuum import VacuumProblem, VacuumState


class AIVisualizerApp(tk.Tk):
    """
    GUI chính.

    Thay đổi quan trọng so với bản cũ:
    - Không vẽ bảng trace bằng Canvas nữa.
    - Dùng ttk.Treeview + thanh cuộn ngang/dọc nên bảng xem được nội dung dài.
    - Search chạy trong background thread để tránh treo/crash giao diện.
    - APPLY sẽ tìm lời giải rồi tự động animate từng bước.
    - Mỗi bước di chuyển sẽ insert đúng một dòng trace tương ứng vào bảng.
    """

    CELL_SIZE = 128
    GAP = 8

    COLORS = {
        "bg": "#0B1328",
        "panel": "#111A33",
        "panel_2": "#0D162D",
        "border": "#30406F",
        "accent": "#45CCEF",
        "accent_2": "#68F2FF",
        "text": "#F8FBFF",
        "muted": "#B8C7FF",
        "blank": "#0C1428",
        "tile": "#45CCEF",
        "clean": "#12341F",
        "dust": "#3D2F16",
        "obstacle": "#44546F",
        "danger": "#FF6B6B",
    }

    def __init__(self) -> None:
        super().__init__()

        self.title("AI Agent Visualizer - BFS/DFS")
        self.geometry("1360x820")
        self.minsize(1250, 760)
        self.configure(bg=self.COLORS["bg"])

        self.mode_var = tk.StringVar(value="8-PUZZLE")
        self.algorithm_var = tk.StringVar(value="BFS1")
        self.max_expansions_var = tk.StringVar(value="6000")
        self.max_depth_var = tk.StringVar(value="12")

        self.puzzle_state: PuzzleState = PuzzleProblem.START
        self.vacuum_state: VacuumState = VacuumProblem.start_state()
        self.vacuum_initial_dirt = max(1, VacuumProblem.dirty_count(self.vacuum_state))

        self.search_result: Optional[SearchResult] = None
        self.solution_path: List[SearchNode] = []
        self.current_step = 0

        self.animation_job: Optional[str] = None
        self.is_animating = False
        self.is_searching = False

        self.result_queue: queue.Queue = queue.Queue()

        self._setup_styles()
        self._build_layout()
        self._bind_events()
        self.draw_board()
        self.update_status("Ready. Choose problem, algorithm, then press APPLY.")

    # ========================================================
    # Layout
    # ========================================================

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            ".",
            background=self.COLORS["bg"],
            foreground=self.COLORS["text"],
            fieldbackground=self.COLORS["panel_2"],
            font=("Consolas", 10),
        )

        style.configure(
            "Dark.TFrame",
            background=self.COLORS["bg"],
        )

        style.configure(
            "Panel.TFrame",
            background=self.COLORS["panel"],
            borderwidth=2,
            relief="solid",
        )

        style.configure(
            "Title.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["text"],
            font=("Consolas", 24, "bold"),
        )

        style.configure(
            "Muted.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["muted"],
            font=("Consolas", 10),
        )

        style.configure(
            "Panel.TLabel",
            background=self.COLORS["panel"],
            foreground=self.COLORS["text"],
            font=("Consolas", 11, "bold"),
        )

        style.configure(
            "Accent.TButton",
            background=self.COLORS["accent"],
            foreground="#04111F",
            font=("Consolas", 11, "bold"),
            borderwidth=0,
            padding=8,
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.COLORS["accent_2"])],
        )

        style.configure(
            "Dark.TButton",
            background=self.COLORS["panel_2"],
            foreground=self.COLORS["text"],
            font=("Consolas", 10, "bold"),
            borderwidth=1,
            padding=8,
        )
        style.map(
            "Dark.TButton",
            background=[("active", self.COLORS["border"])],
        )

        style.configure(
            "Treeview",
            background=self.COLORS["panel_2"],
            foreground=self.COLORS["text"],
            fieldbackground=self.COLORS["panel_2"],
            rowheight=34,
            bordercolor=self.COLORS["border"],
            borderwidth=1,
            font=("Consolas", 9),
        )

        style.configure(
            "Treeview.Heading",
            background=self.COLORS["panel"],
            foreground=self.COLORS["accent_2"],
            font=("Consolas", 9, "bold"),
        )

        style.map(
            "Treeview",
            background=[("selected", self.COLORS["border"])],
            foreground=[("selected", self.COLORS["text"])],
        )

    def _build_layout(self) -> None:
        self._build_header()

        body = ttk.Frame(self, style="Dark.TFrame", padding=12)
        body.pack(fill=tk.BOTH, expand=True)

        self.sidebar = ttk.Frame(body, style="Panel.TFrame", padding=14)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        center = ttk.Frame(body, style="Dark.TFrame")
        center.pack(side=tk.LEFT, fill=tk.BOTH, padx=12)

        right = ttk.Frame(body, style="Dark.TFrame")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_sidebar(self.sidebar)
        self._build_board_area(center)
        self._build_trace_area(right)
        self._build_detail_area(right)

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=self.COLORS["panel"], height=74)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="AI AGENT VISUALIZER",
            bg=self.COLORS["panel"],
            fg=self.COLORS["text"],
            font=("Consolas", 19, "bold"),
        )
        title.place(x=28, y=16)

        subtitle = tk.Label(
            header,
            text="Search Algorithms Console",
            bg=self.COLORS["panel"],
            fg=self.COLORS["muted"],
            font=("Consolas", 9),
        )
        subtitle.place(x=30, y=48)

        puzzle_btn = ttk.Radiobutton(
            header,
            text="8-PUZZLE",
            value="8-PUZZLE",
            variable=self.mode_var,
            command=self.on_mode_changed,
            style="Toolbutton",
        )
        puzzle_btn.place(x=380, y=18, width=150, height=40)

        vacuum_btn = ttk.Radiobutton(
            header,
            text="VACUUM",
            value="VACUUM",
            variable=self.mode_var,
            command=self.on_mode_changed,
            style="Toolbutton",
        )
        vacuum_btn.place(x=548, y=18, width=150, height=40)

        line = tk.Frame(self, bg=self.COLORS["accent"], height=2)
        line.pack(fill=tk.X)

    def _build_sidebar(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Algorithm", style="Panel.TLabel").pack(anchor=tk.W, pady=(0, 8))

        self.algorithm_combo = ttk.Combobox(
            parent,
            textvariable=self.algorithm_var,
            values=["BFS1", "BFS2", "DFS1", "DFS2"],
            state="readonly",
            width=14,
            font=("Consolas", 11, "bold"),
        )
        self.algorithm_combo.pack(fill=tk.X, pady=(0, 18))

        ttk.Label(parent, text="Max expansions", style="Panel.TLabel").pack(anchor=tk.W, pady=(0, 8))

        self.max_entry = ttk.Entry(
            parent,
            textvariable=self.max_expansions_var,
            width=14,
            font=("Consolas", 10),
        )
        self.max_entry.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(parent, text="DFS max depth", style="Panel.TLabel").pack(anchor=tk.W, pady=(0, 8))

        self.max_depth_entry = ttk.Entry(
            parent,
            textvariable=self.max_depth_var,
            width=14,
            font=("Consolas", 10),
        )
        self.max_depth_entry.pack(fill=tk.X, pady=(0, 18))

        self.apply_button = ttk.Button(
            parent,
            text="APPLY",
            style="Accent.TButton",
            command=self.apply_search,
        )
        self.apply_button.pack(fill=tk.X, pady=(190, 8))

        self.stop_button = ttk.Button(
            parent,
            text="STOP",
            style="Dark.TButton",
            command=self.stop_animation,
        )
        self.stop_button.pack(fill=tk.X, pady=4)

        self.shuffle_button = ttk.Button(
            parent,
            text="SHUFFLE / RANDOM",
            style="Dark.TButton",
            command=self.shuffle_current_problem,
        )
        self.shuffle_button.pack(fill=tk.X, pady=4)

        self.reset_button = ttk.Button(
            parent,
            text="RESET",
            style="Dark.TButton",
            command=self.reset_current_problem,
        )
        self.reset_button.pack(fill=tk.X, pady=4)

        help_text = (
            "Manual:\n"
            "W/A/S/D: move\n"
            "Space: suck\n"
            "Mouse: click cell\n\n"
            "BFS1/DFS1:\n"
            "check goal when popped\n\n"
            "BFS2/DFS2:\n"
            "check goal when generated\n\n"
            "DFS uses depth limit\n"
            "to avoid 8-puzzle runaway."
        )

        tk.Label(
            parent,
            text=help_text,
            bg=self.COLORS["panel"],
            fg=self.COLORS["muted"],
            justify=tk.LEFT,
            font=("Consolas", 9),
        ).pack(anchor=tk.W, pady=(18, 0))

    def _build_board_area(self, parent: ttk.Frame) -> None:
        self.title_label = ttk.Label(parent, text="8-Puzzle", style="Title.TLabel")
        self.title_label.pack(anchor=tk.W, pady=(4, 4))

        self.description_label = ttk.Label(
            parent,
            text="Play with mouse, or click APPLY to watch BFS/DFS solve it.",
            style="Muted.TLabel",
        )
        self.description_label.pack(anchor=tk.W, pady=(0, 18))

        self.board_canvas = tk.Canvas(
            parent,
            width=3 * self.CELL_SIZE + 2 * self.GAP + 26,
            height=3 * self.CELL_SIZE + 2 * self.GAP + 26,
            bg=self.COLORS["panel"],
            highlightthickness=2,
            highlightbackground=self.COLORS["border"],
        )
        self.board_canvas.pack(anchor=tk.CENTER)
        self.board_canvas.bind("<Button-1>", self.on_board_click)

        self.stats_label = tk.Label(
            parent,
            text="",
            bg=self.COLORS["bg"],
            fg=self.COLORS["accent_2"],
            font=("Consolas", 11, "bold"),
            justify=tk.LEFT,
        )
        self.stats_label.pack(anchor=tk.W, pady=(18, 6))

        self.status_label = tk.Label(
            parent,
            text="",
            bg=self.COLORS["panel"],
            fg=self.COLORS["muted"],
            font=("Consolas", 10),
            justify=tk.LEFT,
            anchor="w",
            wraplength=430,
            padx=12,
            pady=10,
        )
        self.status_label.pack(fill=tk.X, pady=(4, 0))

    def _build_trace_area(self, parent: ttk.Frame) -> None:
        title_frame = ttk.Frame(parent, style="Dark.TFrame")
        title_frame.pack(fill=tk.X)

        ttk.Label(
            title_frame,
            text="Search Trace - full Node | Frontier | Reached",
            style="Title.TLabel",
            font=("Consolas", 17, "bold"),
        ).pack(side=tk.LEFT, anchor=tk.W)

        self.step_counter_label = ttk.Label(
            title_frame,
            text="0/0",
            style="Muted.TLabel",
            font=("Consolas", 11, "bold"),
        )
        self.step_counter_label.pack(side=tk.RIGHT, anchor=tk.E, padx=(0, 8))

        table_frame = ttk.Frame(parent, style="Dark.TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        columns = ("step", "action", "current", "frontier_count", "frontier", "reached_count", "reached", "note")

        self.trace_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=12,
        )

        headings = {
            "step": "Step",
            "action": "Action",
            "current": "Current Node",
            "frontier_count": "F.Count",
            "frontier": "Frontier - FULL",
            "reached_count": "R.Count",
            "reached": "Reached - FULL",
            "note": "Note",
        }

        widths = {
            "step": 60,
            "action": 95,
            "current": 160,
            "frontier_count": 75,
            "frontier": 760,
            "reached_count": 75,
            "reached": 960,
            "note": 260,
        }

        for col in columns:
            self.trace_tree.heading(col, text=headings[col])
            self.trace_tree.column(col, width=widths[col], minwidth=widths[col], stretch=False, anchor=tk.W)

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.trace_tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.trace_tree.xview)

        self.trace_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.trace_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.trace_tree.bind("<<TreeviewSelect>>", self.on_trace_selected)

    def _build_detail_area(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="Selected trace detail",
            style="Muted.TLabel",
            font=("Consolas", 11, "bold"),
        ).pack(anchor=tk.W)

        self.detail_text = ScrolledText(
            parent,
            height=10,
            bg=self.COLORS["panel_2"],
            fg=self.COLORS["text"],
            insertbackground=self.COLORS["text"],
            relief=tk.FLAT,
            font=("Consolas", 9),
            wrap=tk.NONE,
        )
        self.detail_text.pack(fill=tk.X, pady=(6, 0))
        self.detail_text.configure(state=tk.DISABLED)

    def _bind_events(self) -> None:
        self.bind_all("<KeyPress>", self.on_key_press)

    # ========================================================
    # Drawing
    # ========================================================

    def draw_board(self) -> None:
        self.board_canvas.delete("all")

        if self.mode_var.get() == "8-PUZZLE":
            self.title_label.configure(text="8-Puzzle")
            self.description_label.configure(
                text="Play with mouse, or click APPLY to watch BFS/DFS solve it."
            )
            self.draw_puzzle()
        else:
            self.title_label.configure(text="Vacuum")
            self.description_label.configure(
                text="Robot cleans dust, avoids obstacles, and stops when all cells are clean."
            )
            self.draw_vacuum()

        self.update_stats()

    def draw_puzzle(self) -> None:
        state = self.puzzle_state
        offset = 13

        for index, value in enumerate(state):
            row, col = divmod(index, 3)

            x1 = offset + col * (self.CELL_SIZE + self.GAP)
            y1 = offset + row * (self.CELL_SIZE + self.GAP)
            x2 = x1 + self.CELL_SIZE
            y2 = y1 + self.CELL_SIZE

            if value == 0:
                self.draw_blank_tile(x1, y1, x2, y2)
            else:
                self.draw_number_tile(x1, y1, x2, y2, value)

    def draw_number_tile(self, x1: int, y1: int, x2: int, y2: int, value: int) -> None:
        self.board_canvas.create_rectangle(x1 + 5, y1 + 5, x2 + 5, y2 + 5, fill="#070D1C", outline="")
        self.board_canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=self.COLORS["tile"],
            outline="#8DF2FF",
            width=3,
        )
        self.board_canvas.create_rectangle(x1 + 6, y1 + 6, x2 - 6, y2 - 6, outline="#36A9D6", width=2)
        self.board_canvas.create_text(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            text=str(value),
            fill="#EFF9FF",
            font=("Consolas", 38, "bold"),
        )

    def draw_blank_tile(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self.board_canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=self.COLORS["blank"],
            outline="#25375E",
            width=2,
        )

        for dx in range(x1 + 14, x2 - 10, 22):
            for dy in range(y1 + 14, y2 - 10, 22):
                self.board_canvas.create_rectangle(dx, dy, dx + 4, dy + 4, fill="#121F3D", outline="")

    def draw_vacuum(self) -> None:
        pos, grid = self.vacuum_state
        offset = 13

        for row in range(3):
            for col in range(3):
                x1 = offset + col * (self.CELL_SIZE + self.GAP)
                y1 = offset + row * (self.CELL_SIZE + self.GAP)
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE

                value = grid[row][col]

                if value == -1:
                    fill = self.COLORS["obstacle"]
                    label = "X"
                    label_color = self.COLORS["text"]
                elif value == 1:
                    fill = self.COLORS["dust"]
                    label = "dust"
                    label_color = "#F7C948"
                else:
                    fill = self.COLORS["clean"]
                    label = ""
                    label_color = "#2FD184"

                self.board_canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline=self.COLORS["border"],
                    width=3,
                )

                if label:
                    self.board_canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text=label,
                        fill=label_color,
                        font=("Consolas", 17, "bold"),
                    )

        robot_row, robot_col = pos
        cx = offset + robot_col * (self.CELL_SIZE + self.GAP) + self.CELL_SIZE // 2
        cy = offset + robot_row * (self.CELL_SIZE + self.GAP) + self.CELL_SIZE // 2

        self.board_canvas.create_oval(
            cx - 37,
            cy - 37,
            cx + 37,
            cy + 37,
            fill=self.COLORS["accent"],
            outline="#8DF2FF",
            width=3,
        )
        self.board_canvas.create_text(
            cx,
            cy,
            text="R",
            fill="#05111F",
            font=("Consolas", 28, "bold"),
        )

    # ========================================================
    # Status / Stats
    # ========================================================

    def update_status(self, message: str) -> None:
        self.status_label.configure(text=f"System status: {message}")

    def update_stats(self) -> None:
        if self.mode_var.get() == "8-PUZZLE":
            solved = PuzzleProblem.is_goal(self.puzzle_state)
            text = (
                f"Mode: 8-PUZZLE\n"
                f"Algorithm: {self.algorithm_var.get()}\n"
                f"Moves: {self.current_step if self.solution_path else 0}\n"
                f"Goal: 123/456/78_\n"
                f"Solved: {'YES' if solved else 'NO'}"
            )
        else:
            dirty = VacuumProblem.dirty_count(self.vacuum_state)
            obstacles = VacuumProblem.obstacle_count(self.vacuum_state)
            cleaned = max(0, self.vacuum_initial_dirt - dirty)
            text = (
                f"Mode: VACUUM\n"
                f"Algorithm: {self.algorithm_var.get()}\n"
                f"Moves: {self.current_step if self.solution_path else 0}\n"
                f"Dust cleaned: {cleaned}/{self.vacuum_initial_dirt}\n"
                f"Dust left: {dirty} | Obstacles: {obstacles}"
            )

        self.stats_label.configure(text=text)

        total = max(0, len(self.solution_path) - 1)
        self.step_counter_label.configure(text=f"{min(self.current_step, total)}/{total}")

    # ========================================================
    # Trace table
    # ========================================================

    def clear_trace_table(self) -> None:
        for item in self.trace_tree.get_children():
            self.trace_tree.delete(item)

        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.configure(state=tk.DISABLED)

    def insert_trace_row_for_node(self, step: int, node: SearchNode) -> None:
        entry = None

        if self.search_result is not None:
            entry = self.search_result.trace_by_state.get(node.state)

        if entry is None:
            current_text = self.current_formatter()(node.state)
            values = (
                step,
                node.action,
                current_text,
                0,
                "",
                0,
                "",
                "Trace entry was not found for this state.",
            )
        else:
            values = (
                step,
                node.action,
                entry.current_text,
                entry.frontier_count,
                entry.frontier_text,
                entry.reached_count,
                entry.reached_text,
                entry.note,
            )

        item_id = self.trace_tree.insert("", tk.END, values=values)
        self.trace_tree.see(item_id)
        self.trace_tree.selection_set(item_id)
        self.show_trace_detail(values)

    def on_trace_selected(self, _event: tk.Event) -> None:
        selected = self.trace_tree.selection()

        if not selected:
            return

        values = self.trace_tree.item(selected[0], "values")
        self.show_trace_detail(values)

    def show_trace_detail(self, values) -> None:
        if not values:
            return

        step, action, current, frontier_count, frontier, reached_count, reached, note = values

        content = (
            f"STEP: {step}\n"
            f"ACTION: {action}\n"
            f"CURRENT NODE:\n{current}\n\n"
            f"FRONTIER COUNT: {frontier_count}\n"
            f"FRONTIER FULL:\n{frontier if frontier else '-'}\n\n"
            f"REACHED COUNT: {reached_count}\n"
            f"REACHED FULL:\n{reached if reached else '-'}\n\n"
            f"NOTE:\n{note}\n"
        )

        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, content)
        self.detail_text.configure(state=tk.DISABLED)

    # ========================================================
    # Search / Animation
    # ========================================================

    def apply_search(self) -> None:
        if self.is_searching:
            return

        self.stop_animation()
        self.clear_trace_table()

        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.update_stats()

        max_expansions = self.read_max_expansions()
        max_depth = self.read_max_depth()
        self.is_searching = True
        self.apply_button.configure(state=tk.DISABLED)
        self.update_status("Searching in background thread. UI will not freeze.")

        start_state = self.current_state()
        algorithm_name = self.algorithm_var.get()
        search_function = ALGORITHMS[algorithm_name]

        if self.mode_var.get() == "8-PUZZLE":
            is_goal = PuzzleProblem.is_goal
            successors = PuzzleProblem.successors
            formatter = PuzzleProblem.format_state
        else:
            is_goal = VacuumProblem.is_goal
            successors = VacuumProblem.successors
            formatter = VacuumProblem.format_state

        def worker() -> None:
            try:
                result = search_function(
                    start_state=start_state,
                    is_goal=is_goal,
                    get_successors=successors,
                    formatter=formatter,
                    max_expansions=max_expansions,
                    max_depth=max_depth,
                )
                self.result_queue.put(("success", result))
            except Exception as exc:  # noqa: BLE001 - lỗi cần hiển thị lên GUI.
                self.result_queue.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self.poll_search_result)

    def poll_search_result(self) -> None:
        try:
            kind, payload = self.result_queue.get_nowait()
        except queue.Empty:
            self.after(100, self.poll_search_result)
            return

        self.is_searching = False
        self.apply_button.configure(state=tk.NORMAL)

        if kind == "error":
            self.update_status(f"Search error: {payload}")
            return

        result: SearchResult = payload
        self.search_result = result

        if not result.found:
            self.update_status(f"{result.message} Expansions: {result.expansions}.")
            return

        self.solution_path = result.path
        self.current_step = 0
        self.is_animating = True

        self.update_status(
            f"Found solution: {len(result.path) - 1} moves, expansions={result.expansions}. Animating..."
        )
        self.animate_next_step()

    def animate_next_step(self) -> None:
        if not self.is_animating:
            return

        if self.current_step >= len(self.solution_path):
            self.is_animating = False
            self.current_step = max(0, len(self.solution_path) - 1)
            self.update_status("Completed. Goal reached.")
            self.draw_board()
            return

        node = self.solution_path[self.current_step]
        self.set_current_state(node.state)

        self.draw_board()
        self.insert_trace_row_for_node(self.current_step, node)

        if self.current_step == 0:
            self.update_status("Step 0: START")
        else:
            self.update_status(f"Step {self.current_step}: {node.action}")

        self.current_step += 1
        self.animation_job = self.after(700, self.animate_next_step)

    def stop_animation(self) -> None:
        self.is_animating = False

        if self.animation_job is not None:
            try:
                self.after_cancel(self.animation_job)
            except tk.TclError:
                pass
            finally:
                self.animation_job = None

        if not self.is_searching:
            self.update_status("Stopped.")

    # ========================================================
    # Events / Manual control
    # ========================================================

    def on_mode_changed(self) -> None:
        self.stop_animation()
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()
        self.update_status(f"Switched to {self.mode_var.get()}.")

    def on_key_press(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        key_to_action = {
            "w": "UP",
            "a": "LEFT",
            "s": "DOWN",
            "d": "RIGHT",
            "space": "SUCK",
        }

        if key not in key_to_action:
            return

        action = key_to_action[key]
        self.stop_animation()

        if self.mode_var.get() == "8-PUZZLE":
            if action == "SUCK":
                return

            old_state = self.puzzle_state
            self.puzzle_state = PuzzleProblem.move_blank(self.puzzle_state, action)

            if self.puzzle_state != old_state:
                self.after_manual_change(f"Manual action: {action}")

        else:
            old_state = self.vacuum_state
            self.vacuum_state = VacuumProblem.manual_action(self.vacuum_state, action)

            if self.vacuum_state != old_state:
                self.after_manual_change(f"Manual action: {action}")

    def on_board_click(self, event: tk.Event) -> None:
        row_col = self.board_cell_at(event.x, event.y)

        if row_col is None:
            return

        row, col = row_col
        self.stop_animation()

        if self.mode_var.get() == "8-PUZZLE":
            old_state = self.puzzle_state
            self.puzzle_state = PuzzleProblem.click_move(self.puzzle_state, row, col)

            if self.puzzle_state != old_state:
                self.after_manual_change("Moved by mouse.")

        else:
            old_state = self.vacuum_state
            self.vacuum_state = VacuumProblem.click_action(self.vacuum_state, row, col)

            if self.vacuum_state != old_state:
                self.after_manual_change("Vacuum changed by mouse.")

    def after_manual_change(self, message: str) -> None:
        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()

        if self.current_is_goal():
            self.update_status("Completed. Goal reached.")
        else:
            self.update_status(message)

    def board_cell_at(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        offset = 13

        for row in range(3):
            for col in range(3):
                x1 = offset + col * (self.CELL_SIZE + self.GAP)
                y1 = offset + row * (self.CELL_SIZE + self.GAP)
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE

                if x1 <= x <= x2 and y1 <= y <= y2:
                    return row, col

        return None

    # ========================================================
    # State helpers
    # ========================================================

    def current_state(self) -> object:
        return self.puzzle_state if self.mode_var.get() == "8-PUZZLE" else self.vacuum_state

    def set_current_state(self, state: object) -> None:
        if self.mode_var.get() == "8-PUZZLE":
            self.puzzle_state = state  # type: ignore[assignment]
        else:
            self.vacuum_state = state  # type: ignore[assignment]

    def current_formatter(self):
        return PuzzleProblem.format_state if self.mode_var.get() == "8-PUZZLE" else VacuumProblem.format_state

    def current_is_goal(self) -> bool:
        if self.mode_var.get() == "8-PUZZLE":
            return PuzzleProblem.is_goal(self.puzzle_state)

        return VacuumProblem.is_goal(self.vacuum_state)

    def read_max_expansions(self) -> int:
        try:
            value = int(self.max_expansions_var.get())
        except ValueError:
            value = 6000

        # Giới hạn cứng để tránh người dùng nhập quá lớn rồi làm máy bị treo.
        return max(100, min(value, 50000))

    def read_max_depth(self) -> int:
        try:
            value = int(self.max_depth_var.get())
        except ValueError:
            value = 12

        # Depth quá lớn làm DFS 8-Puzzle tăng rất nhanh.
        # Giữ giới hạn hợp lý để tránh treo GUI/máy.
        return max(1, min(value, 40))

    def shuffle_current_problem(self) -> None:
        self.stop_animation()

        if self.mode_var.get() == "8-PUZZLE":
            self.puzzle_state = PuzzleProblem.random_state(shuffle_steps=10)
            self.update_status("Puzzle shuffled. Because it is shuffled from GOAL, it is solvable.")
        else:
            self.vacuum_state = VacuumProblem.random_state()
            self.vacuum_initial_dirt = max(1, VacuumProblem.dirty_count(self.vacuum_state))
            self.update_status("Vacuum map randomized.")

        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()

    def reset_current_problem(self) -> None:
        self.stop_animation()

        if self.mode_var.get() == "8-PUZZLE":
            self.puzzle_state = PuzzleProblem.START
        else:
            self.vacuum_state = VacuumProblem.start_state()
            self.vacuum_initial_dirt = max(1, VacuumProblem.dirty_count(self.vacuum_state))

        self.search_result = None
        self.solution_path = []
        self.current_step = 0
        self.clear_trace_table()
        self.draw_board()
        self.update_status("Reset current problem.")
