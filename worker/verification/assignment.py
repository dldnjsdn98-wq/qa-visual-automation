from __future__ import annotations

import heapq
from dataclasses import dataclass

from worker.ocr.errors import AdapterError


@dataclass(frozen=True, slots=True)
class CandidateEdge:
    expected_index: int
    region_index: int
    method: str
    score_numerator: int
    score_denominator: int

    @property
    def micro_score(self) -> int:
        return (self.score_numerator * 1_000_000) // self.score_denominator


@dataclass(slots=True)
class _FlowEdge:
    to: int
    reverse: int
    capacity: int
    cost: int


class _Network:
    def __init__(self, size: int) -> None:
        self.graph: list[list[_FlowEdge]] = [[] for _ in range(size)]

    def add_edge(self, source: int, target: int, capacity: int, cost: int) -> _FlowEdge:
        forward = _FlowEdge(target, len(self.graph[target]), capacity, cost)
        reverse = _FlowEdge(source, len(self.graph[source]), 0, -cost)
        self.graph[source].append(forward)
        self.graph[target].append(reverse)
        return forward


def _objective_weights(expected_count: int) -> tuple[int, int, int]:
    maximum_micro_total = expected_count * 100_000_000
    assigned_unit = maximum_micro_total + 1
    maximum_assigned_and_micro = expected_count * assigned_unit + maximum_micro_total
    normalized_unit = maximum_assigned_and_micro + 1
    maximum_normalized_and_lower = (
        expected_count * normalized_unit + maximum_assigned_and_micro
    )
    exact_unit = maximum_normalized_and_lower + 1
    return exact_unit, normalized_unit, assigned_unit


def _edge_weight(
    edge: CandidateEdge,
    *,
    exact_unit: int,
    normalized_unit: int,
    assigned_unit: int,
) -> int:
    method_weight = 0
    if edge.method == "EXACT":
        method_weight = exact_unit
    elif edge.method == "NORMALIZED":
        method_weight = normalized_unit
    elif edge.method != "FUZZY":
        raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
    return method_weight + assigned_unit + edge.micro_score


def _minimum_cost_full_matching(
    expected_count: int,
    region_count: int,
    candidates_by_expected: list[list[CandidateEdge]],
) -> tuple[list[int], list[list[int]]]:
    right_count = region_count + expected_count
    source = 0
    left_start = 1
    right_start = left_start + expected_count
    sink = right_start + right_count
    network = _Network(sink + 1)

    exact_unit, normalized_unit, assigned_unit = _objective_weights(expected_count)
    lex_base = region_count + 1
    lex_unit = lex_base**expected_count
    weighted: dict[tuple[int, int], int] = {}
    maximum_edge_weight = 1
    for row_edges in candidates_by_expected:
        for edge in row_edges:
            primary_weight = _edge_weight(
                edge,
                exact_unit=exact_unit,
                normalized_unit=normalized_unit,
                assigned_unit=assigned_unit,
            )
            lex_weight = (region_count - edge.region_index) * (
                lex_base ** (expected_count - 1 - edge.expected_index)
            )
            weight = primary_weight * lex_unit + lex_weight
            weighted[(edge.expected_index, edge.region_index)] = weight
            maximum_edge_weight = max(maximum_edge_weight, weight)

    references: list[list[tuple[int, _FlowEdge, int]]] = [
        [] for _ in range(expected_count)
    ]
    for row in range(expected_count):
        left_node = left_start + row
        network.add_edge(source, left_node, 1, 0)
        for edge in candidates_by_expected[row]:
            right = edge.region_index
            cost = maximum_edge_weight - weighted[(row, right)]
            reference = network.add_edge(left_node, right_start + right, 1, cost)
            references[row].append((right, reference, cost))
        dummy_right = region_count + row
        dummy_cost = maximum_edge_weight
        reference = network.add_edge(
            left_node,
            right_start + dummy_right,
            1,
            dummy_cost,
        )
        references[row].append((dummy_right, reference, dummy_cost))

    for right in range(right_count):
        network.add_edge(right_start + right, sink, 1, 0)

    potential = [0] * (sink + 1)
    for _ in range(expected_count):
        distance: list[int | None] = [None] * (sink + 1)
        previous_node = [-1] * (sink + 1)
        previous_edge = [-1] * (sink + 1)
        distance[source] = 0
        queue: list[tuple[int, int]] = [(0, source)]
        while queue:
            current_distance, node = heapq.heappop(queue)
            if current_distance != distance[node]:
                continue
            for edge_index, edge in enumerate(network.graph[node]):
                if edge.capacity == 0:
                    continue
                reduced = edge.cost + potential[node] - potential[edge.to]
                candidate_distance = current_distance + reduced
                if distance[edge.to] is None or candidate_distance < distance[edge.to]:
                    distance[edge.to] = candidate_distance
                    previous_node[edge.to] = node
                    previous_edge[edge.to] = edge_index
                    heapq.heappush(queue, (candidate_distance, edge.to))
        if distance[sink] is None:
            raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
        for node, value in enumerate(distance):
            if value is not None:
                potential[node] += value
        node = sink
        while node != source:
            parent = previous_node[node]
            edge_index = previous_edge[node]
            if parent < 0 or edge_index < 0:
                raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
            edge = network.graph[parent][edge_index]
            edge.capacity -= 1
            network.graph[node][edge.reverse].capacity += 1
            node = parent

    matched_right = [-1] * expected_count
    for row, row_references in enumerate(references):
        for right, reference, cost in row_references:
            if reference.capacity == 0:
                matched_right[row] = right
        if matched_right[row] < 0:
            raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
    return matched_right, []


def assign_candidates(
    expected_count: int,
    region_count: int,
    candidates: list[CandidateEdge],
) -> dict[int, CandidateEdge]:
    if expected_count < 0 or region_count < 0:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
    if len(candidates) > 65_536:
        raise AdapterError("RESULT_LIMIT_EXCEEDED", "VERIFY")
    by_expected: list[list[CandidateEdge]] = [[] for _ in range(expected_count)]
    lookup: dict[tuple[int, int], CandidateEdge] = {}
    for edge in candidates:
        if not (0 <= edge.expected_index < expected_count):
            raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
        if not (0 <= edge.region_index < region_count):
            raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
        key = (edge.expected_index, edge.region_index)
        if key in lookup or edge.score_denominator <= 0:
            raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
        lookup[key] = edge
        by_expected[edge.expected_index].append(edge)
    for row_edges in by_expected:
        row_edges.sort(key=lambda edge: edge.region_index)

    if expected_count == 0:
        return {}
    matched, _ = _minimum_cost_full_matching(
        expected_count,
        region_count,
        by_expected,
    )
    return {
        row: lookup[(row, right)]
        for row, right in enumerate(matched)
        if right < region_count
    }
