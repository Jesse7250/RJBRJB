"""A* 学习路径规划器

基于知识图谱前置依赖关系与学生已掌握知识点，使用 A* 算法计算从当前状态
到目标知识点的最优学习路径。

代价设计：
- 边代价 = 2.0 - strength（strength 越大，依赖越紧密，过渡代价越小）
- 启发函数 = max(0, 目标难度 - 当前难度) / 5.0 * 0.5
  保证可采纳性（h <= 实际最小边代价）。

回退策略：
- 若 A* 无法找到可达路径，则沿目标知识点的依赖链反向回溯到已掌握/根节点，
  再反转得到学习序列。
"""
import heapq
from typing import Dict, List, Optional, Tuple


def _build_adjacency(edges: List[dict]) -> Dict[str, List[Tuple[str, float]]]:
    """构建正向邻接表：source -> [(target, cost), ...]"""
    adj: Dict[str, List[Tuple[str, float]]] = {}
    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        strength = float(e.get("strength", 0.8))
        if not src or not tgt:
            continue
        cost = max(0.1, 2.0 - strength)
        adj.setdefault(src, []).append((tgt, cost))
    return adj


def _build_reverse_adjacency(edges: List[dict]) -> Dict[str, List[Tuple[str, float]]]:
    """构建反向邻接表：target -> [(source, cost), ...]"""
    rev: Dict[str, List[Tuple[str, float]]] = {}
    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        strength = float(e.get("strength", 0.8))
        if not src or not tgt:
            continue
        cost = max(0.1, 2.0 - strength)
        rev.setdefault(tgt, []).append((src, cost))
    return rev


def _difficulty_heuristic(
    node: str,
    goal: str,
    difficulties: Dict[str, float],
) -> float:
    """基于难度的可采纳启发函数"""
    goal_diff = difficulties.get(goal)
    node_diff = difficulties.get(node)
    if goal_diff is None or node_diff is None:
        return 0.0
    # 难度差越小，启发值越小；最多不超过 0.4，小于最小边代价 0.1-1.4
    return max(0.0, goal_diff - node_diff) / 5.0 * 0.5


def astar_learning_path(
    edges: List[dict],
    difficulties: Dict[str, float],
    from_concepts: List[str],
    to_concept: str,
) -> List[str]:
    """使用 A* 计算学习路径。

    Args:
        edges: 依赖边列表，每条边至少包含 source/target/optional strength。
        difficulties: 知识点难度映射（1-5）。
        from_concepts: 学生已掌握的知识点列表。
        to_concept: 目标知识点。

    Returns:
        从已掌握知识点到目标知识点的学习路径（包含目标节点）。
    """
    from_set = set(from_concepts)
    if to_concept in from_set:
        return [to_concept]

    adj = _build_adjacency(edges)
    if to_concept not in adj and not any(to_concept in _build_adjacency([e]) for e in edges):
        # 目标在图中但没有任何入边/出边，直接返回
        pass

    # 初始化：所有已掌握知识点都作为潜在起点
    open_heap: List[Tuple[float, int, str]] = []
    counter = 0
    g_score: Dict[str, float] = {}
    parent: Dict[str, Optional[str]] = {}
    visited: set = set()

    for start in from_set:
        if start not in g_score:
            g_score[start] = 0.0
            parent[start] = None
            h = _difficulty_heuristic(start, to_concept, difficulties)
            counter += 1
            heapq.heappush(open_heap, (h, counter, start))

    # A* 主循环
    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == to_concept:
            return _reconstruct_path(parent, current)
        if current in visited:
            continue
        visited.add(current)

        for neighbor, cost in adj.get(current, []):
            if neighbor in visited:
                continue
            tentative_g = g_score.get(current, float("inf")) + cost
            if tentative_g < g_score.get(neighbor, float("inf")):
                parent[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + _difficulty_heuristic(neighbor, to_concept, difficulties)
                counter += 1
                heapq.heappush(open_heap, (f, counter, neighbor))

    # A* 找不到路径时，回退到反向依赖链
    return _fallback_reverse_path(edges, from_set, to_concept)


def _reconstruct_path(parent: Dict[str, Optional[str]], goal: str) -> List[str]:
    """根据 parent 字典重建路径"""
    path = []
    node: Optional[str] = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    path.reverse()
    return path


def _fallback_reverse_path(
    edges: List[dict],
    from_set: set,
    to_concept: str,
) -> List[str]:
    """反向依赖链回退：从目标知识点逆流而上直到已掌握知识点或根节点"""
    rev = _build_reverse_adjacency(edges)
    visited = set()
    path = [to_concept]
    current = to_concept

    while current not in from_set:
        pres = [src for src, _ in rev.get(current, []) if src not in visited]
        if not pres:
            break
        # 优先选择已掌握的前置；否则选难度最低的前置（更基础）
        mastered_pres = [p for p in pres if p in from_set]
        if mastered_pres:
            current = mastered_pres[0]
        else:
            # 简单选第一个未访问的前置
            current = pres[0]
        if current in visited:
            break
        visited.add(current)
        path.append(current)

    path.reverse()
    # 确保目标在路径末尾
    if to_concept not in path:
        path.append(to_concept)
    return path


def compute_edge_cost(strength: float) -> float:
    """根据依赖强度计算边代价"""
    return max(0.1, 2.0 - float(strength))
