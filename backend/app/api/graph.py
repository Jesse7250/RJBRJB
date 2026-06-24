"""知识图谱 API

对应需求/功能：
- 向前端提供完整的 Python 知识图谱数据（节点、边）。
- 提供从已掌握知识点到目标知识点的学习路径查询。
- 提供单个知识点的详细信息查询。

主要接口：
- GET /api/graph/：获取完整知识图谱节点与前置依赖边。
- GET /api/graph/path：根据已掌握知识点和目标知识点计算学习路径。
- GET /api/graph/concept/{name}：获取指定知识点详情。

主要类：
- 直接使用 Pydantic 模型 GraphData / GraphNode / GraphEdge 序列化响应。

TODO:
- [已完成] 完整知识图谱节点与边返回已实现
- [已完成] 学习路径查询接口已实现
- [已完成] 知识点详情查询已实现
- [待完成] 返回节点坐标/模块颜色，便于前端美化渲染
- [待完成] 支持查询学生个人学习路径高亮（已掌握/当前目标/未学）
- [待完成] 支持 A* 算法路径规划（当前图存储层为 shortestPath/BFS）
- [待完成] 支持图嵌入向量计算与相似知识点推荐
"""
from fastapi import APIRouter

from app.models.schemas import GraphData, GraphEdge, GraphNode
from app.services.graph_factory import get_graph_store

router = APIRouter()


@router.get("/", response_model=GraphData)
async def get_graph():
    """获取完整知识图谱"""
    graph = get_graph_store()
    concepts = graph.get_all_concepts()

    # 构造节点列表
    nodes = [
        GraphNode(
            id=c["name"],
            name=c["name"],
            module=c.get("module", "未分类"),
            difficulty=c.get("difficulty", 3),
        )
        for c in concepts
    ]

    # 构造边：基于前置依赖关系，避免重复边
    edges = []
    seen_edges = set()
    for c in concepts:
        concept = graph.get_concept(c["name"])
        if not concept:
            continue
        for pre in concept.get("prerequisites", []):
            key = (pre, c["name"])
            if key not in seen_edges:
                seen_edges.add(key)
                edges.append(GraphEdge(source=pre, target=c["name"], strength=0.8))

    return GraphData(nodes=nodes, edges=edges)


@router.get("/path")
async def get_learning_path(from_concepts: str, to_concept: str):
    """获取从已掌握知识到目标知识点的学习路径"""
    graph = get_graph_store()
    # 支持多个已掌握知识点，以逗号分隔
    from_list = [c.strip() for c in from_concepts.split(",")]
    path = graph.get_learning_path(from_list, to_concept)
    return {"from": from_list, "to": to_concept, "path": path}


@router.get("/concept/{name}")
async def get_concept(name: str):
    """获取知识点详情"""
    graph = get_graph_store()
    concept = graph.get_concept(name)
    if not concept:
        return {"error": "知识点不存在"}
    return concept
