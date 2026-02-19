"""
Matrix Admin Plugin - Bot Commands
Bot 资料管理相关命令
"""

import time

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.star.filter.command import GreedyStr

from .base import AdminCommandMixin


class BotCommandsMixin(AdminCommandMixin):
    """Bot 资料管理命令：setname, setavatar, setstatus"""

    # 状态映射
    STATUS_MAP = {
        "online": ("online", "在线"),
        "在线": ("online", "在线"),
        "away": ("unavailable", "离开"),
        "离开": ("unavailable", "离开"),
        "unavailable": ("unavailable", "离开"),
        "busy": ("unavailable", "忙碌"),
        "忙碌": ("unavailable", "忙碌"),
        "offline": ("offline", "离线"),
        "离线": ("offline", "离线"),
    }

    async def cmd_setname(self, event: AstrMessageEvent, name: GreedyStr):
        """修改 Bot 的显示名称

        用法：/admin setname <新名称>

        示例：
            /admin setname MyBot
            /admin setname 我的机器人
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        if not name or not name.strip():
            yield event.plain_result("请提供有效的名称")
            return

        try:
            await client.set_display_name(name.strip())
            yield event.plain_result(f"已将 Bot 名称修改为：**{name.strip()}**")
        except Exception as e:
            logger.error(f"修改 Bot 名称失败：{e}")
            yield event.plain_result(f"修改 Bot 名称失败：{e}")

    async def cmd_setavatar(self, event: AstrMessageEvent):
        """通过引用图片修改 Bot 的头像

        用法：引用一条包含图片的消息，然后发送 /admin setavatar

        示例：
            1. 先发送或找到一张图片
            2. 引用该图片消息
            3. 发送 /admin setavatar
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        # 获取原始消息中的引用信息
        room_id = self._resolve_event_room_id(event)
        if not room_id:
            yield event.plain_result("无法获取房间 ID")
            return
        reply_event_id = None
        image_mxc_url = None

        # 尝试从原始消息中获取引用的事件 ID
        try:
            # message_obj.raw_message 是 RoomMessageEvent 对象
            raw_message = getattr(event, "message_obj", None)
            if raw_message:
                raw_event = getattr(raw_message, "raw_message", None)
                if raw_event:
                    # raw_event 是 RoomMessageEvent，有 content 属性
                    content = getattr(raw_event, "content", None)
                    if content and isinstance(content, dict):
                        relates_to = content.get("m.relates_to", {})
                        in_reply_to = relates_to.get("m.in_reply_to", {})
                        reply_event_id = in_reply_to.get("event_id")
        except Exception as e:
            logger.debug(f"获取引用事件 ID 失败：{e}")

        if not reply_event_id:
            yield event.plain_result(
                "请引用一条包含图片的消息后再使用此命令\n\n"
                "用法:\n"
                "1. 找到或发送一张图片\n"
                "2. 引用该图片消息\n"
                "3. 发送 /admin setavatar"
            )
            return

        # 获取被引用的消息内容
        try:
            reply_event = await client.get_event(room_id, reply_event_id)
            if not reply_event:
                yield event.plain_result("无法获取被引用的消息")
                return

            reply_content = reply_event.get("content", {})
            msgtype = reply_content.get("msgtype", "")

            # 检查是否是图片消息
            if msgtype == "m.image":
                # 获取图片的 mxc URL
                image_mxc_url = reply_content.get("url")
            elif msgtype == "m.sticker" or reply_event.get("type") == "m.sticker":
                # 贴纸也可以作为头像
                image_mxc_url = reply_content.get("url")
            else:
                yield event.plain_result(
                    f"被引用的消息不是图片 (类型：{msgtype})\n请引用一条包含图片的消息"
                )
                return

            if not image_mxc_url:
                yield event.plain_result("无法从被引用的消息中获取图片 URL")
                return

            # 设置头像
            await client.set_avatar_url(image_mxc_url)
            yield event.plain_result(
                f"已成功修改 Bot 头像\n头像 URL: `{image_mxc_url}`"
            )

        except Exception as e:
            logger.error(f"修改 Bot 头像失败：{e}")
            yield event.plain_result(f"修改 Bot 头像失败：{e}")

    async def cmd_setstatus(
        self, event: AstrMessageEvent, status: str = "", message: str = ""
    ):
        """修改 Bot 的在线状态

        用法：/admin setstatus <状态> [状态消息]

        状态：
            online / 在线 - 在线
            away / 离开 / busy / 忙碌 - 离开/忙碌
            offline / 离线 - 离线

        示例：
            /admin setstatus online
            /admin setstatus away 暂时离开
            /admin setstatus 忙碌 正在处理任务
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        if not status:
            # 显示帮助信息
            yield event.plain_result(
                "**修改 Bot 状态**\n\n"
                "用法：/admin setstatus <状态> [状态消息]\n\n"
                "可用状态:\n"
                "  - `online` / `在线` - 在线\n"
                "  - `away` / `离开` / `busy` / `忙碌` - 离开\n"
                "  - `offline` / `离线` - 离线\n\n"
                "示例:\n"
                "  /admin setstatus online\n"
                "  /admin setstatus away 暂时离开"
            )
            return

        # 解析状态
        status_key = status.lower().strip()
        if status_key not in self.STATUS_MAP:
            valid_statuses = ", ".join(
                [
                    f"`{k}`"
                    for k in ["online", "away", "offline", "在线", "离开", "离线"]
                ]
            )
            yield event.plain_result(
                f"无效的状态：`{status}`\n\n可用状态：{valid_statuses}"
            )
            return

        matrix_status, status_display = self.STATUS_MAP[status_key]
        now_ms = int(time.time() * 1000)
        currently_active = matrix_status == "online"

        try:
            await client.set_presence(
                matrix_status,
                message.strip() if message else None,
                last_active_ts=now_ms,
                currently_active=currently_active,
            )
            result_msg = f"已将 Bot 状态设置为：**{status_display}**"
            if message:
                result_msg += f"\n状态消息：{message.strip()}"
            yield event.plain_result(result_msg)
        except Exception as e:
            logger.error(f"修改 Bot 状态失败：{e}")
            yield event.plain_result(f"修改 Bot 状态失败：{e}")

    async def cmd_statusmsg(self, event: AstrMessageEvent, message: str = ""):
        """设置或清除 Bot 的状态消息（不改变在线状态）

        用法：/admin statusmsg [消息]

        示例：
            /admin statusmsg 正在处理任务
            /admin statusmsg 休息中，稍后回复
            /admin statusmsg  (留空则清除状态消息)
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        try:
            # 使用 online 状态，只更新状态消息
            status_msg = message.strip() if message else None
            await client.set_presence(
                "online",
                status_msg,
                last_active_ts=int(time.time() * 1000),
                currently_active=True,
            )

            if status_msg:
                yield event.plain_result(f"已设置状态消息：**{status_msg}**")
            else:
                yield event.plain_result("已清除状态消息")
        except Exception as e:
            logger.error(f"设置状态消息失败：{e}")
            yield event.plain_result(f"设置状态消息失败：{e}")

    async def cmd_purge_bot_messages(
        self, event: AstrMessageEvent, limit: int = 100, room_id: str = ""
    ):
        """清理机器人在房间内发送的历史消息

        用法：/admin purgebot [数量] [room_id]

        示例：
            /admin purgebot
            /admin purgebot 200
            /admin purgebot 200 !roomid:example.org
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            yield event.plain_result("数量必须是整数")
            return

        if limit <= 0:
            yield event.plain_result("数量必须大于 0")
            return

        target_room_id = room_id.strip() or str(event.get_session_id() or "").strip()
        if not target_room_id:
            yield event.plain_result("无法获取房间 ID")
            return

        bot_user_id = getattr(client, "user_id", None)
        if not bot_user_id:
            try:
                whoami = await client.whoami()
                bot_user_id = whoami.get("user_id")
            except Exception as e:
                yield event.plain_result(f"获取 Bot 用户 ID 失败：{e}")
                return

        scanned = 0
        redacted = 0
        failed = 0
        from_token = None
        remaining = limit

        while remaining > 0:
            batch_limit = min(100, remaining)
            try:
                resp = await client.room_messages(
                    room_id=target_room_id,
                    from_token=from_token,
                    direction="b",
                    limit=batch_limit,
                )
            except Exception as e:
                yield event.plain_result(f"拉取房间消息失败：{e}")
                return

            chunk = resp.get("chunk", []) or []
            if not chunk:
                break

            for msg in chunk:
                scanned += 1
                if msg.get("sender") != bot_user_id:
                    continue
                event_id = msg.get("event_id")
                if not event_id:
                    continue
                try:
                    await client.redact_event(
                        target_room_id, event_id, reason="admin purge bot messages"
                    )
                    redacted += 1
                except Exception:
                    failed += 1

            remaining -= len(chunk)
            from_token = resp.get("end")
            if not from_token:
                break

        yield event.plain_result(
            f"清理完成：扫描 {scanned} 条，撤回 {redacted} 条，失败 {failed} 条"
        )
