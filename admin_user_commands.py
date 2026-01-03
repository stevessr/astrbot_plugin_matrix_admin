"""
Matrix admin user management commands.
"""

from astrbot.api import logger


async def admin_kick(self, event, user: str, reason: str = ""):
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
            msg += f"\n原因：{reason}"
        yield event.plain_result(msg)
    except Exception as e:
        logger.error(f"踢出用户失败：{e}")
        yield event.plain_result(f"踢出用户失败：{e}")


async def admin_ban(self, event, user: str, reason: str = ""):
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
            msg += f"\n原因：{reason}"
        yield event.plain_result(msg)
    except Exception as e:
        logger.error(f"封禁用户失败：{e}")
        yield event.plain_result(f"封禁用户失败：{e}")


async def admin_unban(self, event, user: str):
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
        logger.error(f"解除封禁失败：{e}")
        yield event.plain_result(f"解除封禁失败：{e}")


async def admin_invite(self, event, user: str):
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
        logger.error(f"邀请用户失败：{e}")
        yield event.plain_result(f"邀请用户失败：{e}")


async def admin_ignore(self, event, user: str):
    client = self._get_matrix_client(event)
    if not client:
        yield event.plain_result("此命令仅在 Matrix 平台可用")
        return

    user_id = self._parse_user_id(user, event)
    if not user_id:
        yield event.plain_result("无效的用户 ID")
        return

    try:
        await client.ignore_user(user_id)
        yield event.plain_result(f"已屏蔽 {user_id}")
    except Exception as e:
        logger.error(f"屏蔽用户失败：{e}")
        yield event.plain_result(f"屏蔽用户失败：{e}")


async def admin_unignore(self, event, user: str):
    client = self._get_matrix_client(event)
    if not client:
        yield event.plain_result("此命令仅在 Matrix 平台可用")
        return

    user_id = self._parse_user_id(user, event)
    if not user_id:
        yield event.plain_result("无效的用户 ID")
        return

    try:
        await client.unignore_user(user_id)
        yield event.plain_result(f"已取消屏蔽 {user_id}")
    except Exception as e:
        logger.error(f"取消屏蔽失败：{e}")
        yield event.plain_result(f"取消屏蔽失败：{e}")


async def admin_ignorelist(self, event):
    client = self._get_matrix_client(event)
    if not client:
        yield event.plain_result("此命令仅在 Matrix 平台可用")
        return

    try:
        ignored = await client.get_ignored_users()

        if not ignored:
            yield event.plain_result("屏蔽列表为空")
            return

        lines = [f"**屏蔽列表 ({len(ignored)} 人):**\n"]
        for uid in ignored:
            lines.append(f"- `{uid}`")

        yield event.plain_result("\n".join(lines))

    except Exception as e:
        logger.error(f"获取屏蔽列表失败：{e}")
        yield event.plain_result(f"获取屏蔽列表失败：{e}")
