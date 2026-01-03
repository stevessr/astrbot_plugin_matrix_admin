"""
Matrix Admin Plugin - Base Mixin
提供共享的工具方法
"""

from typing import TYPE_CHECKING

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

if TYPE_CHECKING:
    from astrbot.api.star import Context


class AdminCommandMixin:
    """Admin 命令基类，提供共享工具方法"""

    context: "Context"

    def _get_matrix_client(self, event: AstrMessageEvent):
        """获取 Matrix 客户端实例"""
        if event.get_platform_name() != "matrix":
            return None

        try:
            for platform in self.context.platform_manager.platform_insts:
                meta = platform.meta()
                if meta.name == "matrix" and meta.id == event.get_platform_id():
                    if hasattr(platform, "client"):
                        return platform.client
        except Exception as e:
            logger.debug(f"获取 Matrix 客户端失败: {e}")

        return None

    def _parse_user_id(self, user_input: str, event: AstrMessageEvent) -> str | None:
        """解析用户输入为完整的 Matrix 用户 ID"""
        if not user_input:
            return None

        # 已经是完整的用户 ID
        if user_input.startswith("@") and ":" in user_input:
            return user_input

        # 尝试从房间 ID 提取服务器域名
        room_id = event.get_session_id()
        if ":" in room_id:
            server = room_id.split(":", 1)[1]
            if user_input.startswith("@"):
                return f"{user_input}:{server}"
            else:
                return f"@{user_input}:{server}"

        return None
