"""Original data-only assembly contracts; no generated-code execution or authority grants."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping
from types import MappingProxyType


def strict_json(raw: str | bytes, *, max_bytes: int = 65536, max_depth: int = 16, max_items: int = 4096) -> Any:
    encoded = raw.encode('utf-8') if isinstance(raw, str) else raw
    if not isinstance(encoded, bytes) or len(encoded) > max_bytes:
        raise ValueError('JSON exceeds input budget')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('Non-finite JSON number')
    try:
        value = json.loads(encoded.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Invalid or excessively nested JSON') from error
    count = 0
    def visit(item, depth):
        nonlocal count
        count += 1
        if count > max_items or depth > max_depth:
            raise ValueError('JSON structural budget exceeded')
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError('Non-finite JSON number')
        if isinstance(item, int) and not isinstance(item, bool) and item.bit_length() > 256:
            raise ValueError('JSON integer budget exceeded')
        if isinstance(item, dict):
            for child in item.values(): visit(child, depth + 1)
        elif isinstance(item, list):
            for child in item: visit(child, depth + 1)
    visit(value, 0)
    return value


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    strict_json(encoded,max_bytes=16*1024*1024,max_items=100000)
    return hashlib.sha256(encoded).hexdigest()


def _digest(value: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in '0123456789abcdef' for char in value):
        raise ValueError('Invalid SHA256 identity')
    return value


@dataclass(frozen=True)
class AssemblyNode:
    id: str
    operator: str
    dependencies: tuple[str, ...] = ()
    configuration_sha256: str = '0' * 64


@dataclass(frozen=True)
class AssemblyReceipt:
    node_id: str
    operator: str
    source_sha256: str
    configuration_sha256: str
    dependency_receipts: tuple[tuple[str, str], ...]
    output_sha256: str
    generation: int
    receipt_sha256: str


class AssemblyPlan:
    """Bounded dependency validation and hash receipts; callers persist and authenticate them."""
    OPERATORS = frozenset({'parse', 'normalize', 'extract', 'validate', 'index', 'project'})

    def __init__(self, nodes: tuple[AssemblyNode, ...], *, max_nodes: int = 64, max_edges: int = 256):
        if not nodes or len(nodes) > max_nodes:
            raise ValueError('Assembly node budget exceeded')
        self.nodes = MappingProxyType({node.id: node for node in nodes})
        if len(self.nodes) != len(nodes):
            raise ValueError('Duplicate assembly node')
        edges = 0
        for node in nodes:
            if not isinstance(node.id, str) or not node.id or len(node.id) > 64 or not isinstance(node.operator, str) or node.operator not in self.OPERATORS:
                raise ValueError('Unsupported assembly node/operator')
            if not isinstance(node.dependencies, tuple) or any(not isinstance(dep, str) for dep in node.dependencies):
                raise ValueError('Immutable string dependencies required')
            _digest(node.configuration_sha256)
            if len(set(node.dependencies)) != len(node.dependencies):
                raise ValueError('Duplicate dependency')
            if any(dep not in self.nodes for dep in node.dependencies):
                raise ValueError('Missing dependency')
            edges += len(node.dependencies)
        if edges > max_edges:
            raise ValueError('Assembly edge budget exceeded')
        self.order = self._topological_order()

    def _topological_order(self):
        ordered, pending = [], set(self.nodes)
        while pending:
            ready = sorted(node for node in pending if all(dep in ordered for dep in self.nodes[node].dependencies))
            if not ready:
                raise ValueError('Assembly dependency cycle')
            ordered.extend(ready)
            pending.difference_update(ready)
        return tuple(ordered)

    def create_receipt(self, node_id: str, *, source_sha256: str, output: Any,
                       dependencies: Mapping[str, AssemblyReceipt], generation: int) -> AssemblyReceipt:
        node = self.nodes[node_id]
        if type(generation) is not int or generation < 1:
            raise ValueError('Invalid generation')
        _digest(source_sha256)
        if set(dependencies) != set(node.dependencies):
            raise ValueError('Dependency receipt scope mismatch')
        for dep_id, receipt in dependencies.items():
            if receipt.node_id != dep_id or receipt.source_sha256 != source_sha256:
                raise ValueError('Dependency source mismatch')
            if receipt.configuration_sha256 != self.nodes[dep_id].configuration_sha256:
                raise ValueError('Dependency configuration stale')
            self.verify_integrity(receipt)
        dependency_hashes = tuple(sorted((key, value.receipt_sha256) for key, value in dependencies.items()))
        fields = dict(node_id=node_id, operator=node.operator, source_sha256=source_sha256, configuration_sha256=node.configuration_sha256,
                      dependency_receipts=dependency_hashes, output_sha256=canonical_hash(output), generation=generation)
        return AssemblyReceipt(**fields, receipt_sha256=canonical_hash(fields))

    @staticmethod
    def verify_integrity(receipt: AssemblyReceipt):
        fields = {name: getattr(receipt, name) for name in receipt.__dataclass_fields__ if name != 'receipt_sha256'}
        if canonical_hash(fields) != receipt.receipt_sha256:
            raise ValueError('Assembly receipt hash mismatch')

    def require_fresh(self, receipt: AssemblyReceipt, *, source_sha256: str,
                      current: Mapping[str, AssemblyReceipt]):
        self.verify_integrity(receipt)
        node = self.nodes[receipt.node_id]
        if {dep for dep, _ in receipt.dependency_receipts} != set(node.dependencies) or len(receipt.dependency_receipts) != len(node.dependencies):
            raise ValueError('Dependency receipt scope mismatch')
        if receipt.source_sha256 != source_sha256 or receipt.configuration_sha256 != node.configuration_sha256 or receipt.operator != node.operator:
            raise ValueError('Stale assembly source/configuration')
        own_current = current.get(receipt.node_id)
        if own_current is not None and own_current.receipt_sha256 != receipt.receipt_sha256:
            raise ValueError('Stale node generation')
        for dep_id, dependency_hash in receipt.dependency_receipts:
            dependency = current.get(dep_id)
            if dependency is None or dependency.receipt_sha256 != dependency_hash:
                raise ValueError('Stale dependency generation')
            self.require_fresh(dependency, source_sha256=source_sha256, current=current)
        return True


def validate_holdout(training_families: set[str], holdout_families: set[str], paired_samples: list[dict]) -> dict:
    """Pair only independently held-out source families; never infer population significance."""
    if len(training_families) + len(holdout_families) > 512 or len(paired_samples) > 4096:
        raise ValueError('Holdout evaluation budget exceeded')
    if not holdout_families or training_families & holdout_families:
        raise ValueError('Source-family holdout contamination')
    seen, deltas = set(), []
    for row in paired_samples:
        if row.get('family') not in holdout_families or not row.get('case_id') or row['case_id'] in seen:
            raise ValueError('Invalid or duplicated holdout sample')
        seen.add(row['case_id'])
        for key in ('baseline', 'challenger'):
            if type(row.get(key)) not in (int, float) or not math.isfinite(row[key]):
                raise ValueError('Invalid paired measurement')
        delta = row['challenger'] - row['baseline']
        if not math.isfinite(delta):
            raise ValueError('Paired delta is non-finite')
        deltas.append(delta)
    if not deltas:
        raise ValueError('Missing paired samples')
    try:
        mean = math.fsum(delta / len(deltas) for delta in deltas)
    except OverflowError as error:
        raise ValueError('Paired mean is non-finite') from error
    return {'samples': len(deltas), 'mean_delta': mean,
            'population_significance': 'unqualified', 'holdout_families': sorted(holdout_families)}
