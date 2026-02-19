"""
Matrix Admin Plugin - User Commands
踢出/封禁/邀请用户相关命令
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .base import AdminCommandMixin


class UserCommandsMixin(AdminCommandMixin):
    """用户管理命令：kick, ban, unban, invite"""

    async def cmd_kick(
        self,
        event: AstrMessageEvent,
        user: str,
        reason: str = "",
        room_id: str = "",
    ):
        """踢出用户

        用法：/admin kick <用户 ID> [原因] [room_id]

        示例：
            /admin kick @baduser:example.com
            /admin kick @baduser:example.com 违规发言
            /admin kick @baduser:example.com !roomid:example.com
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        reason_text = str(reason or "").strip()
        target_room_id = self._resolve_target_room_id(event, room_id)
        if (
            not target_room_id
            and not room_id
            and reason_text.startswith("!")
            and ":" in reason_text
        ):
            target_room_id = reason_text
            reason_text = ""

        if not target_room_id:
            yield event.plain_result("无法获取房间 ID")
            return

        user_id = self._parse_user_id(user, event, target_room_id)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        try:
            await client.kick_user(target_room_id, user_id, reason_text or None)
            msg = f"已将 {user_id} 踢出房间"
            if reason_text:
                msg += f"\n原因：{reason_text}"
            msg += f"\n房间：{target_room_id}"
            yield event.plain_result(msg)
        except Exception as e:
            logger.error(f"踢出用户失败：{e}")
            yield event.plain_result(f"踢出用户失败：{e}")

    async def cmd_ban(
        self,
        event: AstrMessageEvent,
        user: str,
        reason: str = "",
        room_id: str = "",
    ):
        """封禁用户

        用法：/admin ban <用户 ID> [原因] [room_id]

        示例：
            /admin ban @spammer:example.com
            /admin ban @spammer:example.com 垃圾广告
            /admin ban @spammer:example.com !roomid:example.com
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        reason_text = str(reason or "").strip()
        target_room_id = self._resolve_target_room_id(event, room_id)
        if (
            not target_room_id
            and not room_id
            and reason_text.startswith("!")
            and ":" in reason_text
        ):
            target_room_id = reason_text
            reason_text = ""

        if not target_room_id:
            yield event.plain_result("无法获取房间 ID")
            return

        user_id = self._parse_user_id(user, event, target_room_id)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        try:
            await client.ban_user(target_room_id, user_id, reason_text or None)
            msg = f"已封禁 {user_id}"
            if reason_text:
                msg += f"\n原因：{reason_text}"
            msg += f"\n房间：{target_room_id}"
            yield event.plain_result(msg)
        except Exception as e:
            logger.error(f"封禁用户失败：{e}")
            yield event.plain_result(f"封禁用户失败：{e}")

    async def cmd_unban(self, event: AstrMessageEvent, user: str, room_id: str = ""):
        """解除封禁

        用法：/admin unban <用户 ID> [room_id]

        示例：
            /admin unban @user:example.com
            /admin unban @user:example.com !roomid:example.com
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room_id = self._resolve_target_room_id(event, room_id)
        if not target_room_id:
            yield event.plain_result("无法获取房间 ID")
            return

        user_id = self._parse_user_id(user, event, target_room_id)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        try:
            await client.unban_user(target_room_id, user_id)
            yield event.plain_result(f"已解除 {user_id} 的封禁\n房间：{target_room_id}")
        except Exception as e:
            logger.error(f"解除封禁失败：{e}")
            yield event.plain_result(f"解除封禁失败：{e}")

    async def cmd_invite(self, event: AstrMessageEvent, user: str, room_id: str = ""):
        """邀请用户加入房间

        用法：/admin invite <用户 ID> [room_id]

        示例：
            /admin invite @friend:example.com
            /admin invite @friend:example.com !roomid:example.com
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room_id = self._resolve_target_room_id(event, room_id)
        if not target_room_id:
            yield event.plain_result("无法获取房间 ID")
            return

        user_id = self._parse_user_id(user, event, target_room_id)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        try:
            await client.invite_user(target_room_id, user_id)
            yield event.plain_result(
                f"已邀请 {user_id} 加入房间\n房间：{target_room_id}"
            )
        except Exception as e:
            logger.error(f"邀请用户失败：{e}")
            yield event.plain_result(f"邀请用户失败：{e}")
