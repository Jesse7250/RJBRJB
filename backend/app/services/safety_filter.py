"""输入安全过滤与敏感词检测

对应需求：
- 在用户输入到达下游 Agent 之前进行本地轻量级安全审查。
- 对教学场景中常见的政治、色情、暴力、歧视等敏感关键词进行拦截。

主要类/函数/接口：
- ContentSafetyFilter：内容安全过滤器。
  - __init__：支持内置词库 + extra_keywords 扩展，并预编译正则。
  - check：检查文本是否命中敏感词，返回 (是否违规, 命中列表)。
  - sanitize：将敏感词替换为等长星号。
- get_safety_filter：全局单例工厂。

当前特点：
- 本地轻量级实现，适用于教学场景。
- 对命中内容返回统一提示，不调用下游 Agent。

TODO:
- [已完成] 本地敏感词关键词匹配与脱敏。
- [已完成] 预编译正则提升匹配效率，支持扩展词库。
- [待完成] 接入第三方内容审核 API（如阿里云、百度）提升准确率与覆盖范围。
- [待完成] 支持正则匹配与语义级违规检测。
"""
import re
from typing import List, Tuple


class ContentSafetyFilter:
    """内容安全过滤器"""

    # 示例敏感词列表（实际生产环境应维护更完整词库）
    SENSITIVE_KEYWORDS: List[str] = [
        # 政治敏感
        "反动", "颠覆", "分裂", "暴乱", "游行", "集会",
        # 色情低俗
        "色情", "淫秽", "嫖娼", "裸聊", "约炮",
        # 暴力恐怖
        "恐怖", "炸弹", "枪支", "杀人", "自杀", "自残",
        # 歧视侮辱
        "傻逼", "脑残", "废物", "去死",
    ]

    def __init__(self, extra_keywords: List[str] | None = None):
        self.keywords = set(self.SENSITIVE_KEYWORDS)
        if extra_keywords:
            self.keywords.update(extra_keywords)
        # 预编译正则，提升匹配效率
        self._pattern = re.compile(
            "|".join(re.escape(k) for k in self.keywords),
            re.IGNORECASE,
        )

    def check(self, text: str) -> Tuple[bool, List[str]]:
        """检查文本是否包含敏感词

        Returns:
            (是否违规, 命中关键词列表)
        """
        if not text:
            return False, []
        matches = self._pattern.findall(text)
        if not matches:
            return False, []
        return True, list(set(matches))

    def sanitize(self, text: str) -> str:
        """将敏感词替换为 ***"""
        if not text:
            return text
        return self._pattern.sub(lambda m: "*" * len(m.group()), text)


_safety_filter: ContentSafetyFilter | None = None


def get_safety_filter() -> ContentSafetyFilter:
    """获取全局安全过滤器实例"""
    global _safety_filter
    if _safety_filter is None:
        _safety_filter = ContentSafetyFilter()
    return _safety_filter

