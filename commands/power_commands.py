"""
Matrix Admin Plugin - Power Commands
权限管理相关命令
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .base import AdminCommandMixin


class PowerCommandsMixin(AdminCommandMixin):
    """权限管理命令：promote, demote, power, admins"""

    async def cmd_promote(
        self,
        event: AstrMessageEvent,
        user: str,
        level: str = "mod",
        room_id: str = "",
    ):
        """提升用户权限

        用法：/admin promote <用户 ID> [级别] [room_id]

        级别：
            mod - 管理员 (50)
            admin - 房主 (100)

        示例：
            /admin promote @user:example.com
            /admin promote @user:example.com admin
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room_id = self._resolve_target_room_id(event, room_id)
        level_text = str(level or "").strip().lower()
        if (
            not target_room_id
            and not room_id
            and level_text.startswith("!")
            and ":" in level_text
        ):
            target_room_id = level_text
            level_text = "mod"

        if not target_room_id:
            yield event.plain_result("无法获取房间 ID")
            return

        user_id = self._parse_user_id(user, event, target_room_id)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        level_map = {
            "mod": 50,
            "moderator": 50,
            "admin": 100,
            "owner": 100,
        }

        power_level = level_map.get(level_text, 50)
        level_name = "管理员" if power_level == 50 else "房主"

        try:
            await client.set_user_power_level(target_room_id, user_id, power_level)
            yield event.plain_result(
                f"已将 {user_id} 提升为{level_name} (权限等级：{power_level})\n"
                f"房间：{target_room_id}"
            )
        except Exception as e:
            logger.error(f"提升权限失败：{e}")
            yield event.plain_result(f"提升权限失败：{e}")

    async def cmd_demote(self, event: AstrMessageEvent, user: str, room_id: str = ""):
        """降低用户权限为普通成员

        用法：/admin demote <用户 ID> [room_id]

        示例：
            /admin demote @user:example.com
            /admin demote @user:example.com !roomid:example.com
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
            await client.set_user_power_level(target_room_id, user_id, 0)
            yield event.plain_result(
                f"已将 {user_id} 降级为普通成员\n房间：{target_room_id}"
            )
        except Exception as e:
            logger.error(f"降级失败：{e}")
            yield event.plain_result(f"降级失败：{e}")

    async def cmd_power(
        self,
        event: AstrMessageEvent,
        user: str,
        level: int,
        room_id: str = "",
    ):
        """设置用户权限等级

        用法：/admin power <用户 ID> <等级> [room_id]

        等级说明：
            0 - 普通成员
            50 - 管理员
            100 - 房主

        示例：
            /admin power @user:example.com 50
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
            await client.set_user_power_level(target_room_id, user_id, level)
            yield event.plain_result(
                f"已将 {user_id} 的权限等级设置为 {level}\n房间：{target_room_id}"
            )
        except Exception as e:
            logger.error(f"设置权限失败：{e}")
            yield event.plain_result(f"设置权限失败：{e}")

    async def cmd_admins(self, event: AstrMessageEvent, room_id: str = ""):
        """列出房间管理员

        用法：/admin admins [room_id]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room_id = self._resolve_target_room_id(event, room_id)
        if not target_room_id:
            yield event.plain_result("无法获取房间 ID")
            return

        try:
            power_levels = await client.get_power_levels(target_room_id)
            users = power_levels.get("users", {})

            admins = []
            mods = []

            for uid, level in users.items():
                if level >= 100:
                    admins.append((uid, level))
                elif level >= 50:
                    mods.append((uid, level))

            lines = [f"**房间权限列表** ({target_room_id})\n"]

            if admins:
                lines.append("**房主 (100+):**")
                for uid, level in admins:
                    lines.append(f"  - {uid} ({level})")
                lines.append("")

            if mods:
                lines.append("**管理员 (50+):**")
                for uid, level in mods:
                    lines.append(f"  - {uid} ({level})")

            if not admins and not mods:
                lines.append("没有设置特殊权限的用户")

            yield event.plain_result("\n".join(lines))

        except Exception as e:
            logger.error(f"获取管理员列表失败：{e}")
            yield event.plain_result(f"获取管理员列表失败：{e}")
