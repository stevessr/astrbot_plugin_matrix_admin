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
    _matrix_utils_cls = None

    def _get_matrix_utils_cls(self):
        if self._matrix_utils_cls is not None:
            return self._matrix_utils_cls

        try:
            from astrbot_plugin_matrix_adapter.utils import MatrixUtils
        except ImportError as e:
            logger.debug(f"导入 MatrixUtils 失败：{e}")
            return None

        self._matrix_utils_cls = MatrixUtils
        return MatrixUtils

    def _resolve_matrix_platform(
        self, event: AstrMessageEvent, matrix_platform_id: str = ""
    ):
        matrix_utils_cls = self._get_matrix_utils_cls()
        if matrix_utils_cls is None:
            return None, "未检测到 Matrix 适配器插件"

        requested_platform_id = str(matrix_platform_id or "").strip()
        current_platform_name = str(event.get_platform_name() or "").strip().lower()
        current_platform_id = str(event.get_platform_id() or "")

        target_platform_id = requested_platform_id
        if not target_platform_id and current_platform_name == "matrix":
            target_platform_id = current_platform_id

        if not target_platform_id and current_platform_name != "matrix":
            matrix_platform_ids = matrix_utils_cls.list_matrix_platform_ids(
                self.context
            )
            if not matrix_platform_ids:
                return None, "未检测到可用的 Matrix 适配器"
            if len(matrix_platform_ids) > 1:
                return None, (
                    "检测到多个 Matrix 适配器，请在命令末尾指定 matrix_platform_id：\n"
                    + "\n".join(
                        f"- {platform_id}" for platform_id in matrix_platform_ids
                    )
                )
            target_platform_id = matrix_platform_ids[0]

        platform = matrix_utils_cls.get_matrix_platform(
            self.context,
            target_platform_id,
            fallback_to_first=not bool(target_platform_id),
        )
        if platform is None:
            return None, "指定的 Matrix 适配器不存在或不可用"
        return platform, None

    def _resolve_matrix_e2ee_manager(
        self,
        event: AstrMessageEvent,
        matrix_platform_id: str = "",
    ):
        platform, error = self._resolve_matrix_platform(event, matrix_platform_id)
        if error:
            return None, error

        e2ee_manager = getattr(platform, "e2ee_manager", None)
        if not e2ee_manager:
            return None, "端到端加密未启用、不可用，或指定的 Matrix 适配器不存在"
        return e2ee_manager, None

    @staticmethod
    def _get_event_e2ee_manager(event: AstrMessageEvent):
        try:
            message_obj = getattr(event, "message_obj", None)
            if message_obj:
                raw_message = getattr(message_obj, "raw_message", None)
                if raw_message:
                    adapter = getattr(raw_message, "_adapter", None)
                    if adapter:
                        return getattr(adapter, "e2ee_manager", None)
        except Exception as exc:
            logger.debug(f"获取 e2ee_manager 失败：{exc}")
        return None

    def _get_matrix_client(self, event: AstrMessageEvent):
        """获取 Matrix 客户端实例"""
        platform_name = str(event.get_platform_name() or "").strip().lower()
        if platform_name != "matrix":
            return None

        matrix_utils_cls = self._get_matrix_utils_cls()
        if matrix_utils_cls is None:
            return None

        try:
            target_platform_id = str(event.get_platform_id() or "")
            return matrix_utils_cls.get_matrix_client(self.context, target_platform_id)
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
