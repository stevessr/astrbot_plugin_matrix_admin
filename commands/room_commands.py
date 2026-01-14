"""
Matrix Admin Plugin - Room Commands
房间管理相关命令
"""


from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .base import AdminCommandMixin


class RoomCommandsMixin(AdminCommandMixin):
    """房间管理命令：createroom, dm, alias, publicrooms, forget, upgrade, hierarchy, knock"""

    def _parse_room_alias(self, alias: str, room_id: str) -> str | None:
        alias = alias.strip()
        if not alias:
            return None
        if not alias.startswith("#"):
            alias = f"#{alias}"
        if ":" in alias:
            return alias
        if ":" in room_id:
            server = room_id.split(":", 1)[1]
            return f"{alias}:{server}"
        return None

    async def cmd_createroom(
        self,
        event: AstrMessageEvent,
        name: str,
        is_public: str = "no",
    ):
        """创建新房间

        用法：/admin createroom <房间名> [是否公开]

        示例：
            /admin createroom 新群组
            /admin createroom 公开频道 yes
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        public = is_public.lower() in ("yes", "true", "1", "public")

        try:
            result = await client.create_room(name=name, is_public=public)
            room_id = result.get("room_id", "未知")
            visibility = "公开" if public else "私有"
            yield event.plain_result(
                f"已创建房间 **{name}**\n房间 ID: `{room_id}`\n可见性：{visibility}"
            )
        except Exception as e:
            logger.error(f"创建房间失败：{e}")
            yield event.plain_result(f"创建房间失败：{e}")

    async def cmd_dm(self, event: AstrMessageEvent, user: str):
        """创建与用户的私聊房间

        用法：/admin dm <用户 ID>

        示例：
            /admin dm @friend:example.com
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
            result = await client.create_dm_room(user_id)
            room_id = result.get("room_id", "未知")
            yield event.plain_result(
                f"已创建与 {user_id} 的私聊房间\n房间 ID: `{room_id}`"
            )
        except Exception as e:
            logger.error(f"创建私聊房间失败：{e}")
            yield event.plain_result(f"创建私聊房间失败：{e}")

    async def cmd_alias_set(self, event: AstrMessageEvent, alias: str, room_id: str = ""):
        """设置房间别名

        用法：/admin aliasset <alias> [room_id]
        示例：/admin aliasset #myroom:example.com
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room = room_id.strip() if room_id else event.get_session_id()
        room_alias = self._parse_room_alias(alias, target_room)
        if not room_alias:
            yield event.plain_result("无效的别名格式")
            return

        try:
            await client.create_room_alias(room_alias, target_room)
            yield event.plain_result(f"已设置别名：{room_alias}")
        except Exception as e:
            logger.error(f"设置别名失败：{e}")
            yield event.plain_result(f"设置别名失败：{e}")

    async def cmd_alias_del(self, event: AstrMessageEvent, alias: str):
        """删除房间别名

        用法：/admin aliasdel <alias>
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_alias = self._parse_room_alias(alias, event.get_session_id())
        if not room_alias:
            yield event.plain_result("无效的别名格式")
            return

        try:
            await client.delete_room_alias(room_alias)
            yield event.plain_result(f"已删除别名：{room_alias}")
        except Exception as e:
            logger.error(f"删除别名失败：{e}")
            yield event.plain_result(f"删除别名失败：{e}")

    async def cmd_alias_get(self, event: AstrMessageEvent, alias: str):
        """解析房间别名

        用法：/admin aliasget <alias>
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_alias = self._parse_room_alias(alias, event.get_session_id())
        if not room_alias:
            yield event.plain_result("无效的别名格式")
            return

        try:
            result = await client.get_room_alias(room_alias)
            room_id = result.get("room_id", "未知")
            servers = result.get("servers", [])
            server_text = ", ".join(servers) if servers else "未知"
            yield event.plain_result(
                f"别名解析结果：\n房间 ID: `{room_id}`\n服务器：{server_text}"
            )
        except Exception as e:
            logger.error(f"解析别名失败：{e}")
            yield event.plain_result(f"解析别名失败：{e}")

    async def cmd_publicrooms(
        self, event: AstrMessageEvent, server: str = "", limit: int = 20
    ):
        """列出公共房间

        用法：/admin publicrooms [server] [limit]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        server_name = server.strip() or None
        try:
            result = await client.list_public_rooms(server=server_name, limit=limit)
            chunk = result.get("chunk", [])
            if not chunk:
                yield event.plain_result("没有公共房间可显示")
                return

            lines = ["公共房间列表："]
            for room in chunk:
                name = room.get("name") or room.get("canonical_alias") or "未命名"
                room_id = room.get("room_id", "未知")
                topic = room.get("topic")
                line = f"- {name} ({room_id})"
                if topic:
                    line += f" - {topic}"
                lines.append(line)

            yield event.plain_result("\n".join(lines))
        except Exception as e:
            logger.error(f"获取公共房间失败：{e}")
            yield event.plain_result(f"获取公共房间失败：{e}")

    async def cmd_forget(self, event: AstrMessageEvent, room_id: str = ""):
        """忘记房间（需先离开）

        用法：/admin forget [room_id]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room = room_id.strip() if room_id else event.get_session_id()
        try:
            await client.forget_room(target_room)
            yield event.plain_result(f"已忘记房间：`{target_room}`")
        except Exception as e:
            logger.error(f"忘记房间失败：{e}")
            yield event.plain_result(f"忘记房间失败：{e}")

    async def cmd_upgrade(self, event: AstrMessageEvent, new_version: str, room_id: str = ""):
        """升级房间版本

        用法：/admin upgrade <new_version> [room_id]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room = room_id.strip() if room_id else event.get_session_id()
        try:
            result = await client.upgrade_room(target_room, new_version)
            replacement = result.get("replacement_room", "未知")
            yield event.plain_result(
                f"已升级房间：`{target_room}`\n新房间：`{replacement}`"
            )
        except Exception as e:
            logger.error(f"升级房间失败：{e}")
            yield event.plain_result(f"升级房间失败：{e}")

    async def cmd_hierarchy(
        self, event: AstrMessageEvent, room_id: str = "", limit: int = 20
    ):
        """获取房间层级（Space）

        用法：/admin hierarchy [room_id] [limit]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room = room_id.strip() if room_id else event.get_session_id()
        try:
            result = await client.get_room_hierarchy(target_room, limit=limit)
            rooms = result.get("rooms", [])
            if not rooms:
                yield event.plain_result("未找到层级房间")
                return

            lines = ["房间层级："]
            for room in rooms:
                name = room.get("name") or room.get("canonical_alias") or "未命名"
                rid = room.get("room_id", "未知")
                lines.append(f"- {name} ({rid})")
            yield event.plain_result("\n".join(lines))
        except Exception as e:
            logger.error(f"获取房间层级失败：{e}")
            yield event.plain_result(f"获取房间层级失败：{e}")

    async def cmd_knock(
        self, event: AstrMessageEvent, room_id_or_alias: str, reason: str = ""
    ):
        """敲门请求加入房间

        用法：/admin knock <room_id_or_alias> [reason]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        try:
            result = await client.knock_room(
                room_id_or_alias, reason.strip() if reason else None
            )
            room_id = result.get("room_id", "未知")
            yield event.plain_result(f"已发起 knock 请求：`{room_id}`")
        except Exception as e:
            logger.error(f"敲门请求失败：{e}")
            yield event.plain_result(f"敲门请求失败：{e}")

    async def cmd_room_refresh(self, event: AstrMessageEvent, room_id: str = ""):
        """重新获取房间信息并刷新本地缓存

        用法：/admin roomrefresh [room_id|all]
        """
        try:
            from astrbot_plugin_matrix_adapter.room_member_store import (
                MatrixRoomMemberStore,
            )
            from astrbot_plugin_matrix_adapter.user_store import MatrixUserStore
        except Exception:
            yield event.plain_result("未安装 Matrix 适配器插件，无法刷新房间缓存")
            return

        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target = room_id.strip() if room_id else event.get_session_id()
        if not target:
            yield event.plain_result("无法获取房间 ID")
            return

        async def _refresh_room(target_room: str) -> tuple[bool, str]:
            try:
                members_resp = await client.get_room_members(target_room)
                chunk = members_resp.get("chunk", []) or []
            except Exception as e:
                logger.error(f"获取房间成员失败：{e}")
                return False, f"{target_room} 获取成员失败：{e}"

            members: dict[str, str] = {}
            member_avatars: dict[str, str] = {}
            for evt in chunk:
                if evt.get("type") != "m.room.member":
                    continue
                user_id = evt.get("state_key")
                if not user_id:
                    continue
                content = evt.get("content", {})
                if content.get("membership") != "join":
                    continue
                display_name = content.get("displayname") or user_id
                members[user_id] = display_name
                avatar_url = content.get("avatar_url")
                if avatar_url:
                    member_avatars[user_id] = avatar_url

            member_count = len(members)
            MatrixRoomMemberStore().upsert(
                room_id=target_room,
                members=members,
                member_avatars=member_avatars,
                member_count=member_count,
                is_direct=None,
            )

            user_store = MatrixUserStore()
            for user_id, display_name in members.items():
                user_store.upsert(user_id, display_name, member_avatars.get(user_id))

            room_name = None
            room_topic = None
            canonical_alias = None
            is_encrypted = False
            try:
                state_events = await client.get_room_state(target_room)
                for evt in state_events:
                    evt_type = evt.get("type")
                    content = evt.get("content", {})
                    if evt_type == "m.room.name":
                        room_name = content.get("name")
                    elif evt_type == "m.room.topic":
                        room_topic = content.get("topic")
                    elif evt_type == "m.room.canonical_alias":
                        canonical_alias = content.get("alias")
                    elif evt_type == "m.room.encryption":
                        is_encrypted = True
            except Exception as e:
                logger.debug(f"获取房间状态失败：{e}")

            lines = [f"已刷新房间信息：`{target_room}`"]
            if room_name:
                lines.append(f"名称：{room_name}")
            if canonical_alias:
                lines.append(f"别名：{canonical_alias}")
            lines.append(f"成员数：{member_count}")
            if room_topic:
                lines.append(f"主题：{room_topic}")
            lines.append(f"加密：{'是' if is_encrypted else '否'}")
            return True, "\n".join(lines)

        if target.lower() == "all":
            try:
                rooms = await client.get_joined_rooms()
            except Exception as e:
                yield event.plain_result(f"获取已加入房间失败：{e}")
                return

            if not rooms:
                yield event.plain_result("没有已加入的房间可刷新")
                return

            ok_count = 0
            fail_count = 0
            for room in rooms:
                ok, _ = await _refresh_room(room)
                if ok:
                    ok_count += 1
                else:
                    fail_count += 1

            yield event.plain_result(
                f"已刷新所有房间：成功 {ok_count} 个，失败 {fail_count} 个"
            )
            return

        ok, message = await _refresh_room(target)
        if ok:
            yield event.plain_result(message)
        else:
            yield event.plain_result(message)
