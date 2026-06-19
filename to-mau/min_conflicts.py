# -*- coding: utf-8 -*-
from __future__ import annotations

import random
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


def conflicts_for(
    var: str,
    color: str,
    assignment: Assignment,
    neighbors: Neighbors,
) -> int:
    return sum(
        1
        for neighbor in neighbors[var]
        if assignment.get(neighbor) == color
    )


def conflicted_variables(
    variables: Sequence[str],
    assignment: Assignment,
    neighbors: Neighbors,
) -> List[str]:
    return [
        var
        for var in variables
        if conflicts_for(var, assignment[var], assignment, neighbors) > 0
    ]


def total_conflicts(
    variables: Sequence[str],
    assignment: Assignment,
    neighbors: Neighbors,
) -> int:
    counted_edges = set()
    conflicts = 0

    for var in variables:
        for neighbor in neighbors[var]:
            edge = tuple(sorted((var, neighbor)))
            if edge in counted_edges:
                continue

            counted_edges.add(edge)
            if assignment[var] == assignment[neighbor]:
                conflicts += 1

    return conflicts


def min_conflicts_search(
    variables: Sequence[str],
    domains: Mapping[str, Sequence[str]],
    neighbors: Neighbors,
    names: Mapping[str, str],
    max_steps: int = 300,
    seed: Optional[int] = None,
) -> Iterator[Step]:
    """
    Min-Conflicts cho bài toán CSP tô màu bản đồ.

    Thuật toán bắt đầu bằng một phép gán đầy đủ, sau đó liên tục đổi màu
    của một biến đang xung đột sang màu làm số xung đột nhỏ nhất.
    """
    rng = random.Random(seed)
    current_domains: Domains = {var: list(domains[var]) for var in variables}
    assignment: Assignment = {
        var: rng.choice(current_domains[var])
        for var in variables
    }

    yield (
        "assign",
        assignment.copy(),
        snapshot_domains(current_domains, variables),
        None,
        None,
        "Khởi tạo ngẫu nhiên một phép gán đầy đủ:\n"
        f"   {format_assignment(assignment, names)}",
    )

    for step in range(1, max_steps + 1):
        conflict_count = total_conflicts(variables, assignment, neighbors)
        if conflict_count == 0:
            yield (
                "success",
                assignment.copy(),
                snapshot_domains(current_domains, variables),
                None,
                None,
                f"Tìm thấy lời giải bằng Min-Conflicts sau {step - 1} bước đổi màu!",
            )
            return

        conflicted = conflicted_variables(variables, assignment, neighbors)
        var = rng.choice(conflicted)
        var_name = names.get(var, var)

        yield (
            "select_var",
            assignment.copy(),
            snapshot_domains(current_domains, variables),
            var,
            assignment[var],
            f"Bước {step}: Còn {conflict_count} cặp giáp ranh trùng màu. Chọn biến đang xung đột: {var_name} ({var}).",
        )

        conflict_by_color = {
            color: conflicts_for(var, color, assignment, neighbors)
            for color in current_domains[var]
        }
        best_score = min(conflict_by_color.values())
        best_colors = [
            color
            for color, score in conflict_by_color.items()
            if score == best_score
        ]
        chosen_color = rng.choice(best_colors)
        score_text = ", ".join(
            f"{color}: {score}"
            for color, score in conflict_by_color.items()
        )

        yield (
            "try_val",
            assignment.copy(),
            snapshot_domains(current_domains, variables),
            var,
            chosen_color,
            f"   -> Đếm xung đột nếu đổi màu {var_name}: {score_text}. Chọn '{chosen_color}'.",
        )

        old_color = assignment[var]
        assignment[var] = chosen_color

        yield (
            "assign",
            assignment.copy(),
            snapshot_domains(current_domains, variables),
            var,
            chosen_color,
            f"   -> Đổi {var_name} ({var}) từ '{old_color}' sang '{chosen_color}'.",
        )

    yield (
        "failure",
        assignment.copy(),
        snapshot_domains(current_domains, variables),
        None,
        None,
        f"Min-Conflicts dừng sau {max_steps} bước nhưng vẫn còn {total_conflicts(variables, assignment, neighbors)} xung đột.",
    )
