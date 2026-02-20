"""
Matrix Admin Plugin - Room Commands
房间管理相关命令
"""

import re

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .base import AdminCommandMixin


class RoomCommandsMixin(AdminCommandMixin):
    """房间管理命令：createroom, dm, alias, publicrooms, forget, upgrade, hierarchy, knock"""

    _ROOM_ID_RE = re.compile(r"^![^\s:]+:[^\s:]+$")
    _SERVER_NAME_RE = re.compile(r"^[A-Za-z0-9.-]+(?::\d{1,5})?$")

    @classmethod
    def _is_valid_room_id(cls, room_id: str) -> bool:
        text = str(room_id or "").strip()
        return bool(cls._ROOM_ID_RE.match(text))

    @classmethod
    def _is_valid_server_name(cls, server_name: str) -> bool:
        normalized = str(server_name or "").strip()
        return bool(normalized and cls._SERVER_NAME_RE.match(normalized))

    @staticmethod
    def _is_not_found_error(exc: Exception) -> bool:
        text = str(exc or "").strip().lower()
        return "404" in text or "not found" in text or "m_not_found" in text

    async def _get_room_power_context(
        self,
        client,
        room_id: str,
    ) -> tuple[int | None, int | None]:
        """返回 (bot_power, required_state_default)，失败时返回 (None, None)。"""
        try:
            power_levels = await client.get_power_levels(room_id)
        except Exception:
            return None, None

        if not isinstance(power_levels, dict):
            return None, None

        users = power_levels.get("users", {})
        if not isinstance(users, dict):
            users = {}

        bot_user_id = str(getattr(client, "user_id", "") or "")
        users_default = power_levels.get("users_default", 0)
        try:
            users_default = int(users_default)
        except (TypeError, ValueError):
            users_default = 0

        bot_power_raw = users.get(bot_user_id, users_default)
        try:
            bot_power = int(bot_power_raw)
        except (TypeError, ValueError):
            bot_power = users_default

        state_default = power_levels.get("state_default", 50)
        try:
            required_state_default = int(state_default)
        except (TypeError, ValueError):
            required_state_default = 50

        return bot_power, required_state_default

    async def _ensure_state_event_permission(
        self,
        client,
        room_id: str,
        event_type: str,
    ) -> tuple[bool, str]:
        """检查机器人在房间内发送指定 state event 的权限。"""
        bot_power, required_default = await self._get_room_power_context(client, room_id)
        if bot_power is None or required_default is None:
            return (
                False,
                (
                    f"无法校验房间 `{room_id}` 的权限，请确认机器人在房间内并可读取 power levels"
                ),
            )

        try:
            power_levels = await client.get_power_levels(room_id)
        except Exception:
            power_levels = {}
        if not isinstance(power_levels, dict):
            power_levels = {}

        events = power_levels.get("events", {})
        if not isinstance(events, dict):
            events = {}

        required = events.get(event_type, required_default)
        try:
            required_level = int(required)
        except (TypeError, ValueError):
            required_level = required_default

        if bot_power < required_level:
            return (
                False,
                (
                    f"权限不足：机器人在房间 `{room_id}` 的 power level 为 {bot_power}，"
                    f"修改 `{event_type}` 需要 >= {required_level}"
                ),
            )

        return True, ""

    def _parse_room_alias(
        self,
        alias: str,
        room_id: str = "",
        server_name: str = "",
    ) -> str | None:
        alias = alias.strip()
        if not alias:
            return None
        room_id = str(room_id or "")
        if not alias.startswith("#"):
            alias = f"#{alias}"
        if ":" in alias:
            return alias
        server = ""
        if ":" in room_id:
            server = room_id.split(":", 1)[1]
        if not server:
            server = str(server_name or "").strip()
        if server:
            return f"{alias}:{server}"
        return None

    def _resolve_server_name(self, event: AstrMessageEvent, room_id: str = "") -> str:
        room_id_text = str(room_id or "").strip()
        if ":" in room_id_text:
            return room_id_text.split(":", 1)[1]
        client = self._get_matrix_client(event)
        client_user_id = str(getattr(client, "user_id", "") or "")
        if ":" in client_user_id:
            return client_user_id.split(":", 1)[1]
        return ""

    @staticmethod
    def _resolve_target_room(event: AstrMessageEvent, room_id: str = "") -> str | None:
        if isinstance(room_id, str) and room_id.strip():
            return room_id.strip()
        session_room = str(event.get_session_id() or "").strip()
        return session_room or None

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

    async def cmd_alias_set(
        self, event: AstrMessageEvent, alias: str, room_id: str = ""
    ):
        """设置房间别名

        用法：/admin aliasset <alias> [room_id]
        示例：/admin aliasset #myroom:example.com
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room = self._resolve_target_room(event, room_id)
        if not target_room:
            yield event.plain_result("无法获取房间 ID")
            return
        server_name = self._resolve_server_name(event, target_room)
        room_alias = self._parse_room_alias(alias, target_room, server_name)
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

        server_name = self._resolve_server_name(event)
        room_alias = self._parse_room_alias(alias, "", server_name)
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

        server_name = self._resolve_server_name(event)
        room_alias = self._parse_room_alias(alias, "", server_name)
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

        target_room = self._resolve_target_room(event, room_id)
        if not target_room:
            yield event.plain_result("无法获取房间 ID")
            return
        try:
            await client.forget_room(target_room)
            yield event.plain_result(f"已忘记房间：`{target_room}`")
        except Exception as e:
            logger.error(f"忘记房间失败：{e}")
            yield event.plain_result(f"忘记房间失败：{e}")

    async def cmd_upgrade(
        self, event: AstrMessageEvent, new_version: str, room_id: str = ""
    ):
        """升级房间版本

        用法：/admin upgrade <new_version> [room_id]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        target_room = self._resolve_target_room(event, room_id)
        if not target_room:
            yield event.plain_result("无法获取房间 ID")
            return
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

        target_room = self._resolve_target_room(event, room_id)
        if not target_room:
            yield event.plain_result("无法获取房间 ID")
            return
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

    async def cmd_space_create(
        self,
        event: AstrMessageEvent,
        name: str,
        is_public: str = "no",
        topic: str = "",
    ):
        """创建 Matrix Space

        用法：/admin spacecreate <名称> [是否公开] [主题]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        name = str(name or "").strip()
        if not name:
            yield event.plain_result("Space 名称不能为空")
            return

        topic_text = str(topic or "").strip()
        normalized_public = str(is_public or "").strip().lower()
        valid_public_values = {"yes", "true", "1", "public", "no", "false", "0", "private", ""}
        if normalized_public not in valid_public_values:
            yield event.plain_result("is_public 参数无效，请使用 yes/no")
            return
        public = normalized_public in ("yes", "true", "1", "public")

        try:
            result = await client.create_room(
                name=name,
                topic=topic_text or None,
                is_public=public,
                creation_content={"type": "m.space"},
            )
            space_id = str(result.get("room_id", "") or "")
            if not space_id:
                yield event.plain_result("创建 Space 失败：未返回 room_id")
                return
            visibility = "公开" if public else "私有"
            lines = [
                f"已创建 Space **{name}**",
                f"Space ID: `{space_id}`",
                f"可见性：{visibility}",
            ]
            if topic_text:
                lines.append(f"主题：{topic_text}")
            yield event.plain_result("\n".join(lines))
        except Exception as e:
            logger.error(f"创建 Space 失败：{e}")
            yield event.plain_result(f"创建 Space 失败：{e}")

    async def cmd_space_link(
        self,
        event: AstrMessageEvent,
        space_id: str,
        child_room_id: str,
        suggested: str = "yes",
    ):
        """将房间关联到 Space

        用法：/admin spacelink <space_id> <room_id> [是否推荐]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        space_id = str(space_id or "").strip()
        child_room_id = str(child_room_id or "").strip()
        if not space_id or not child_room_id:
            yield event.plain_result("space_id 和 child_room_id 不能为空")
            return
        if not self._is_valid_room_id(space_id):
            yield event.plain_result("space_id 格式无效，应为 !room:server")
            return
        if not self._is_valid_room_id(child_room_id):
            yield event.plain_result("child_room_id 格式无效，应为 !room:server")
            return
        if space_id == child_room_id:
            yield event.plain_result("space_id 与 child_room_id 不能相同")
            return

        ok, permission_message = await self._ensure_state_event_permission(
            client,
            space_id,
            "m.space.child",
        )
        if not ok:
            yield event.plain_result(permission_message)
            return

        ok, permission_message = await self._ensure_state_event_permission(
            client,
            child_room_id,
            "m.space.parent",
        )
        if not ok:
            yield event.plain_result(permission_message)
            return

        server_name = self._resolve_server_name(event, child_room_id)
        if not server_name:
            server_name = self._resolve_server_name(event, space_id)
        if not self._is_valid_server_name(server_name):
            yield event.plain_result(
                "无法确定有效的 homeserver（via），请显式使用完整 room_id 并确保机器人已登录 Matrix"
            )
            return

        content = {
            "via": [server_name],
            "suggested": str(suggested or "").strip().lower() in (
                "yes",
                "true",
                "1",
                "on",
            ),
        }
        parent_content = {"via": [server_name]}

        previous_child_event = None
        try:
            previous_child_event = await client.get_room_state_event(
                room_id=space_id,
                event_type="m.space.child",
                state_key=child_room_id,
            )
        except Exception:
            previous_child_event = None

        child_link_created = False
        try:
            await client.set_room_state_event(
                room_id=space_id,
                event_type="m.space.child",
                content=content,
                state_key=child_room_id,
            )
            child_link_created = True
            await client.set_room_state_event(
                room_id=child_room_id,
                event_type="m.space.parent",
                content=parent_content,
                state_key=space_id,
            )
            yield event.plain_result(
                f"已将房间 `{child_room_id}` 挂载到 Space `{space_id}`（child/parent 已同步）"
            )
        except Exception as e:
            if child_link_created:
                rollback_content = (
                    previous_child_event
                    if isinstance(previous_child_event, dict) and previous_child_event
                    else {}
                )
                try:
                    await client.set_room_state_event(
                        room_id=space_id,
                        event_type="m.space.child",
                        content=rollback_content,
                        state_key=child_room_id,
                    )
                except Exception as rollback_error:
                    logger.error(f"Space 挂载回滚失败：{rollback_error}")
            logger.error(f"Space 挂载失败：{e}")
            yield event.plain_result(f"Space 挂载失败：{e}")

    async def cmd_space_unlink(
        self,
        event: AstrMessageEvent,
        space_id: str,
        child_room_id: str,
    ):
        """从 Space 移除子房间

        用法：/admin spaceunlink <space_id> <room_id>
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        space_id = str(space_id or "").strip()
        child_room_id = str(child_room_id or "").strip()
        if not space_id or not child_room_id:
            yield event.plain_result("space_id 和 child_room_id 不能为空")
            return
        if not self._is_valid_room_id(space_id):
            yield event.plain_result("space_id 格式无效，应为 !room:server")
            return
        if not self._is_valid_room_id(child_room_id):
            yield event.plain_result("child_room_id 格式无效，应为 !room:server")
            return
        if space_id == child_room_id:
            yield event.plain_result("space_id 与 child_room_id 不能相同")
            return

        ok, permission_message = await self._ensure_state_event_permission(
            client,
            space_id,
            "m.space.child",
        )
        if not ok:
            yield event.plain_result(permission_message)
            return

        ok, permission_message = await self._ensure_state_event_permission(
            client,
            child_room_id,
            "m.space.parent",
        )
        if not ok:
            yield event.plain_result(permission_message)
            return

        previous_child_event = None
        try:
            previous_child_event = await client.get_room_state_event(
                room_id=space_id,
                event_type="m.space.child",
                state_key=child_room_id,
            )
        except Exception:
            previous_child_event = None

        child_link_removed = False
        try:
            await client.set_room_state_event(
                room_id=space_id,
                event_type="m.space.child",
                content={},
                state_key=child_room_id,
            )
            child_link_removed = True
            await client.set_room_state_event(
                room_id=child_room_id,
                event_type="m.space.parent",
                content={},
                state_key=space_id,
            )
            yield event.plain_result(
                f"已从 Space `{space_id}` 移除子房间 `{child_room_id}`（child/parent 已同步）"
            )
        except Exception as e:
            if child_link_removed and not self._is_not_found_error(e):
                rollback_content = (
                    previous_child_event
                    if isinstance(previous_child_event, dict) and previous_child_event
                    else None
                )
                if rollback_content is None:
                    server_name = self._resolve_server_name(event, child_room_id)
                    if not server_name:
                        server_name = self._resolve_server_name(event, space_id)
                    if self._is_valid_server_name(server_name):
                        rollback_content = {"via": [server_name], "suggested": True}
                if rollback_content is not None:
                    try:
                        await client.set_room_state_event(
                            room_id=space_id,
                            event_type="m.space.child",
                            content=rollback_content,
                            state_key=child_room_id,
                        )
                    except Exception as rollback_error:
                        logger.error(f"Space 解绑回滚失败：{rollback_error}")
            logger.error(f"Space 解绑失败：{e}")
            yield event.plain_result(f"Space 解绑失败：{e}")

    async def cmd_space_children(
        self,
        event: AstrMessageEvent,
        space_id: str,
        limit: int = 20,
    ):
        """查看 Space 子房间列表

        用法：/admin spacechildren <space_id> [limit]
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        space_id = str(space_id or "").strip()
        if not space_id:
            yield event.plain_result("space_id 不能为空")
            return
        if not self._is_valid_room_id(space_id):
            yield event.plain_result("space_id 格式无效，应为 !room:server")
            return

        try:
            requested_limit = max(1, min(int(limit), 500))
        except (TypeError, ValueError):
            requested_limit = 20

        page_size = min(requested_limit, 100)
        next_token = None
        rooms: list[dict] = []
        room_ids: set[str] = set()

        try:
            while len(rooms) < requested_limit:
                request_kwargs = {"limit": page_size}
                if next_token:
                    request_kwargs["from_token"] = next_token
                result = await client.get_room_hierarchy(space_id, **request_kwargs)
                page_rooms = result.get("rooms", [])
                for room in page_rooms:
                    if not isinstance(room, dict):
                        continue
                    rid = str(room.get("room_id", "") or "")
                    if rid and rid in room_ids:
                        continue
                    if rid:
                        room_ids.add(rid)
                    rooms.append(room)
                    if len(rooms) >= requested_limit:
                        break
                next_token = result.get("next_batch")
                if not next_token or not page_rooms:
                    break

            if not rooms:
                yield event.plain_result("该 Space 下暂无子房间")
                return

            lines = [f"Space `{space_id}` 子房间（显示 {len(rooms)} 项）："]
            for room in rooms:
                name = room.get("name") or room.get("canonical_alias") or "未命名"
                rid = room.get("room_id", "未知")
                lines.append(f"- {name} ({rid})")
            if next_token and len(rooms) >= requested_limit:
                lines.append("- ...（仍有更多子房间，调大 limit 可查看更多）")
            yield event.plain_result("\n".join(lines))
        except Exception as e:
            logger.error(f"获取 Space 子房间失败：{e}")
            yield event.plain_result(f"获取 Space 子房间失败：{e}")

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

        target = self._resolve_target_room(event, room_id)
        if not target:
            yield event.plain_result("无法获取房间 ID")
            return

        async def _refresh_room(target_room: str) -> tuple[bool, str]:
            try:
                members_resp = await client.get_room_members(target_room)
                if not isinstance(members_resp, dict):
                    return False, f"{target_room} 获取成员失败：返回格式无效"
                chunk = members_resp.get("chunk", []) or []
                if not isinstance(chunk, list):
                    chunk = []
            except Exception as e:
                logger.error(f"获取房间成员失败：{e}")
                return False, f"{target_room} 获取成员失败：{e}"

            members: dict[str, str] = {}
            member_avatars: dict[str, str] = {}
            for evt in chunk:
                if not isinstance(evt, dict):
                    continue
                if evt.get("type") != "m.room.member":
                    continue
                user_id = evt.get("state_key")
                if not user_id:
                    continue
                content = evt.get("content", {})
                if not isinstance(content, dict):
                    continue
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
                if not isinstance(state_events, list):
                    state_events = []
                for evt in state_events:
                    if not isinstance(evt, dict):
                        continue
                    evt_type = evt.get("type")
                    content = evt.get("content", {})
                    if not isinstance(content, dict):
                        continue
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
                if isinstance(rooms, dict):
                    rooms = rooms.get("joined_rooms", [])
                if not isinstance(rooms, (list, tuple, set)):
                    yield event.plain_result("获取已加入房间失败：返回格式无效")
                    return
            except Exception as e:
                yield event.plain_result(f"获取已加入房间失败：{e}")
                return

            if not rooms:
                yield event.plain_result("没有已加入的房间可刷新")
                return

            ok_count = 0
            fail_count = 0
            for room in rooms:
                room_id = str(room or "").strip()
                if not room_id:
                    fail_count += 1
                    continue
                ok, _ = await _refresh_room(room_id)
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
