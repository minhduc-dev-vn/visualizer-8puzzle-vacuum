# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple


Assignment = Dict[str, str]
Domains = Dict[str, List[str]]
Neighbors = Mapping[str, Sequence[str]]
Step = Tuple[str, Assignment, Domains, Optional[str], Optional[str], str]
Arc = Tuple[str, str]


def snapshot_domains(current_domains: Domains, variables: Sequence[str]) -> Domains:
    return {var: list(current_domains[var]) for var in variables}


def singleton_assignment(current_domains: Domains, variables: Sequence[str]) -> Assignment:
    return {
        var: current_domains[var][0]
        for var in variables
        if len(current_domains[var]) == 1
    }


def format_domain(domain: Sequence[str]) -> str:
    return ", ".join(f"'{color}'" for color in domain) or "rỗng"


def revise(xi: str, xj: str, current_domains: Domains) -> List[str]:
    removed: List[str] = []

    for color in list(current_domains[xi]):
        has_support = any(color != other_color for other_color in current_domains[xj])
        if not has_support:
            current_domains[xi].remove(color)
            removed.append(color)

    return removed


def ac3_search(
    variables: Sequence[str],
    domains: Mapping[str, Sequence[str]],
    neighbors: Neighbors,
    names: Mapping[str, str],
) -> Iterator[Step]:
    """
    AC-3 cho bài toán CSP tô màu bản đồ.

    AC-3 chỉ rút gọn miền giá trị. Nếu sau khi chạy một biến còn nhiều màu,
    thuật toán chưa tự chọn màu cuối cùng cho biến đó.
    """
    current_domains: Domains = {var: list(domains[var]) for var in variables}
    queue: Deque[Arc] = deque(
        (xi, xj)
        for xi in variables
        for xj in neighbors[xi]
    )
    step_num = 0

    yield (
        "select_var",
        singleton_assignment(current_domains, variables),
        snapshot_domains(current_domains, variables),
        None,
        None,
        f"Khởi tạo AC-3 với {len(queue)} cung cần kiểm tra.",
    )

    while queue:
        xi, xj = queue.popleft()
        step_num += 1
        xi_name = names.get(xi, xi)
        xj_name = names.get(xj, xj)

        yield (
            "select_var",
            singleton_assignment(current_domains, variables),
            snapshot_domains(current_domains, variables),
            xi,
            None,
            f"Bước {step_num}: Lấy cung ({xi_name} ({xi}), {xj_name} ({xj})) khỏi hàng đợi.",
        )

        removed = revise(xi, xj, current_domains)

        if not removed:
            yield (
                "no_change",
                singleton_assignment(current_domains, variables),
                snapshot_domains(current_domains, variables),
                xi,
                None,
                f"   -> Không xóa màu nào: mọi màu của {xi_name} đều có màu hỗ trợ ở {xj_name}.",
            )
            continue

        removed_text = ", ".join(f"'{color}'" for color in removed)
        yield (
            "prune",
            singleton_assignment(current_domains, variables),
            snapshot_domains(current_domains, variables),
            xi,
            None,
            f"   -> Xóa {removed_text} khỏi miền của {xi_name}. Miền còn lại = [{format_domain(current_domains[xi])}]",
        )

        if not current_domains[xi]:
            yield (
                "failure",
                singleton_assignment(current_domains, variables),
                snapshot_domains(current_domains, variables),
                xi,
                None,
                f"AC-3 thất bại: Miền giá trị của {xi_name} ({xi}) bị rỗng.",
            )
            return

        arcs_added: List[Arc] = []
        for xk in neighbors[xi]:
            if xk == xj:
                continue

            queue.append((xk, xi))
            arcs_added.append((xk, xi))

        if arcs_added:
            arc_text = ", ".join(
                f"({names.get(xk, xk)} ({xk}), {xi_name} ({xi}))"
                for xk, _ in arcs_added
            )
            yield (
                "prune",
                singleton_assignment(current_domains, variables),
                snapshot_domains(current_domains, variables),
                xi,
                None,
                f"   -> Vì miền của {xi_name} thay đổi, thêm lại các cung liên quan: {arc_text}",
            )

    yield (
        "success",
        singleton_assignment(current_domains, variables),
        snapshot_domains(current_domains, variables),
        None,
        None,
        "AC-3 kết thúc: CSP đã nhất quán cung. Các quận/huyện còn nhiều màu cần thuật toán tìm kiếm để chọn tiếp.",
    )
