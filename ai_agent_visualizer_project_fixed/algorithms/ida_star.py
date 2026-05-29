from __future__ import annotations

import math
from typing import Callable, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace


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


def _dirty_cells_if_vacuum(state: object) -> int | None:
    if not isinstance(state, tuple) or len(state) != 2:
        return None

    _, grid = state
    if not isinstance(grid, tuple):
        return None

    dirty = 0
    for row in grid:
        if not isinstance(row, tuple):
            return None
        for cell in row:
            if cell == 1:
                dirty += 1

    return dirty


def _heuristic(state: object) -> int:
    puzzle_h = _manhattan_if_puzzle(state)
    if puzzle_h is not None:
        return puzzle_h

    vacuum_h = _dirty_cells_if_vacuum(state)
    if vacuum_h is not None:
        return vacuum_h

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
    Iterative Deepening A* (IDA*).

    - Uses iterative f-thresholds where f(n)=g(n)+h(n).
    - Uses depth-first contour search for each threshold.
    - Includes optional max_depth to keep runs bounded in GUI.
    """
    if max_depth is None:
        max_depth = 20

    root = SearchNode(start_state, parent=None, action="START", depth=0)
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
            note="START is goal",
        )
        return SearchResult(True, root.path(), trace, trace_by_state, "Start is already goal.", expansions)

    threshold = _heuristic(start_state)
    iteration = 0

    while expansions < max_expansions:
        found_node: SearchNode | None = None
        next_threshold = math.inf

        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=root,
            frontier=[root],
            reached_order=reached_order,
            formatter=formatter,
            note=f"Starting IDA* iteration={iteration}, threshold={threshold}",
        )

        def dfs(
            node: SearchNode,
            g_score: int,
            path_nodes: List[SearchNode],
            path_states: set,
        ) -> float:
            nonlocal expansions, next_threshold, found_node

            h_score = _heuristic(node.state)
            f_score = g_score + h_score

            if f_score > threshold:
                next_threshold = min(next_threshold, f_score)
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=list(path_nodes),
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"IDA* cutoff: f={f_score} > threshold={threshold}",
                )
                return f_score

            if expansions >= max_expansions or found_node is not None:
                return math.inf

            expansions += 1

            if is_goal(node.state):
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=list(path_nodes),
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"GOAL found by IDA* (g={g_score}, h={h_score}, f={f_score})",
                )
                found_node = node
                return f_score

            if node.depth >= max_depth:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=list(path_nodes),
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"Depth limit reached: depth={node.depth}, max_depth={max_depth}",
                )
                return math.inf

            min_exceeded = math.inf
            expanded_any = False

            for action, child_state in get_successors(node.state):
                if child_state in path_states:
                    continue

                expanded_any = True
                child = SearchNode(
                    state=child_state,
                    parent=node,
                    action=action,
                    depth=node.depth + 1,
                )

                if child_state not in reached_set:
                    reached_set.add(child_state)
                    reached_order.append(child_state)

                path_nodes.append(child)
                path_states.add(child_state)

                result = dfs(child, g_score + 1, path_nodes, path_states)

                path_states.remove(child_state)
                path_nodes.pop()

                if found_node is not None or expansions >= max_expansions:
                    return result

                if result < min_exceeded:
                    min_exceeded = result

            if expanded_any:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=list(path_nodes),
                    reached_order=reached_order,
                    formatter=formatter,
                    note=f"Expanded by IDA* under threshold={threshold}",
                )
            else:
                append_trace(
                    trace=trace,
                    trace_by_state=trace_by_state,
                    node=node,
                    frontier=list(path_nodes),
                    reached_order=reached_order,
                    formatter=formatter,
                    note="Dead end (all successors were in current DFS path).",
                )

            return min_exceeded

        dfs(root, 0, [root], {start_state})

        if found_node is not None:
            path = found_node.path()
            return SearchResult(
                True,
                path,
                trace,
                _align_trace_with_path(path, trace, trace_by_state),
                f"Goal found by IDA* at depth={found_node.depth}.",
                expansions,
            )

        if expansions >= max_expansions:
            break

        if next_threshold == math.inf:
            return SearchResult(
                False,
                [],
                trace,
                trace_by_state,
                f"No solution found within max_depth={max_depth}.",
                expansions,
            )

        threshold = int(next_threshold)
        iteration += 1

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No solution within max_expansions={max_expansions}, max_depth={max_depth}.",
        expansions,
    )

