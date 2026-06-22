# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Set, Tuple

EMPTY = "."
HUMAN = "X"
AI = "O"
DRAW = "DRAW"

BOARD_SIZE = 15
WIN_LENGTH = 5
DIRECTIONS: Tuple[Tuple[int, int], ...] = (
    (1, 0),
    (0, 1),
    (1, 1),
    (1, -1),
)

Board = List[List[str]]
Move = Tuple[int, int]

WIN_SCORE = 1_000_000_000


def create_board(size: int = BOARD_SIZE) -> Board:
    return [[EMPTY for _ in range(size)] for _ in range(size)]


def clone_board(board: Board) -> Board:
    return [row[:] for row in board]


def opponent(player: str) -> str:
    return HUMAN if player == AI else AI


def in_bounds(row: int, col: int, size: int) -> bool:
    return 0 <= row < size and 0 <= col < size


def is_full(board: Board) -> bool:
    return all(cell != EMPTY for row in board for cell in row)


def place_move(board: Board, move: Move, player: str) -> None:
    row, col = move
    board[row][col] = player


def undo_move(board: Board, move: Move) -> None:
    row, col = move
    board[row][col] = EMPTY


def get_winner(board: Board, win_length: int = WIN_LENGTH) -> Optional[str]:
    size = len(board)
    for row in range(size):
        for col in range(size):
            player = board[row][col]
            if player == EMPTY:
                continue

            for d_row, d_col in DIRECTIONS:
                prev_row = row - d_row
                prev_col = col - d_col
                if in_bounds(prev_row, prev_col, size) and board[prev_row][prev_col] == player:
                    continue

                count = 0
                cur_row = row
                cur_col = col
                while in_bounds(cur_row, cur_col, size) and board[cur_row][cur_col] == player:
                    count += 1
                    if count >= win_length:
                        return player
                    cur_row += d_row
                    cur_col += d_col

    return DRAW if is_full(board) else None


def _iter_windows(board: Board, length: int = WIN_LENGTH) -> Iterable[List[str]]:
    size = len(board)
    for row in range(size):
        for col in range(size):
            for d_row, d_col in DIRECTIONS:
                end_row = row + (length - 1) * d_row
                end_col = col + (length - 1) * d_col
                if not in_bounds(end_row, end_col, size):
                    continue
                yield [board[row + i * d_row][col + i * d_col] for i in range(length)]


def evaluate_board(board: Board, player: str = AI) -> int:
    winner = get_winner(board)
    enemy = opponent(player)
    if winner == player:
        return WIN_SCORE
    if winner == enemy:
        return -WIN_SCORE
    if winner == DRAW:
        return 0

    attack_weights = {1: 2, 2: 15, 3: 160, 4: 3_500, 5: WIN_SCORE}
    defense_weights = {1: 2, 2: 20, 3: 220, 4: 4_500, 5: WIN_SCORE}

    score = 0
    for window in _iter_windows(board):
        own_count = window.count(player)
        enemy_count = window.count(enemy)
        if own_count and enemy_count:
            continue
        if own_count:
            score += attack_weights[own_count]
        elif enemy_count:
            score -= defense_weights[enemy_count]

    center = (len(board) - 1) / 2
    for row, cells in enumerate(board):
        for col, cell in enumerate(cells):
            if cell == EMPTY:
                continue
            center_bonus = int(14 - abs(row - center) - abs(col - center))
            if cell == player:
                score += center_bonus
            else:
                score -= center_bonus

    return score


def _occupied_cells(board: Board) -> List[Move]:
    cells: List[Move] = []
    for row, line in enumerate(board):
        for col, cell in enumerate(line):
            if cell != EMPTY:
                cells.append((row, col))
    return cells


def _empty_cells(board: Board) -> List[Move]:
    cells: List[Move] = []
    for row, line in enumerate(board):
        for col, cell in enumerate(line):
            if cell == EMPTY:
                cells.append((row, col))
    return cells


def _move_priority(board: Board, move: Move, player: str) -> int:
    row, col = move
    enemy = opponent(player)
    size = len(board)
    center = (size - 1) / 2
    center_bonus = int(50 - 4 * (abs(row - center) + abs(col - center)))

    place_move(board, move, player)
    if get_winner(board) == player:
        own_score = WIN_SCORE
    else:
        own_score = evaluate_board(board, player)
    undo_move(board, move)

    place_move(board, move, enemy)
    block_score = WIN_SCORE // 2 if get_winner(board) == enemy else 0
    undo_move(board, move)

    return own_score + block_score + center_bonus


def generate_candidate_moves(
    board: Board,
    player: str = AI,
    radius: int = 2,
    limit: Optional[int] = 12,
) -> List[Move]:
    size = len(board)
    occupied = _occupied_cells(board)
    if not occupied:
        center = size // 2
        return [(center, center)]

    candidates: Set[Move] = set()
    for row, col in occupied:
        for d_row in range(-radius, radius + 1):
            for d_col in range(-radius, radius + 1):
                new_row = row + d_row
                new_col = col + d_col
                if in_bounds(new_row, new_col, size) and board[new_row][new_col] == EMPTY:
                    candidates.add((new_row, new_col))

    moves = list(candidates) or _empty_cells(board)
    moves.sort(key=lambda move: _move_priority(board, move, player), reverse=True)
    return moves[:limit] if limit is not None else moves


def move_to_text(move: Optional[Move]) -> str:
    if move is None:
        return "-"
    row, col = move
    return f"({row + 1}, {col + 1})"
