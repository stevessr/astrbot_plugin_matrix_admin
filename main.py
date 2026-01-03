"""
Matrix Admin Plugin - 提供 Matrix 房间管理命令

此插件依赖于 astrbot_plugin_matrix_adapter 提供的 Matrix 客户端。
提供用户管理、权限控制、房间管理等功能。
"""

from typing import TYPE_CHECKING

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

if TYPE_CHECKING:
    from astrbot_plugin_matrix_adapter.client import MatrixHTTPClient


class Main(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.context = context

    def _get_matrix_client(self, event: AstrMessageEvent):
        """获取 Matrix 客户端实例"""
        if event.get_platform_name() != "matrix":
            return None

        try:
            for platform in self.context.platform_manager.platform_insts:
                meta = platform.meta()
                if meta.name == "matrix" and meta.id == event.get_platform_id():
                    if hasattr(platform, "client"):
                        return platform.client
        except Exception as e:
            logger.debug(f"获取 Matrix 客户端失败：{e}")

        return None

    def _parse_user_id(self, user_input: str, event: AstrMessageEvent) -> str | None:
        """解析用户输入为完整的 Matrix 用户 ID"""
        if not user_input:
            return None

        # 已经是完整的用户 ID
        if user_input.startswith("@") and ":" in user_input:
            return user_input

        # 尝试从房间 ID 提取服务器域名
        room_id = event.get_session_id()
        if ":" in room_id:
            server = room_id.split(":", 1)[1]
            if user_input.startswith("@"):
                return f"{user_input}:{server}"
            else:
                return f"@{user_input}:{server}"

        return None

    # ==================== 用户管理命令组 ====================

    @filter.command_group("admin")
    def admin_group(self):
        """Matrix 房间管理命令"""

    # -------------------- 踢出/封禁 --------------------

    @admin_group.command("kick")
    async def admin_kick(
        self, event: AstrMessageEvent, user: str, reason: str = ""
    ):
        """踢出用户

        用法：/admin kick <用户 ID> [原因]

        示例：
            /admin kick @baduser:example.com
            /admin kick @baduser:example.com 违规发言
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
            await client.kick_user(room_id, user_id, reason or None)
            msg = f"已将 {user_id} 踢出房间"
            if reason:
                msg += f"\n原因：{reason}"
            yield event.plain_result(msg)
        except Exception as e:
            logger.error(f"踢出用户失败：{e}")
            yield event.plain_result(f"踢出用户失败：{e}")

    @admin_group.command("ban")
    async def admin_ban(
        self, event: AstrMessageEvent, user: str, reason: str = ""
    ):
        """封禁用户

        用法：/admin ban <用户 ID> [原因]

        示例：
            /admin ban @spammer:example.com
            /admin ban @spammer:example.com 垃圾广告
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
            await client.ban_user(room_id, user_id, reason or None)
            msg = f"已封禁 {user_id}"
            if reason:
                msg += f"\n原因：{reason}"
            yield event.plain_result(msg)
        except Exception as e:
            logger.error(f"封禁用户失败：{e}")
            yield event.plain_result(f"封禁用户失败：{e}")

    @admin_group.command("unban")
    async def admin_unban(self, event: AstrMessageEvent, user: str):
        """解除封禁

        用法：/admin unban <用户 ID>

        示例：
            /admin unban @user:example.com
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
            await client.unban_user(room_id, user_id)
            yield event.plain_result(f"已解除 {user_id} 的封禁")
        except Exception as e:
            logger.error(f"解除封禁失败：{e}")
            yield event.plain_result(f"解除封禁失败：{e}")

    # -------------------- 邀请 --------------------

    @admin_group.command("invite")
    async def admin_invite(self, event: AstrMessageEvent, user: str):
        """邀请用户加入房间

        用法：/admin invite <用户 ID>

        示例：
            /admin invite @friend:example.com
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
            await client.invite_user(room_id, user_id)
            yield event.plain_result(f"已邀请 {user_id} 加入房间")
        except Exception as e:
            logger.error(f"邀请用户失败：{e}")
            yield event.plain_result(f"邀请用户失败：{e}")

    # -------------------- 权限管理 --------------------

    @admin_group.command("promote")
    async def admin_promote(
        self, event: AstrMessageEvent, user: str, level: str = "mod"
    ):
        """提升用户权限

        用法：/admin promote <用户 ID> [级别]

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

        user_id = self._parse_user_id(user, event)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        room_id = event.get_session_id()

        level_map = {
            "mod": 50,
            "moderator": 50,
            "admin": 100,
            "owner": 100,
        }

        power_level = level_map.get(level.lower(), 50)
        level_name = "管理员" if power_level == 50 else "房主"

        try:
            await client.set_user_power_level(room_id, user_id, power_level)
            yield event.plain_result(
                f"已将 {user_id} 提升为{level_name} (权限等级：{power_level})"
            )
        except Exception as e:
            logger.error(f"提升权限失败：{e}")
            yield event.plain_result(f"提升权限失败：{e}")

    @admin_group.command("demote")
    async def admin_demote(self, event: AstrMessageEvent, user: str):
        """降低用户权限为普通成员

        用法：/admin demote <用户 ID>

        示例：
            /admin demote @user:example.com
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
            await client.set_user_power_level(room_id, user_id, 0)
            yield event.plain_result(f"已将 {user_id} 降级为普通成员")
        except Exception as e:
            logger.error(f"降级失败：{e}")
            yield event.plain_result(f"降级失败：{e}")

    @admin_group.command("power")
    async def admin_power(
        self, event: AstrMessageEvent, user: str, level: int
    ):
        """设置用户权限等级

        用法：/admin power <用户 ID> <等级>

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

        user_id = self._parse_user_id(user, event)
        if not user_id:
            yield event.plain_result("无效的用户 ID")
            return

        room_id = event.get_session_id()

        try:
            await client.set_user_power_level(room_id, user_id, level)
            yield event.plain_result(
                f"已将 {user_id} 的权限等级设置为 {level}"
            )
        except Exception as e:
            logger.error(f"设置权限失败：{e}")
            yield event.plain_result(f"设置权限失败：{e}")

    # -------------------- 查询 --------------------

    @admin_group.command("admins")
    async def admin_list_admins(self, event: AstrMessageEvent):
        """列出房间管理员

        用法：/admin admins
        """
        client = self._get_matrix_client(event)
        if not client:
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        room_id = event.get_session_id()

        try:
            power_levels = await client.get_power_levels(room_id)
            users = power_levels.get("users", {})

            admins = []
            mods = []

            for uid, level in users.items():
                if level >= 100:
                    admins.append((uid, level))
                elif level >= 50:
                    mods.append((uid, level))

            lines = ["**房间权限列表**\n"]

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

    @admin_group.command("whois")
    async def admin_whois(self, event: AstrMessageEvent, user: str):
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

    @admin_group.command("search")
    async def admin_search(
        self, event: AstrMessageEvent, keyword: str, limit: int = 10
    ):
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

    # -------------------- 屏蔽列表 --------------------

    @admin_group.command("ignore")
    async def admin_ignore(self, event: AstrMessageEvent, user: str):
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

    @admin_group.command("unignore")
    async def admin_unignore(self, event: AstrMessageEvent, user: str):
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

    @admin_group.command("ignorelist")
    async def admin_ignorelist(self, event: AstrMessageEvent):
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

    # -------------------- 房间管理 --------------------

    @admin_group.command("createroom")
    async def admin_createroom(
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
                f"已创建房间 **{name}**\n"
                f"房间 ID: `{room_id}`\n"
                f"可见性：{visibility}"
            )
        except Exception as e:
            logger.error(f"创建房间失败：{e}")
            yield event.plain_result(f"创建房间失败：{e}")

    @admin_group.command("dm")
    async def admin_dm(self, event: AstrMessageEvent, user: str):
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
                f"已创建与 {user_id} 的私聊房间\n"
                f"房间 ID: `{room_id}`"
            )
        except Exception as e:
            logger.error(f"创建私聊房间失败：{e}")
            yield event.plain_result(f"创建私聊房间失败：{e}")

    # -------------------- Bot 资料管理 --------------------

    @admin_group.command("setname")
    async def admin_setname(self, event: AstrMessageEvent, name: str):
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

    @admin_group.command("setavatar")
    async def admin_setavatar(self, event: AstrMessageEvent):
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
                    f"被引用的消息不是图片 (类型：{msgtype})\n"
                    "请引用一条包含图片的消息"
                )
                return

            if not image_mxc_url:
                yield event.plain_result("无法从被引用的消息中获取图片 URL")
                return

            # 设置头像
            await client.set_avatar_url(image_mxc_url)
            yield event.plain_result(
                f"已成功修改 Bot 头像\n"
                f"头像 URL: `{image_mxc_url}`"
            )

        except Exception as e:
            logger.error(f"修改 Bot 头像失败：{e}")
            yield event.plain_result(f"修改 Bot 头像失败：{e}")
