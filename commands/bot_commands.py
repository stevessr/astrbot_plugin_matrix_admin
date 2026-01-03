"""
Matrix Admin Plugin - Bot Commands
Bot 资料管理相关命令
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .base import AdminCommandMixin


class BotCommandsMixin(AdminCommandMixin):
    """Bot 资料管理命令: setname, setavatar"""

    async def cmd_setname(self, event: AstrMessageEvent, name: str):
        """修改 Bot 的显示名称

        用法: /admin setname <新名称>

        示例:
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
            yield event.plain_result(f"已将 Bot 名称修改为: **{name.strip()}**")
        except Exception as e:
            logger.error(f"修改 Bot 名称失败: {e}")
            yield event.plain_result(f"修改 Bot 名称失败: {e}")

    async def cmd_setavatar(self, event: AstrMessageEvent):
        """通过引用图片修改 Bot 的头像

        用法: 引用一条包含图片的消息，然后发送 /admin setavatar

        示例:
            1. 先发送或找到一张图片
            2. 引用该图片消息
            3. 发送 /admin setavatar
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        # 获取原始消息中的引用信息
        room_id = event.get_session_id()
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
            logger.debug(f"获取引用事件 ID 失败: {e}")

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
                    f"被引用的消息不是图片 (类型: {msgtype})\n请引用一条包含图片的消息"
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
            logger.error(f"修改 Bot 头像失败: {e}")
            yield event.plain_result(f"修改 Bot 头像失败: {e}")
