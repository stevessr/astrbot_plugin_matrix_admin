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
            platform_manager = getattr(self.context, "platform_manager", None)
            if platform_manager is None:
                return None
            target_platform_id = str(event.get_platform_id() or "")
            get_insts = getattr(platform_manager, "get_insts", None)
            if callable(get_insts):
                try:
                    platforms = get_insts()
                except Exception:
                    platforms = getattr(platform_manager, "platform_insts", [])
            else:
                platforms = getattr(platform_manager, "platform_insts", [])
            fallback_client = None
            for platform in platforms:
                try:
                    meta = platform.meta()
                except Exception:
                    continue
                if getattr(meta, "name", "") != "matrix":
                    continue
                client = getattr(platform, "client", None)
                if client is None:
                    continue
                platform_id = str(getattr(meta, "id", "") or "")
                if target_platform_id and platform_id == target_platform_id:
                    return client
                if fallback_client is None:
                    fallback_client = client
            return fallback_client
        except Exception as e:
            logger.debug(f"获取 Matrix 客户端失败：{e}")

        return None

    def _parse_user_id(self, user_input: str, event: AstrMessageEvent) -> str | None:
        """解析用户输入为完整的 Matrix 用户 ID"""
        if not user_input:
            return None

        # 已经是完整的用户 ID
        if user_input.startswith("@") and ":" in user_input:
            return user_input

        # 尝试从房间 ID 提取服务器域名
        room_id = str(event.get_session_id() or "")
        if ":" in room_id:
            server = room_id.split(":", 1)[1]
            if user_input.startswith("@"):
                return f"{user_input}:{server}"
            else:
                return f"@{user_input}:{server}"

        return None

    @staticmethod
    def _resolve_event_room_id(event: AstrMessageEvent) -> str | None:
        room_id = str(event.get_session_id() or "").strip()
        return room_id or None
