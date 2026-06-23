"""请求日志与错误监控中间件

记录：
- 每个请求的 method、path、status_code、耗时
- 异常请求的 traceback（简要）

输出到标准输出，便于 Docker/K8s 日志采集。
TODO:
- [待完成] 接入 Sentry/Logstash 等外部监控系统
- [待完成] 按用户/会话聚合日志
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
