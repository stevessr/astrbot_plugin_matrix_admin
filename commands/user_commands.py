"""
Matrix Admin Plugin - User Commands
踢出/封禁/邀请用户相关命令
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .base import AdminCommandMixin


class UserCommandsMixin(AdminCommandMixin):
    """用户管理命令: kick, ban, unban, invite"""

    async def cmd_kick(self, event: AstrMessageEvent, user: str, reason: str = ""):
        """踢出用户

        用法: /admin kick <用户ID> [原因]

        示例:
            /admin kick @baduser:example.com
            /admin kick @baduser:example.com 违规发言
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        user_id = self._parse_user_id(user, event)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        room_id = event.get_session_id()

        try:
            await client.kick_user(room_id, user_id, reason or None)
            msg = f"已将 {user_id} 踢出房间"
            if reason:
                msg += f"\n原因: {reason}"
            yield event.plain_result(msg)
        except Exception as e:
            logger.error(f"踢出用户失败: {e}")
            yield event.plain_result(f"踢出用户失败: {e}")

    async def cmd_ban(self, event: AstrMessageEvent, user: str, reason: str = ""):
        """封禁用户

        用法: /admin ban <用户ID> [原因]

        示例:
            /admin ban @spammer:example.com
            /admin ban @spammer:example.com 垃圾广告
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        user_id = self._parse_user_id(user, event)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        room_id = event.get_session_id()

        try:
            await client.ban_user(room_id, user_id, reason or None)
            msg = f"已封禁 {user_id}"
            if reason:
                msg += f"\n原因: {reason}"
            yield event.plain_result(msg)
        except Exception as e:
            logger.error(f"封禁用户失败: {e}")
            yield event.plain_result(f"封禁用户失败: {e}")

    async def cmd_unban(self, event: AstrMessageEvent, user: str):
        """解除封禁

        用法: /admin unban <用户ID>

        示例:
            /admin unban @user:example.com
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        user_id = self._parse_user_id(user, event)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        room_id = event.get_session_id()

        try:
            await client.unban_user(room_id, user_id)
            yield event.plain_result(f"已解除 {user_id} 的封禁")
        except Exception as e:
            logger.error(f"解除封禁失败: {e}")
            yield event.plain_result(f"解除封禁失败: {e}")

    async def cmd_invite(self, event: AstrMessageEvent, user: str):
        """邀请用户加入房间

        用法: /admin invite <用户ID>

        示例:
            /admin invite @friend:example.com
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        user_id = self._parse_user_id(user, event)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        room_id = event.get_session_id()

        try:
            await client.invite_user(room_id, user_id)
            yield event.plain_result(f"已邀请 {user_id} 加入房间")
        except Exception as e:
            logger.error(f"邀请用户失败: {e}")
            yield event.plain_result(f"邀请用户失败: {e}")
