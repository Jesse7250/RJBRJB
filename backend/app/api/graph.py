"""知识图谱 API

TODO:
- [待完成] 返回节点坐标/模块颜色，便于前端美化渲染
- [待完成] 支持查询学生个人学习路径高亮（已掌握/当前目标/未学）
- [待完成] 支持 A* 算法路径规划（当前为 shortestPath/BFS）
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

    nodes = [
        GraphNode(
            id=c["name"],
            name=c["name"],
            module=c.get("module", "未分类"),
            difficulty=c.get("difficulty", 3),
        )
        for c in concepts
    ]

    # 构造边：基于前置依赖关系
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
