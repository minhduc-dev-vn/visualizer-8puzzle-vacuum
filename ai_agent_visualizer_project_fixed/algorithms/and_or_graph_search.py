from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple

from algorithms.common import SearchNode, SearchResult, StateFormatter, TraceEntry, append_trace


@dataclass(frozen=True)
class PlanResult:
    path: List[SearchNode]
    plan_text: str


def _group_successors(successors: Iterable[Tuple[str, object]]) -> List[Tuple[str, Tuple[object, ...]]]:
    grouped: Dict[str, List[object]] = {}

    for action, state in successors:
        states = grouped.setdefault(action, [])
        if state not in states:
            states.append(state)

    return [(action, tuple(states)) for action, states in grouped.items()]


def _trim(text: str, max_length: int = 260) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3]}..."


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
    AND-OR graph search.

    The current project exposes successors as (action, next_state). To support
    nondeterministic actions, successors with the same action name are grouped
    and every possible result state must be solved by AND_SEARCH.
    """
    if max_depth is None:
        max_depth = 12

    root = SearchNode(start_state, parent=None, action="START", depth=0)
    reached_set = {start_state}
    reached_order = [start_state]

    trace: List[TraceEntry] = []
    trace_by_state = {}
    expansions = 0
    hit_expansion_limit = False
    hit_depth_limit = False

    def remember_state(state: object) -> None:
        if state not in reached_set:
            reached_set.add(state)
            reached_order.append(state)

    def add_trace(node: SearchNode, frontier: List[SearchNode], note: str) -> None:
        append_trace(
            trace=trace,
            trace_by_state=trace_by_state,
            node=node,
            frontier=frontier,
            reached_order=reached_order,
            formatter=formatter,
            note=note,
        )

    def and_search(nodes: List[SearchNode], path: Tuple[object, ...]) -> PlanResult | None:
        branch_plans: List[Tuple[SearchNode, PlanResult]] = []

        for child in nodes:
            plan = or_search(child, path)
            if plan is None:
                return None
            branch_plans.append((child, plan))

        if not branch_plans:
            return PlanResult([], "{}")

        representative_path = branch_plans[0][1].path

        if len(branch_plans) == 1:
            return PlanResult(representative_path, branch_plans[0][1].plan_text)

        plan_parts = [
            f"{formatter(child.state)}: {plan.plan_text}"
            for child, plan in branch_plans
        ]
        return PlanResult(representative_path, "{ " + "; ".join(plan_parts) + " }")

    def or_search(node: SearchNode, path: Tuple[object, ...]) -> PlanResult | None:
        nonlocal expansions, hit_expansion_limit, hit_depth_limit

        if is_goal(node.state):
            add_trace(
                node,
                [],
                "OR_SEARCH: goal test succeeded; return empty plan",
            )
            return PlanResult([node], "GOAL")

        if node.state in path:
            add_trace(
                node,
                [],
                "OR_SEARCH: failure because state is already on the current path",
            )
            return None

        if node.depth >= max_depth:
            hit_depth_limit = True
            add_trace(
                node,
                [],
                f"OR_SEARCH: depth limit reached (depth={node.depth}, max_depth={max_depth})",
            )
            return None

        if expansions >= max_expansions:
            hit_expansion_limit = True
            add_trace(
                node,
                [],
                f"OR_SEARCH: expansion limit reached (max_expansions={max_expansions})",
            )
            return None

        expansions += 1
        action_groups = _group_successors(get_successors(node.state))

        if not action_groups:
            add_trace(
                node,
                [],
                "OR_SEARCH: no available actions; return failure",
            )
            return None

        next_path = path + (node.state,)

        for action, result_states in action_groups:
            child_nodes = [
                SearchNode(
                    state=result_state,
                    parent=node,
                    action=action,
                    depth=node.depth + 1,
                )
                for result_state in result_states
            ]

            for child in child_nodes:
                remember_state(child.state)

            add_trace(
                node,
                child_nodes,
                f"OR_SEARCH: try action {action}; AND_SEARCH must solve {len(child_nodes)} result state(s)",
            )

            plan = and_search(child_nodes, next_path)

            if plan is not None:
                if plan.plan_text == "GOAL":
                    plan_text = action
                else:
                    plan_text = f"{action} -> {plan.plan_text}"

                add_trace(
                    node,
                    child_nodes,
                    f"OR_SEARCH: action {action} succeeds; conditional plan: {_trim(plan_text)}",
                )
                return PlanResult([node] + plan.path, plan_text)

            add_trace(
                node,
                child_nodes,
                f"OR_SEARCH: action {action} failed; trying next action",
            )

        return None

    plan = or_search(root, tuple())

    if plan is not None:
        return SearchResult(
            True,
            plan.path,
            trace,
            _align_trace_with_path(plan.path, trace, trace_by_state),
            "Conditional plan found by AND-OR Graph Search.",
            expansions,
        )

    if hit_expansion_limit:
        message = f"No conditional plan within max_expansions={max_expansions}."
    elif hit_depth_limit:
        message = f"No conditional plan within max_depth={max_depth}."
    else:
        message = "No conditional plan found."

    return SearchResult(
        False,
        [],
        trace,
        trace_by_state,
        message,
        expansions,
    )
