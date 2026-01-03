"""
Matrix Admin Plugin - Query Commands
查询相关命令
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .base import AdminCommandMixin


class QueryCommandsMixin(AdminCommandMixin):
    """查询命令：whois, search"""

    async def cmd_whois(self, event: AstrMessageEvent, user: str):
        """查询用户信息

        用法：/admin whois <用户 ID>

        示例：
            /admin whois @user:example.com
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
            # 获取用户资料
            profile = await client.get_user_profile(user_id)
            display_name = profile.get("displayname", "未设置")
            avatar_url = profile.get("avatar_url", "无")

            # 获取房间内权限
            power_level = 0
            try:
                power_levels = await client.get_power_levels(room_id)
                users = power_levels.get("users", {})
                power_level = users.get(user_id, power_levels.get("users_default", 0))
            except Exception:
                pass

            # 获取房间成员状态
            member_info = await client.get_room_member(room_id, user_id)
            membership = "未知"
            if member_info:
                membership = member_info.get("membership", "未知")

            lines = [
                f"**用户信息：{user_id}**\n",
                f"显示名称：{display_name}",
                f"头像：{avatar_url}",
                f"房间状态：{membership}",
                f"权限等级：{power_level}",
            ]

            yield event.plain_result("\n".join(lines))

        except Exception as e:
            logger.error(f"查询用户信息失败：{e}")
            yield event.plain_result(f"查询用户信息失败：{e}")

    async def cmd_search(self, event: AstrMessageEvent, keyword: str, limit: int = 10):
        """搜索用户

        用法：/admin search <关键词> [数量]

        示例：
            /admin search alice
            /admin search bob 5
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        try:
            result = await client.search_users(keyword, limit)
            users = result.get("results", [])

            if not users:
                yield event.plain_result(f"未找到匹配 '{keyword}' 的用户")
                return

            lines = [f"**搜索结果 ({len(users)} 个用户):**\n"]
            for user in users:
                uid = user.get("user_id", "未知")
                name = user.get("display_name", "")
                if name:
                    lines.append(f"- {name} (`{uid}`)")
                else:
                    lines.append(f"- `{uid}`")

            yield event.plain_result("\n".join(lines))

        except Exception as e:
            logger.error(f"搜索用户失败：{e}")
            yield event.plain_result(f"搜索用户失败：{e}")
