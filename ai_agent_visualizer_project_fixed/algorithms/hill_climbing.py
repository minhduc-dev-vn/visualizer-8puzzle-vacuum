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


def _random_walk_node(
    *,
    start_node: SearchNode,
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    rng: random.Random,
    steps: int,
) -> SearchNode:
    current = start_node
    path_states = {start_node.state}

    for _ in range(steps):
        successors = list(get_successors(current.state))
        if not successors:
            break

        fresh_successors = [
            (action, child_state)
            for action, child_state in successors
            if child_state not in path_states
        ]
        action, child_state = rng.choice(fresh_successors or successors)
        current = SearchNode(
            state=child_state,
            parent=current,
            action=action,
            depth=current.depth + 1,
        )
        path_states.add(child_state)

    return current


def search_random_restart(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    restart_count = max(1, max_depth or 12)
    root = SearchNode(start_state, parent=None, action="START", depth=0)
    rng = random.Random()

    reached_set = {start_state}
    reached_order = [start_state]

    trace: List[TraceEntry] = []
    trace_by_state = {}
    expansions = 0

    best_node = root
    best_score = _local_score(start_state)

    for restart_index in range(restart_count):
        if expansions >= max_expansions:
            break

        if restart_index == 0:
            current = root
        else:
            walk_steps = min(10, 2 + restart_index)
            current = _random_walk_node(
                start_node=root,
                get_successors=get_successors,
                rng=rng,
                steps=walk_steps,
            )
            for node in current.path():
                if node.state not in reached_set:
                    reached_set.add(node.state)
                    reached_order.append(node.state)

        current_score = _local_score(current.state)
        if current_score < best_score:
            best_node = current
            best_score = current_score

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=current,
            frontier=[current],
            reached_order=reached_order,
            formatter=formatter,
            note=(
                f"Random Restart HC: start restart {restart_index + 1}/{restart_count}, "
                f"score={current_score}"
            ),
        )

        if is_goal(current.state):
            path = current.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                f"Goal found by Random Restart Hill Climbing at restart {restart_index + 1}.",
                expansions,
            )

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
                strategy="steepest",
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
                    note=(
                        f"Restart {restart_index + 1} stuck at local optimum/plateau, "
                        f"score={current_score}; moving to next restart"
                    ),
                )
                break

            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=current,
                frontier=[candidate.node for candidate in candidates],
                reached_order=reached_order,
                formatter=formatter,
                note=(
                    f"Random Restart HC restart {restart_index + 1}: chose {chosen.node.action} "
                    f"(score {current_score} -> {chosen.score})"
                ),
            )

            current = chosen.node
            current_score = chosen.score

            if current_score < best_score:
                best_node = current
                best_score = current_score

            if is_goal(current.state):
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=current,
                    frontier=[],
                    reached_order=reached_order,
                    formatter=formatter,
                    note=(
                        f"GOAL reached by Random Restart HC at restart {restart_index + 1}, "
                        f"score={current_score}"
                    ),
                )
                path = current.path()
                return SearchResult(
                    True,
                    path,
                    trace,
                    _align_trace_with_path(path, trace, trace_by_state),
                    f"Goal found by Random Restart Hill Climbing at restart {restart_index + 1}.",
                    expansions,
                )

    return SearchResult(
        False,
        best_node.path(),
        trace,
        _align_trace_with_path(best_node.path(), trace, trace_by_state),
        (
            f"Random Restart Hill Climbing failed after {restart_count} restarts "
            f"or max_expansions={max_expansions}; best score={best_score}."
        ),
        expansions,
    )


def search_local_beam(
    *,
    start_state: object,
    is_goal: Callable[[object], bool],
    get_successors: Callable[[object], Iterable[Tuple[str, object]]],
    formatter: StateFormatter,
    max_expansions: int,
    max_depth: int | None = None,
) -> SearchResult:
    beam_width = max(1, min(max_depth or 3, 20))
    root = SearchNode(start_state, parent=None, action="START", depth=0)
    rng = random.Random()

    current_nodes = [root]
    seen_initial_states = {start_state}

    for index in range(1, beam_width):
        random_node = _random_walk_node(
            start_node=root,
            get_successors=get_successors,
            rng=rng,
            steps=min(10, index + 1),
        )
        if random_node.state in seen_initial_states:
            continue
        seen_initial_states.add(random_node.state)
        current_nodes.append(random_node)

    reached_set = set()
    reached_order: List[object] = []
    for node in current_nodes:
        for path_node in node.path():
            if path_node.state not in reached_set:
                reached_set.add(path_node.state)
                reached_order.append(path_node.state)

    trace: List[TraceEntry] = []
    trace_by_state = {}
    expansions = 0

    for node in current_nodes:
        if is_goal(node.state):
            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=current_nodes,
                reached_order=reached_order,
                formatter=formatter,
                note=f"GOAL found in initial Local Beam set (k={beam_width})",
            )
            path = node.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                "Goal found by Local Beam Search in initial beam.",
                expansions,
            )

    while current_nodes and expansions < max_expansions:
        neighbor_by_state = {}

        for node in current_nodes:
            if expansions >= max_expansions:
                break

            expansions += 1
            local_candidates: List[NeighborCandidate] = []

            for action, child_state in get_successors(node.state):
                child = SearchNode(
                    state=child_state,
                    parent=node,
                    action=action,
                    depth=node.depth + 1,
                )
                candidate = NeighborCandidate(node=child, score=_local_score(child_state))
                local_candidates.append(candidate)

                existing = neighbor_by_state.get(child_state)
                if existing is None or candidate.score < existing.score:
                    neighbor_by_state[child_state] = candidate

                if child_state not in reached_set:
                    reached_set.add(child_state)
                    reached_order.append(child_state)

                if is_goal(child_state):
                    append_trace(
                        trace=trace,
                        trace_by_state=trace_by_state,
                        node=child,
                        frontier=[candidate.node for candidate in local_candidates],
                        reached_order=reached_order,
                        formatter=formatter,
                        note=f"GOAL generated by Local Beam Search (k={beam_width})",
                    )
                    path = child.path()
                    return SearchResult(
                        True,
                        path,
                        trace,
                        _align_trace_with_path(path, trace, trace_by_state),
                        "Goal found by Local Beam Search.",
                        expansions,
                    )

            append_trace(
                trace=trace,
                trace_by_state=trace_by_state,
                node=node,
                frontier=[candidate.node for candidate in local_candidates],
                reached_order=reached_order,
                formatter=formatter,
                note=(
                    f"Local Beam Search(k={beam_width}): generated "
                    f"{len(local_candidates)} neighbors from this beam state"
                ),
            )

        candidates = sorted(neighbor_by_state.values(), key=lambda candidate: candidate.score)
        if not candidates:
            break

        next_nodes = [candidate.node for candidate in candidates[:beam_width]]
        best_score = candidates[0].score

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=next_nodes[0],
            frontier=next_nodes,
            reached_order=reached_order,
            formatter=formatter,
            note=(
                f"Local Beam Search(k={beam_width}): selected best {len(next_nodes)} "
                f"states for next beam, best score={best_score}"
            ),
        )

        current_nodes = next_nodes

    best_node = min(current_nodes, key=lambda node: _local_score(node.state)) if current_nodes else root
    best_score = _local_score(best_node.state)

    return SearchResult(
        False,
        best_node.path(),
        trace,
        _align_trace_with_path(best_node.path(), trace, trace_by_state),
        f"Local Beam Search(k={beam_width}) reached max_expansions={max_expansions}; best score={best_score}.",
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
