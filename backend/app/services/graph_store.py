"""知识图谱存储抽象接口

对应需求：
- 统一知识图谱的存储抽象，使业务层不依赖具体后端。
- 支持 Neo4j 和内存两种实现，方便在没有 Docker/Neo4j 的环境下开发测试。

主要类/函数/接口：
- GraphStore：抽象基类，定义所有图存储必须实现的方法。
  - init_schema / close：可选的初始化与关闭钩子。
  - get_concept：获取单个知识点详情（含前置、后续、易错点）。
  - get_all_concepts：获取全部知识点列表。
  - get_prerequisites：获取某知识点的直接前置依赖。
  - get_learning_path：根据已掌握知识点计算到目标知识点的学习路径。
  - check_forbidden_concepts：检测内容中是否包含超纲概念。
  - get_concepts_by_module：按模块分组（通用默认实现）。

TODO:
- [已完成] 抽象接口定义与默认分组实现。
- [已完成] Neo4jClient 与 MemoryGraph 两个具体实现。
- [待完成] 增加批量导入/导出接口，便于种子数据维护。
- [待完成] 支持事务与并发访问控制。
- [待完成] 增加图嵌入计算与向量索引接口。
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class GraphStore(ABC):
    """知识图谱存储抽象基类"""

    def init_schema(self) -> None:
        """初始化 schema，子类可重写"""
        pass

    def close(self) -> None:
        """关闭连接，子类可重写"""
        pass

    @abstractmethod
    def get_concept(self, name: str) -> Optional[dict]:
        """获取知识点详情"""
        ...

    @abstractmethod
    def get_all_concepts(self) -> List[dict]:
        """获取所有知识点"""
        ...

    @abstractmethod
    def get_prerequisites(self, name: str) -> List[str]:
        """获取某知识点的直接前置依赖"""
        ...

    @abstractmethod
    def get_learning_path(self, from_concepts: List[str], to_concept: str) -> List[str]:
        """计算学习路径"""
        ...

    def get_dependency_edges(self) -> List[dict]:
        """获取所有 PREREQUISITE_OF 依赖边（默认实现，子类可重写以提升性能）。

        返回每条边至少包含：source, target, strength。
        """
        edges = []
        seen = set()
        for c in self.get_all_concepts():
            name = c.get("name")
            if not name:
                continue
            concept = self.get_concept(name)
            if not concept:
                continue
            for pre in concept.get("prerequisites", []):
                key = (pre, name)
                if key in seen:
                    continue
                seen.add(key)
                edges.append({"source": pre, "target": name, "strength": 0.8})
        return edges

    @abstractmethod
    def check_forbidden_concepts(
        self, content: str, target_concept: str
    ) -> List[str]:
        """检查内容中是否包含未学概念"""
        ...

    def get_concepts_by_module(self) -> Dict[str, List[dict]]:
        """按模块分组返回知识点（默认实现，子类可重写以提升性能）"""
        concepts = self.get_all_concepts()
        modules: Dict[str, List[dict]] = {}
        for c in concepts:
            module = c.get("module", "未分类")
            modules.setdefault(module, []).append(c)
        return modules

