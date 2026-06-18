# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Iterator, List, Mapping, Optional, Sequence, Tuple


Assignment = Dict[str, str]
Domains = Dict[str, List[str]]
Neighbors = Mapping[str, Sequence[str]]
Step = Tuple[str, Assignment, Domains, Optional[str], Optional[str], str]


def snapshot_domains(current_domains: Domains, variables: Sequence[str]) -> Domains:
    return {var: list(current_domains[var]) for var in variables}


def format_assignment(assignment: Assignment, names: Mapping[str, str]) -> str:
    if not assignment:
        return "{}"

    parts = [
        f"'{names.get(var, var)} ({var})': '{color}'"
        for var, color in assignment.items()
    ]
    return "{" + ", ".join(parts) + "}"


def backtracking_search(
    variables: Sequence[str],
    domains: Mapping[str, Sequence[str]],
    neighbors: Neighbors,
    names: Mapping[str, str],
) -> Iterator[Step]:
    """
    Backtracking Search cho bài toán CSP tô màu bản đồ.

    Mỗi bước trả về:
    (step_type, assignment, current_domains, current_var, current_val, log_message)
    """
    assignment: Assignment = {}
    current_domains: Domains = {var: list(domains[var]) for var in variables}
    step_num = [0]

    def backtrack() -> Iterator[Step]:
        if len(assignment) == len(variables):
            yield (
                "success",
                assignment.copy(),
                snapshot_domains(current_domains, variables),
                None,
                None,
                "Tìm thấy lời giải thành công!",
            )
            return True

        var = next(item for item in variables if item not in assignment)
        var_name = names.get(var, var)

        step_num[0] += 1
        yield (
            "select_var",
            assignment.copy(),
            snapshot_domains(current_domains, variables),
            var,
            None,
            f"Bước {step_num[0]}: Chọn quận/huyện để tô: {var_name} ({var})",
        )

        for color in domains[var]:
            yield (
                "try_val",
                assignment.copy(),
                snapshot_domains(current_domains, variables),
                var,
                color,
                f" - Thử gán {var_name} ({var}) = {color}",
            )

            conflict_neighbor = next(
                (
                    neighbor
                    for neighbor in neighbors[var]
                    if neighbor in assignment and assignment[neighbor] == color
                ),
                None,
            )

            if conflict_neighbor is not None:
                conflict_name = names.get(conflict_neighbor, conflict_neighbor)
                yield (
                    "conflict",
                    assignment.copy(),
                    snapshot_domains(current_domains, variables),
                    var,
                    color,
                    f"   -> Thất bại: Trùng màu với {conflict_name} ({conflict_neighbor})",
                )
                continue

            assignment[var] = color
            old_domains = snapshot_domains(current_domains, variables)
            current_domains[var] = [color]

            yield (
                "assign",
                assignment.copy(),
                snapshot_domains(current_domains, variables),
                var,
                color,
                f"   -> Hợp lệ. Assignment = {format_assignment(assignment, names)}",
            )

            solved = yield from backtrack()
            if solved:
                return True

            del assignment[var]
            current_domains.clear()
            current_domains.update(old_domains)

            yield (
                "backtrack",
                assignment.copy(),
                snapshot_domains(current_domains, variables),
                var,
                color,
                f"   -> Quay lui: Bỏ gán {var_name} ({var})",
            )

        return False

    solved = yield from backtrack()
    if not solved:
        yield (
            "failure",
            assignment.copy(),
            snapshot_domains(current_domains, variables),
            None,
            None,
            "Không tìm thấy lời giải với tập màu hiện tại.",
        )
