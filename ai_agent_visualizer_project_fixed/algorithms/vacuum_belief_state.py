from __future__ import annotations

from collections import deque
from typing import Callable, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry
from problems.vacuum import Position, VacuumGrid, VacuumState


BeliefState = frozenset[VacuumState]


ACTIONS: Tuple[Tuple[str, int, int], ...] = (
    ("SUCK", 0, 0),
    ("UP", -1, 0),
    ("DOWN", 1, 0),
    ("LEFT", 0, -1),
    ("RIGHT", 0, 1),
)


def _free_cells(grid: VacuumGrid) -> List[Position]:
    return [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[row]))
        if grid[row][col] != -1
    ]


def _grid_with_dirt(obstacle_grid: VacuumGrid, dirty_cells: set[Position]) -> VacuumGrid:
    rows = []
    for row_index, row in enumerate(obstacle_grid):
        values = []
        for col_index, value in enumerate(row):
            if value == -1:
                values.append(-1)
            elif (row_index, col_index) in dirty_cells:
                values.append(1)
            else:
                values.append(0)
        rows.append(tuple(values))
    return tuple(rows)


def _initial_belief(start_state: VacuumState) -> BeliefState:
    """
    Sensorless/conformant vacuum belief.

    The agent knows its position and obstacle layout, but every free cell may or
    may not contain dirt. The search must find one action sequence that cleans
    every world still possible in this belief set.
    """
    start_pos, grid = start_state
    free_cells = _free_cells(grid)
    states = []

    for mask in range(1 << len(free_cells)):
        dirty_cells = {
            cell
            for index, cell in enumerate(free_cells)
            if mask & (1 << index)
        }
        states.append((start_pos, _grid_with_dirt(grid, dirty_cells)))

    return frozenset(states)


def _all_dirty_representative(start_state: VacuumState) -> VacuumState:
    start_pos, grid = start_state
    return start_pos, _grid_with_dirt(grid, set(_free_cells(grid)))


def _dirty_cells(state: VacuumState) -> set[Position]:
    _, grid = state
    return {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[row]))
        if grid[row][col] == 1
    }


def _belief_dirty_union(belief: BeliefState) -> set[Position]:
    possible_dirty: set[Position] = set()
    for state in belief:
        possible_dirty.update(_dirty_cells(state))
    return possible_dirty


def _is_belief_goal(belief: BeliefState) -> bool:
    return all(not _dirty_cells(state) for state in belief)


def _apply_action(state: VacuumState, action: str) -> VacuumState | None:
    (row, col), grid = state

    if action == "SUCK":
        if grid[row][col] != 1:
            return state

        new_grid = [list(item) for item in grid]
        new_grid[row][col] = 0
        return (row, col), tuple(tuple(item) for item in new_grid)

    for candidate_action, dr, dc in ACTIONS:
        if action != candidate_action:
            continue

        nr, nc = row + dr, col + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[nr]) and grid[nr][nc] != -1:
            return (nr, nc), grid
        return None

    return None


def _belief_successors(belief: BeliefState) -> List[Tuple[str, BeliefState]]:
    result: List[Tuple[str, BeliefState]] = []

    for action, _, _ in ACTIONS:
        next_states = []
        valid_for_all_worlds = True

        for state in belief:
            next_state = _apply_action(state, action)
            if next_state is None:
                valid_for_all_worlds = False
                break
            next_states.append(next_state)

        if valid_for_all_worlds:
            result.append((action, frozenset(next_states)))

    return result


def _format_belief(belief: BeliefState) -> str:
    if not belief:
        return "Belief(size=0)"

    positions = sorted({state[0] for state in belief})
    possible_dirty = sorted(_belief_dirty_union(belief))
    dirty_text = ",".join(f"({row},{col})" for row, col in possible_dirty) or "none"
    pos_text = ",".join(f"({row},{col})" for row, col in positions)
    return f"Belief(size={len(belief)}, pos={pos_text}, possible_dirty={dirty_text})"


def _beliefs_text(beliefs: List[BeliefState], limit: int = 12) -> str:
    shown = beliefs[:limit]
    text = "  |  ".join(_format_belief(belief) for belief in shown)
    if len(beliefs) > limit:
        text += f"  |  ... {len(beliefs) - limit} more belief states"
    return text


def _representative_after_action(state: VacuumState, action: str) -> VacuumState:
    next_state = _apply_action(state, action)
    return state if next_state is None else next_state


def _make_trace(
    *,
    trace_step: int,
    concrete_state: VacuumState,
    action: str,
    depth: int,
    current_belief: BeliefState,
    frontier: Iterable[BeliefState],
    reached_order: Iterable[BeliefState],
    note: str,
) -> TraceEntry:
    reached_list = list(reached_order)
    frontier_list = list(frontier)
    return TraceEntry(
        trace_step=trace_step,
        state=concrete_state,
        action=action,
        depth=depth,
        current_text=_format_belief(current_belief),
        frontier_count=len(frontier_list),
        frontier_text=_beliefs_text(frontier_list),
        reached_count=len(reached_list),
        reached_text=_beliefs_text(reached_list),
        note=note,
    )


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
    Belief-state BFS for sensorless Vacuum World.

    This algorithm is intentionally Vacuum-specific. It keeps the original
    concrete VacuumState path only for UI animation, while the trace table shows
    the actual belief states explored by BFS.
    """
    _ = is_goal, get_successors, formatter
    if max_depth is None:
        max_depth = 30

    concrete_start = start_state  # type: ignore[assignment]
    start_belief = _initial_belief(concrete_start)
    representative_start = _all_dirty_representative(concrete_start)
    root = SearchNode(representative_start, parent=None, action="START", depth=0)

    frontier = deque([(start_belief, root)])
    frontier_beliefs = deque([start_belief])
    reached_set = {start_belief}
    reached_order = [start_belief]

    trace: List[TraceEntry] = []
    trace_by_state = {}
    expansions = 0

    while frontier and expansions < max_expansions:
        belief, concrete_node = frontier.popleft()
        frontier_beliefs.popleft()
        expansions += 1

        if _is_belief_goal(belief):
            entry = _make_trace(
                trace_step=len(trace),
                concrete_state=concrete_node.state,  # type: ignore[arg-type]
                action=concrete_node.action,
                depth=concrete_node.depth,
                current_belief=belief,
                frontier=frontier_beliefs,
                reached_order=reached_order,
                note="GOAL belief popped: every possible world is clean.",
            )
            trace.append(entry)
            trace_by_state.setdefault(concrete_node.state, entry)
            return SearchResult(
                True,
                concrete_node.path(),
                trace,
                trace_by_state,
                "Belief-state plan found for all possible dirt configurations.",
                expansions,
            )

        if concrete_node.depth >= max_depth:
            entry = _make_trace(
                trace_step=len(trace),
                concrete_state=concrete_node.state,  # type: ignore[arg-type]
                action=concrete_node.action,
                depth=concrete_node.depth,
                current_belief=belief,
                frontier=frontier_beliefs,
                reached_order=reached_order,
                note=f"Depth limit reached for belief search: max_depth={max_depth}.",
            )
            trace.append(entry)
            trace_by_state.setdefault(concrete_node.state, entry)
            continue

        for action, child_belief in _belief_successors(belief):
            if child_belief in reached_set:
                continue

            child_concrete_state = _representative_after_action(
                concrete_node.state,  # type: ignore[arg-type]
                action,
            )
            child_node = SearchNode(
                state=child_concrete_state,
                parent=concrete_node,
                action=action,
                depth=concrete_node.depth + 1,
            )

            frontier.append((child_belief, child_node))
            frontier_beliefs.append(child_belief)
            reached_set.add(child_belief)
            reached_order.append(child_belief)

        entry = _make_trace(
            trace_step=len(trace),
            concrete_state=concrete_node.state,  # type: ignore[arg-type]
            action=concrete_node.action,
            depth=concrete_node.depth,
            current_belief=belief,
            frontier=frontier_beliefs,
            reached_order=reached_order,
            note="Expanded belief node by BFS; actions must be valid for every possible world.",
        )
        trace.append(entry)
        trace_by_state.setdefault(concrete_node.state, entry)

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        f"No belief-state plan within max_expansions={max_expansions}, max_depth={max_depth}.",
        expansions,
    )
