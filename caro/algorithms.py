# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from math import inf
from time import perf_counter
from typing import Callable, Dict, Optional

from game import (
    AI,
    DRAW,
    WIN_SCORE,
    Board,
    Move,
    evaluate_board,
    generate_candidate_moves,
    get_winner,
    opponent,
    place_move,
    undo_move,
)


@dataclass
class SearchResult:
    algorithm: str
    move: Optional[Move]
    score: float
    nodes: int
    depth: int
    elapsed: float
    pruned: int = 0


def _terminal_score(board: Board, ai_player: str, depth_left: int) -> Optional[int]:
    winner = get_winner(board)
    if winner is None:
        return None
    if winner == ai_player:
        return WIN_SCORE + depth_left * 1_000
    if winner == opponent(ai_player):
        return -WIN_SCORE - depth_left * 1_000
    if winner == DRAW:
        return 0
    return None


def minimax_decision(
    board: Board,
    ai_player: str = AI,
    depth: int = 2,
    candidate_limit: int = 10,
) -> SearchResult:
    started = perf_counter()
    nodes = 0

    def search(depth_left: int, current_player: str) -> float:
        nonlocal nodes
        nodes += 1

        terminal = _terminal_score(board, ai_player, depth_left)
        if terminal is not None:
            return terminal
        if depth_left == 0:
            return evaluate_board(board, ai_player)

        moves = generate_candidate_moves(board, current_player, limit=candidate_limit)
        if not moves:
            return evaluate_board(board, ai_player)

        if current_player == ai_player:
            best = -inf
            for move in moves:
                place_move(board, move, current_player)
                best = max(best, search(depth_left - 1, opponent(current_player)))
                undo_move(board, move)
            return best

        best = inf
        for move in moves:
            place_move(board, move, current_player)
            best = min(best, search(depth_left - 1, opponent(current_player)))
            undo_move(board, move)
        return best

    best_move: Optional[Move] = None
    best_score = -inf
    for move in generate_candidate_moves(board, ai_player, limit=candidate_limit):
        place_move(board, move, ai_player)
        score = search(depth - 1, opponent(ai_player))
        undo_move(board, move)
        if score > best_score:
            best_score = score
            best_move = move

    return SearchResult(
        algorithm="Minimax",
        move=best_move,
        score=best_score,
        nodes=nodes,
        depth=depth,
        elapsed=perf_counter() - started,
    )


def alphabeta_decision(
    board: Board,
    ai_player: str = AI,
    depth: int = 3,
    candidate_limit: int = 12,
) -> SearchResult:
    started = perf_counter()
    nodes = 0
    pruned = 0

    def search(depth_left: int, current_player: str, alpha: float, beta: float) -> float:
        nonlocal nodes, pruned
        nodes += 1

        terminal = _terminal_score(board, ai_player, depth_left)
        if terminal is not None:
            return terminal
        if depth_left == 0:
            return evaluate_board(board, ai_player)

        moves = generate_candidate_moves(board, current_player, limit=candidate_limit)
        if not moves:
            return evaluate_board(board, ai_player)

        if current_player == ai_player:
            value = -inf
            for index, move in enumerate(moves):
                place_move(board, move, current_player)
                value = max(value, search(depth_left - 1, opponent(current_player), alpha, beta))
                undo_move(board, move)
                alpha = max(alpha, value)
                if alpha >= beta:
                    pruned += len(moves) - index - 1
                    break
            return value

        value = inf
        for index, move in enumerate(moves):
            place_move(board, move, current_player)
            value = min(value, search(depth_left - 1, opponent(current_player), alpha, beta))
            undo_move(board, move)
            beta = min(beta, value)
            if alpha >= beta:
                pruned += len(moves) - index - 1
                break
        return value

    best_move: Optional[Move] = None
    best_score = -inf
    alpha = -inf
    beta = inf
    for move in generate_candidate_moves(board, ai_player, limit=candidate_limit):
        place_move(board, move, ai_player)
        score = search(depth - 1, opponent(ai_player), alpha, beta)
        undo_move(board, move)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, best_score)

    return SearchResult(
        algorithm="Alpha-Beta",
        move=best_move,
        score=best_score,
        nodes=nodes,
        depth=depth,
        elapsed=perf_counter() - started,
        pruned=pruned,
    )


def expectimax_decision(
    board: Board,
    ai_player: str = AI,
    depth: int = 2,
    candidate_limit: int = 8,
) -> SearchResult:
    started = perf_counter()
    nodes = 0

    def search(depth_left: int, current_player: str) -> float:
        nonlocal nodes
        nodes += 1

        terminal = _terminal_score(board, ai_player, depth_left)
        if terminal is not None:
            return terminal
        if depth_left == 0:
            return evaluate_board(board, ai_player)

        moves = generate_candidate_moves(board, current_player, limit=candidate_limit)
        if not moves:
            return evaluate_board(board, ai_player)

        if current_player == ai_player:
            value = -inf
            for move in moves:
                place_move(board, move, current_player)
                value = max(value, search(depth_left - 1, opponent(current_player)))
                undo_move(board, move)
            return value

        total = 0.0
        for move in moves:
            place_move(board, move, current_player)
            total += search(depth_left - 1, opponent(current_player))
            undo_move(board, move)
        return total / len(moves)

    best_move: Optional[Move] = None
    best_score = -inf
    for move in generate_candidate_moves(board, ai_player, limit=candidate_limit):
        place_move(board, move, ai_player)
        score = search(depth - 1, opponent(ai_player))
        undo_move(board, move)
        if score > best_score:
            best_score = score
            best_move = move

    return SearchResult(
        algorithm="Expectimax",
        move=best_move,
        score=best_score,
        nodes=nodes,
        depth=depth,
        elapsed=perf_counter() - started,
    )


ALGORITHMS: Dict[str, Callable[[Board, str, int, int], SearchResult]] = {
    "Minimax": minimax_decision,
    "Alpha-Beta": alphabeta_decision,
    "Expectimax": expectimax_decision,
}
