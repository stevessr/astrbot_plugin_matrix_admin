"""
Matrix Admin Plugin - Base Mixin
提供共享的工具方法
"""

from typing import TYPE_CHECKING

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from astrbot_plugin_matrix_adapter.utils import MatrixUtils

if TYPE_CHECKING:
    from astrbot.api.star import Context


class AdminCommandMixin:
    """Admin 命令基类，提供共享工具方法"""

    context: "Context"

    def _get_matrix_client(self, event: AstrMessageEvent):
        """获取 Matrix 客户端实例"""
        platform_name = str(event.get_platform_name() or "").strip().lower()
        if platform_name != "matrix":
            return None

        try:
            target_platform_id = str(event.get_platform_id() or "")
            return MatrixUtils.get_matrix_client(self.context, target_platform_id)
        except Exception as e:
            logger.debug(f"获取 Matrix 客户端失败：{e}")

        return None

    def _parse_user_id(
        self,
        user_input: str,
        event: AstrMessageEvent,
        room_id_hint: str = "",
    ) -> str | None:
        """解析用户输入为完整的 Matrix 用户 ID"""
        user_text = str(user_input or "").strip()
        if not user_text:
            return None

        # 已经是完整的用户 ID
        if user_text.startswith("@") and ":" in user_text:
            return user_text
        if ":" in user_text and not user_text.startswith("@"):
            return f"@{user_text}"

        # 尝试从房间 ID 提取服务器域名
        room_id = str(room_id_hint or event.get_session_id() or "")
        server = ""
        if ":" in room_id:
            server = room_id.split(":", 1)[1]

        if not server:
            client = self._get_matrix_client(event)
            client_user_id = str(getattr(client, "user_id", "") or "")
            if ":" in client_user_id:
                server = client_user_id.split(":", 1)[1]

        if server:
            if user_text.startswith("@"):
                return f"{user_text}:{server}"
            return f"@{user_text}:{server}"

        return None

    @staticmethod
    def _resolve_event_room_id(event: AstrMessageEvent) -> str | None:
        room_id = str(event.get_session_id() or "").strip()
        return room_id or None

    @staticmethod
    def _resolve_target_room_id(
        event: AstrMessageEvent, room_id: str = ""
    ) -> str | None:
        room_id_text = str(room_id or "").strip()
        if room_id_text:
            return room_id_text
        return AdminCommandMixin._resolve_event_room_id(event)
