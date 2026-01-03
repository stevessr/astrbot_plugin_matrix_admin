"""
Matrix admin room commands.
"""

from astrbot.api import logger


async def admin_createroom(self, event, name: str, is_public: str = "no"):
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
            f"已创建房间 **{name}**\n"
            f"房间 ID: `{room_id}`\n"
            f"可见性：{visibility}"
        )
    except Exception as e:
        logger.error(f"创建房间失败：{e}")
        yield event.plain_result(f"创建房间失败：{e}")


async def admin_dm(self, event, user: str):
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
            f"已创建与 {user_id} 的私聊房间\n" f"房间 ID: `{room_id}`"
        )
    except Exception as e:
        logger.error(f"创建私聊房间失败：{e}")
        yield event.plain_result(f"创建私聊房间失败：{e}")


async def admin_setname(self, event, name: str):
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


async def admin_setavatar(self, event):
    client = self._get_matrix_client(event)
    if not client:
        yield event.plain_result("此命令仅在 Matrix 平台可用")
        return

    room_id = event.get_session_id()
    reply_event_id = None
    image_mxc_url = None

    try:
        raw_message = getattr(event, "message_obj", None)
        if raw_message:
            raw_event = getattr(raw_message, "raw_message", None)
            if raw_event:
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

    try:
        reply_event = await client.get_event(room_id, reply_event_id)
        if not reply_event:
            yield event.plain_result("无法获取被引用的消息")
            return

        reply_content = reply_event.get("content", {})
        msgtype = reply_content.get("msgtype", "")

        if msgtype == "m.image":
            image_mxc_url = reply_content.get("url")
        elif msgtype == "m.sticker" or reply_event.get("type") == "m.sticker":
            image_mxc_url = reply_content.get("url")
        else:
            yield event.plain_result(
                f"被引用的消息不是图片 (类型：{msgtype})\n"
                "请引用一条包含图片的消息"
            )
            return

        if not image_mxc_url:
            yield event.plain_result("无法从被引用的消息中获取图片 URL")
            return

        await client.set_avatar_url(image_mxc_url)
        yield event.plain_result(
            f"已成功修改 Bot 头像\n" f"头像 URL: `{image_mxc_url}`"
        )

    except Exception as e:
        logger.error(f"修改 Bot 头像失败：{e}")
        yield event.plain_result(f"修改 Bot 头像失败：{e}")
