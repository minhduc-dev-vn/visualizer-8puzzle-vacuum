from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Literal, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace


@dataclass(frozen=True)
class NeighborCandidate:
    node: SearchNode
    score: int


def _manhattan_if_puzzle(state: object) -> int | None:
    if not isinstance(state, tuple) or len(state) != 9:
        return None
    if not all(isinstance(value, int) for value in state):
        return None

    distance = 0
    for index, value in enumerate(state):
        if value == 0:
            continue
        target_index = value - 1
        row, col = divmod(index, 3)
        target_row, target_col = divmod(target_index, 3)
        distance += abs(row - target_row) + abs(col - target_col)

    return distance


def _vacuum_local_score(state: object) -> int | None:
    if not isinstance(state, tuple) or len(state) != 2:
        return None

    position, grid = state
    if not (
        isinstance(position, tuple)
        and len(position) == 2
        and isinstance(position[0], int)
        and isinstance(position[1], int)
        and isinstance(grid, tuple)
    ):
        return None

    robot_row, robot_col = position
    dirty_cells: List[Tuple[int, int]] = []

    for row_index, row in enumerate(grid):
        if not isinstance(row, tuple):
            return None
        for col_index, cell in enumerate(row):
            if cell == 1:
                dirty_cells.append((row_index, col_index))

    dirty_count = len(dirty_cells)
    if dirty_count == 0:
        return 0

    nearest_distance = min(abs(robot_row - row) + abs(robot_col - col) for row, col in dirty_cells)

    # Keep dirty count dominant; nearest distance guides movement toward dirt.
    return dirty_count * 10 + nearest_distance


def _local_score(state: object) -> int:
    puzzle_score = _manhattan_if_puzzle(state)
    if puzzle_score is not None:
        return puzzle_score

    vacuum_score = _vacuum_local_score(state)
    if vacuum_score is not None:
        return vacuum_score

    return 0


def _align_trace_with_path(
    path: List[SearchNode],
    trace: List[TraceEntry],
    trace_by_state: dict,
) -> dict:
    if not path:
        return trace_by_state

    needed_states = {node.state for node in path}
    latest_for_path = {}

    for entry in reversed(trace):
        if entry.state in needed_states and entry.state not in latest_for_path:
            latest_for_path[entry.state] = entry
            if len(latest_for_path) == len(needed_states):
                break

    merged = dict(trace_by_state)
    merged.update(latest_for_path)
    return merged


def _pick_candidate(
    *,
    strategy: Literal["simple", "steepest", "stochastic"],
    candidates: List[NeighborCandidate],
    current_score: int,
    rng: random.Random,
) -> NeighborCandidate | None:
    improving = [candidate for candidate in candidates if candidate.score < current_score]
    if not improving:
        return None

    if strategy == "simple":
        for candidate in candidates:
            if candidate.score < current_score:
                return candidate
        return None

    if strategy == "steepest":
        return min(improving, key=lambda candidate: candidate.score)

    return rng.choice(improving)


def _hill_climbing(
    *,
    strategy: Literal["simple", "steepest", "stochastic"],
    strategy_name: str,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
) -> SearchResult:
    root = SearchNode(start_state, parent=None, action="START", depth=0)
    current = root
    current_score = _local_score(start_state)

    reached_set = {start_state}
    reached_order = [start_state]

    trace: List[TraceEntry] = []
    trace_by_state = {}
    expansions = 0

    if is_goal(start_state):
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=root,
            frontier=[root],
            reached_order=reached_order,
            formatter=formatter,
            note=f"START is goal ({strategy_name})",
        )
        return SearchResult(True, root.path(), trace, trace_by_state, "Start is already goal.", expansions)

    rng = random.Random()

    while expansions < max_expansions:
        expansions += 1

        successors = list(get_successors(current.state))
        candidates: List[NeighborCandidate] = []

        for action, child_state in successors:
            child = SearchNode(
                state=child_state,
                parent=current,
                action=action,
                depth=current.depth + 1,
            )
            candidate = NeighborCandidate(node=child, score=_local_score(child_state))
            candidates.append(candidate)

            if child_state not in reached_set:
                reached_set.add(child_state)
                reached_order.append(child_state)

        chosen = _pick_candidate(
            strategy=strategy,
            candidates=candidates,
            current_score=current_score,
            rng=rng,
        )

        if chosen is None:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=[candidate.node for candidate in candidates],
                reached_order=reached_order,
                formatter=formatter,
                note=f"Stopped at local optimum/plateau ({strategy_name}), score={current_score}",
            )
            return SearchResult(
                False,
                current.path(),
                trace,
                _align_trace_with_path(current.path(), trace, trace_by_state),
                f"{strategy_name} stopped at local optimum (score={current_score}).",
                expansions,
            )

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=current,
            frontier=[candidate.node for candidate in candidates],
            reached_order=reached_order,
            formatter=formatter,
            note=(
                f"{strategy_name}: chose action {chosen.node.action} "
                f"(score {current_score} -> {chosen.score})"
            ),
        )

        current = chosen.node
        current_score = chosen.score

        if is_goal(current.state):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note=f"GOAL reached by {strategy_name} (score={current_score})",
            )
            path = current.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                f"Goal found by {strategy_name}.",
                expansions,
            )

    found = is_goal(current.state)
    path = current.path()

    return SearchResult(
        found,
        path if found else current.path(),
        trace,
        _align_trace_with_path(path, trace, trace_by_state),
        (
            f"{strategy_name} reached max_expansions={max_expansions}."
            if not found
            else f"Goal found by {strategy_name}."
        ),
        expansions,
    )


def search_simple(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    _ = max_depth
    return _hill_climbing(
        strategy="simple",
        strategy_name="Simple Hill Climbing",
        start_state=start_state,
        is_goal=is_goal,
        get_successors=get_successors,
        formatter=formatter,
        max_expansions=max_expansions,
    )


def search_steepest(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    _ = max_depth
    return _hill_climbing(
        strategy="steepest",
        strategy_name="Steepest Ascent Hill Climbing",
        start_state=start_state,
        is_goal=is_goal,
        get_successors=get_successors,
        formatter=formatter,
        max_expansions=max_expansions,
    )


def search_stochastic(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    _ = max_depth
    return _hill_climbing(
        strategy="stochastic",
        strategy_name="Stochastic Hill Climbing",
        start_state=start_state,
        is_goal=is_goal,
        get_successors=get_successors,
        formatter=formatter,
        max_expansions=max_expansions,
    )

