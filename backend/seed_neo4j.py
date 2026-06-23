"""Neo4j 知识图谱种子数据导入脚本

TODO:
- [待完成] 在 Docker Compose 启动时自动运行该脚本
- [待完成] 增加导入幂等性，避免重复创建
- [待完成] 支持从多个 Cypher 文件批量导入
"""
import os

from app.core.config import get_settings
from app.services.neo4j_client import Neo4jClient


def seed_from_cypher(file_path: str):
    """从 Cypher 文件导入数据"""
    client = Neo4jClient()

    # 初始化 schema
    client.init_schema()

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 按分号分割多个语句
    statements = [s.strip() for s in content.split(";") if s.strip()]

    with client.driver.session() as session:
        for statement in statements:
            try:
                session.run(statement)
            except Exception as e:
                print(f"执行语句失败: {statement[:80]}...\n错误: {e}")

    print("知识图谱种子数据导入完成")

    # 统计
    with client.driver.session() as session:
        result = session.run("MATCH (c:Concept) RETURN count(c) as count").single()
        print(f"知识点节点数: {result['count']}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cypher_file = os.path.join(base_dir, "data", "knowledge_graph.cypher")
    seed_from_cypher(cypher_file)
