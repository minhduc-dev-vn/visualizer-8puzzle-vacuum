from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace


@dataclass(frozen=True)
class AnnealingCandidate:
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


def _acceptance_probability(delta: int, temperature: float) -> float:
    if delta < 0:
        return 1.0
    if temperature <= 0:
        return 0.0

    return math.exp(-delta / temperature)


def search(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    """
    Simulated Annealing local search.

    - current state = start
    - T = T0, lay tu o "Depth / HC parameter" tren UI neu co
    - lap khi T > Tmin va chua vuot max_expansions
    - neu neighbor tot hon thi nhan, neu xau hon thi nhan theo exp(-delta / T)
    """
    initial_temperature = float(max_depth or 12)
    minimum_temperature = 0.001
    cooling_rate = 0.995

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    current = root
    current_score = _local_score(start_state)

    reached_set = {start_state}
    reached_order = [start_state]

    trace: List[TraceEntry] = []
    trace_by_state = {}
    expansions = 0

    best_node = root
    best_score = current_score

    if is_goal(start_state):
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=root,
            frontier=[root],
            reached_order=reached_order,
            formatter=formatter,
            note="START is goal (Simulated Annealing)",
        )
        return SearchResult(True, root.path(), trace, trace_by_state, "Start is already goal.", expansions)

    rng = random.Random()
    temperature = initial_temperature

    while temperature > minimum_temperature and expansions < max_expansions:
        if is_goal(current.state):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note=f"GOAL reached by Simulated Annealing (score={current_score}, T={temperature:.4f})",
            )
            path = current.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                "Goal found by Simulated Annealing.",
                expansions,
            )

        expansions += 1
        candidates: List[AnnealingCandidate] = []

        for action, child_state in get_successors(current.state):
            child = SearchNode(
                state=child_state,
                parent=current,
                action=action,
                depth=current.depth + 1,
            )
            candidate = AnnealingCandidate(node=child, score=_local_score(child_state))
            candidates.append(candidate)

            if child_state not in reached_set:
                reached_set.add(child_state)
                reached_order.append(child_state)

        if not candidates:
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=[],
                reached_order=reached_order,
                formatter=formatter,
                note="Stopped: current state has no random neighbor.",
            )
            break

        chosen = rng.choice(candidates)
        delta = chosen.score - current_score
        probability = _acceptance_probability(delta, temperature)
        roll = rng.random()
        accepted = delta < 0 or roll < probability

        if accepted:
            decision = "accepted better neighbor" if delta < 0 else "accepted worse/equal neighbor by probability"
        else:
            decision = "rejected worse neighbor"

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=current,
            frontier=[candidate.node for candidate in candidates],
            reached_order=reached_order,
            formatter=formatter,
            note=(
                f"SA chose {chosen.node.action}: score {current_score}->{chosen.score}, "
                f"delta={delta}, T={temperature:.4f}, p={probability:.4f}, "
                f"random={roll:.4f}; {decision}"
            ),
        )

        if accepted:
            current = chosen.node
            current_score = chosen.score

            if current_score < best_score:
                best_node = current
                best_score = current_score

        temperature *= cooling_rate

    if is_goal(current.state):
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=current,
            frontier=[],
            reached_order=reached_order,
            formatter=formatter,
            note=f"GOAL reached by Simulated Annealing (score={current_score})",
        )
        path = current.path()
        return SearchResult(
            True,
            path,
            trace,
            _align_trace_with_path(path, trace, trace_by_state),
            "Goal found by Simulated Annealing.",
            expansions,
        )

    best_path = best_node.path()
    stop_reason = (
        f"temperature cooled to Tmin={minimum_temperature}"
        if temperature <= minimum_temperature
        else f"max_expansions={max_expansions}"
    )

    return SearchResult(
        False,
        best_path,
        trace,
        _align_trace_with_path(best_path, trace, trace_by_state),
        f"Simulated Annealing stopped by {stop_reason}; best score={best_score}.",
        expansions,
    )
