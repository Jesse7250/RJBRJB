"""知识图谱存储抽象接口

支持 Neo4j 和内存两种实现，方便在没有 Docker/Neo4j 的环境下开发测试。
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

    @abstractmethod
    def check_forbidden_concepts(
        self, content: str, target_concept: str
    ) -> List[str]:
        """检查内容中是否包含未学概念"""
        ...

    def get_concepts_by_module(self) -> Dict[str, List[dict]]:
        """按模块分组返回知识点"""
        concepts = self.get_all_concepts()
        modules: Dict[str, List[dict]] = {}
        for c in concepts:
            module = c.get("module", "未分类")
            modules.setdefault(module, []).append(c)
        return modules
