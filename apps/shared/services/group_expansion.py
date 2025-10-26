"""
Group expansion engine with recursive resolution and circular reference prevention.

Implements pure functional expansion with caching for performance optimization.
Follows patent specification for set theory operations on semantic tag groups.
"""

from functools import lru_cache
from typing import Optional
import time

from apps.shared.services.group_storage import get_group_by_id, is_group_tag


# ============ Circular Reference Detection ============


def validate_circular_reference(
    group_id: str,
    new_member_id: str,
    max_depth: int = 10
) -> tuple[bool, Optional[str]]:
    """
    Validate that adding new_member to group won't create circular reference.

    Uses depth-first search to detect cycles.
    Returns (is_valid, error_message)
    """
    if group_id == new_member_id:
        return False, "Cannot add group to itself"

    if not is_group_tag(new_member_id):
        return True, None  # Regular tags cannot create cycles

    def would_create_cycle(
        current_id: str,
        target_id: str,
        visited: frozenset[str] = frozenset(),
        depth: int = 0
    ) -> bool:
        """Recursive cycle detection."""
        if current_id == target_id:
            return True

        if current_id in visited or depth >= max_depth:
            return False

        group = get_group_by_id(current_id)
        if not group:
            return False

        new_visited = visited | {current_id}

        # Check all nested groups
        for member_id in group.member_tag_ids:
            if is_group_tag(member_id):
                if would_create_cycle(member_id, target_id, new_visited, depth + 1):
                    return True

        return False

    # Check if new_member contains group_id anywhere in its hierarchy
    if would_create_cycle(new_member_id, group_id):
        return False, f"Adding {new_member_id} would create circular reference"

    return True, None


# ============ Group Expansion Engine ============


class GroupExpansionCache:
    """
    Cache for group expansions with LRU eviction.

    Implements bounded memory usage with automatic cleanup.
    """

    def __init__(self, max_size: int = 1024, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, frozenset[str]] = {}
        self._timestamps: dict[str, float] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def get(self, key: str) -> Optional[frozenset[str]]:
        """Get cached expansion if valid."""
        if key not in self._cache:
            self._cache_misses += 1
            return None

        # Check TTL
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            del self._cache[key]
            del self._timestamps[key]
            self._cache_misses += 1
            return None

        self._cache_hits += 1
        return self._cache[key]

    def put(self, key: str, value: frozenset[str]) -> None:
        """Store expansion in cache with TTL."""
        # Evict oldest entries if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        self._cache[key] = value
        self._timestamps[key] = time.time()

    def _evict_oldest(self) -> None:
        """Remove oldest 10% of cache entries."""
        sorted_keys = sorted(
            self._timestamps.keys(),
            key=lambda k: self._timestamps[k]
        )

        to_remove = sorted_keys[:max(1, len(sorted_keys) // 10)]
        for key in to_remove:
            del self._cache[key]
            del self._timestamps[key]

    def invalidate(self, group_id: str) -> None:
        """Invalidate cache entries for a group."""
        keys_to_remove = [k for k in self._cache.keys() if group_id in k]
        for key in keys_to_remove:
            del self._cache[key]
            del self._timestamps[key]

    def get_statistics(self) -> dict:
        """Return cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_size': len(self._cache),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }


# Global cache instance
_expansion_cache = GroupExpansionCache(max_size=1024, ttl_seconds=300)


def invalidate_expansion_cache(group_id: str) -> None:
    """Invalidate cache for a specific group."""
    _expansion_cache.invalidate(group_id)


def get_cache_statistics() -> dict:
    """Get expansion cache statistics."""
    return _expansion_cache.get_statistics()


# ============ Recursive Expansion ============


def expand_group_recursive(
    group_id: str,
    visited: frozenset[str] = frozenset(),
    max_depth: int = 10,
    current_depth: int = 0
) -> frozenset[str]:
    """
    Recursively expand group to all member tags.

    Mathematical specification:
    expand(G) = members(G) ∪ ⋃{expand(g) | g ∈ members(G) ∧ g is group}

    Complexity: O(n) where n = total unique tags in hierarchy
    Space: O(d) where d = max nesting depth

    Args:
        group_id: ID of group to expand
        visited: Set of already visited groups (prevents cycles)
        max_depth: Maximum nesting depth to traverse
        current_depth: Current depth in recursion

    Returns:
        Frozenset of all tag IDs (excluding group IDs)
    """
    # Check cache first
    cache_key = f"{group_id}:{','.join(sorted(visited))}"
    cached_result = _expansion_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Circular reference and depth check
    if group_id in visited or current_depth >= max_depth:
        return frozenset()

    # Get group data
    group = get_group_by_id(group_id)
    if not group:
        return frozenset()

    # Track visit
    new_visited = visited | {group_id}

    # Separate regular tags from nested groups
    direct_tags = frozenset()
    nested_groups = frozenset()

    for member_id in group.member_tag_ids:
        if is_group_tag(member_id):
            nested_groups = nested_groups | {member_id}
        else:
            direct_tags = direct_tags | {member_id}

    # Recursively expand nested groups
    expanded_tags = direct_tags

    for nested_group_id in nested_groups:
        nested_expansion = expand_group_recursive(
            nested_group_id,
            new_visited,
            max_depth,
            current_depth + 1
        )
        expanded_tags = expanded_tags | nested_expansion

    # Cache result
    _expansion_cache.put(cache_key, expanded_tags)

    return expanded_tags


# ============ Set Operations with Groups ============


def apply_group_to_zone(
    group_id: str,
    zone_type: str,
    current_tags: frozenset[str]
) -> frozenset[str]:
    """
    Apply group expansion to spatial zone with appropriate set operation.

    Pure functional implementation following patent specification.

    Args:
        group_id: ID of group to expand and apply
        zone_type: Type of zone ('union', 'intersection', 'exclusion', 'symmetric_diff')
        current_tags: Current tag set in zone

    Returns:
        Updated tag set after applying group
    """
    expanded_tags = expand_group_recursive(group_id)

    zone_operations = {
        'union': lambda curr, exp: curr | exp,
        'intersection': lambda curr, exp: curr & exp if curr else exp,
        'exclusion': lambda curr, exp: curr - exp,
        'symmetric_diff': lambda curr, exp: curr ^ exp
    }

    operation = zone_operations.get(zone_type, lambda c, e: c | e)
    return operation(current_tags, expanded_tags)


def apply_group_to_card(
    group_id: str,
    current_tags: frozenset[str]
) -> frozenset[str]:
    """
    Apply group expansion to card tags.

    Always uses union operation (add all member tags).

    Args:
        group_id: ID of group to expand
        current_tags: Current tag set on card

    Returns:
        Updated tag set with group members added
    """
    expanded_tags = expand_group_recursive(group_id)
    return current_tags | expanded_tags


# ============ Expansion Statistics ============


def get_expansion_depth(group_id: str) -> int:
    """
    Calculate maximum nesting depth of a group.

    Returns the depth of deepest nested group.
    """
    def calculate_depth(
        gid: str,
        visited: frozenset[str] = frozenset()
    ) -> int:
        if gid in visited:
            return 0

        group = get_group_by_id(gid)
        if not group:
            return 0

        new_visited = visited | {gid}

        nested_groups = [m for m in group.member_tag_ids if is_group_tag(m)]
        if not nested_groups:
            return 0

        return 1 + max(
            calculate_depth(ng, new_visited) for ng in nested_groups
        )

    return calculate_depth(group_id)


def get_total_expanded_count(group_id: str) -> int:
    """
    Get total number of tags when group is fully expanded.

    Returns count of unique tag IDs (excluding nested groups).
    """
    expanded = expand_group_recursive(group_id)
    return len(expanded)


def get_expansion_tree(group_id: str) -> dict:
    """
    Get tree structure of group expansion for visualization.

    Returns nested dict representing expansion hierarchy.
    """
    def build_tree(
        gid: str,
        visited: frozenset[str] = frozenset()
    ) -> dict:
        if gid in visited:
            return {'id': gid, 'circular': True}

        group = get_group_by_id(gid)
        if not group:
            return {'id': gid, 'error': 'not_found'}

        new_visited = visited | {gid}

        children = []
        for member_id in group.member_tag_ids:
            if is_group_tag(member_id):
                children.append(build_tree(member_id, new_visited))
            else:
                children.append({'id': member_id, 'type': 'tag'})

        return {
            'id': gid,
            'name': group.name,
            'type': 'group',
            'children': children,
            'member_count': len(group.member_tag_ids)
        }

    return build_tree(group_id)
