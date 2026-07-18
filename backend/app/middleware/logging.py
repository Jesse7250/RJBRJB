"""请求日志与错误监控中间件

对应需求：
- 统一记录每个 HTTP 请求的关键信息（方法、路径、状态码、耗时、客户端 IP）。
- 捕获异常请求的简要 traceback，便于问题排查。
- 输出到标准输出，便于 Docker/K8s 日志采集。

主要类/函数/接口：
- RequestLoggingMiddleware：基于 Starlette BaseHTTPMiddleware 的请求日志中间件。
  - dispatch：记录请求开始时间，调用下游，记录耗时与状态码；异常时记录错误与 traceback。
- setup_logging：配置根日志格式与级别。
- logger（"eduhive"）：模块级日志器，供中间件与业务层使用。

TODO:
- [已完成] 请求耗时、状态码、异常 traceback 的统一记录。
- [已完成] 标准输出日志格式，适配容器化部署。
- [待完成] 接入 Sentry/Logstash 等外部监控系统。
- [待完成] 按用户/会话聚合日志，支持链路追踪。
"""
import logging
import time
import traceback
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("eduhive")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.time()
        client = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = (time.time() - start) * 1000
            logger.error(
                f"[{request.method}] {request.url.path} - ERROR - {duration:.1f}ms - {client} - {exc}"
            )
            logger.error(traceback.format_exc(limit=5))
            raise

        duration = (time.time() - start) * 1000
        logger.info(
            f"[{request.method}] {request.url.path} - {response.status_code} - {duration:.1f}ms - {client}"
        )
        return response


def setup_logging():
    """配置日志格式与级别"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

