"""中间件包

对应需求：
- 统一导出项目中注册到 FastAPI 应用的中间件，简化 main.py 的导入。

当前导出：
- RequestLoggingMiddleware：请求日志与错误监控中间件。
- setup_logging：根日志配置函数。

TODO:
- [已完成] 请求日志中间件导出。
- [待完成] 未来如需认证、限流、链路追踪等中间件，统一在此导出。
"""
from app.middleware.logging import RequestLoggingMiddleware, setup_logging

__all__ = ["RequestLoggingMiddleware", "setup_logging"]
