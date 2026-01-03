"""
Matrix Admin Plugin - Ignore Commands
屏蔽列表相关命令
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .base import AdminCommandMixin


class IgnoreCommandsMixin(AdminCommandMixin):
    """屏蔽命令：ignore, unignore, ignorelist"""

    async def cmd_ignore(self, event: AstrMessageEvent, user: str):
        """屏蔽用户

        用法：/admin ignore <用户 ID>

        示例：
            /admin ignore @annoying:example.com
        """
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

    async def cmd_unignore(self, event: AstrMessageEvent, user: str):
        """取消屏蔽用户

        用法：/admin unignore <用户 ID>

        示例：
            /admin unignore @user:example.com
        """
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

    async def cmd_ignorelist(self, event: AstrMessageEvent):
        """查看屏蔽列表

        用法：/admin ignorelist
        """
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
