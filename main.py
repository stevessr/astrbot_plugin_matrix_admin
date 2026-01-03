"""
Matrix Admin Plugin - 提供 Matrix 房间管理命令

此插件依赖于 astrbot_plugin_matrix_adapter 提供的 Matrix 客户端。
提供用户管理、权限控制、房间管理等功能。
"""

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .commands import (
    BotCommandsMixin,
    IgnoreCommandsMixin,
    PowerCommandsMixin,
    QueryCommandsMixin,
    RoomCommandsMixin,
    UserCommandsMixin,
)


class Main(
    Star,
    UserCommandsMixin,
    PowerCommandsMixin,
    QueryCommandsMixin,
    IgnoreCommandsMixin,
    RoomCommandsMixin,
    BotCommandsMixin,
):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.context = context

    # ==================== 命令组定义 ====================

    @filter.command_group("admin")
    def admin_group(self):
        """Matrix 房间管理命令"""

    # -------------------- 用户管理命令 --------------------

    @admin_group.command("kick")
    async def admin_kick(self, event: AstrMessageEvent, user: str, reason: str = ""):
        """踢出用户

        用法：/admin kick <用户 ID> [原因]

        示例：
            /admin kick @baduser:example.com
            /admin kick @baduser:example.com 违规发言
        """
        async for result in self.cmd_kick(event, user, reason):
            yield result

    @admin_group.command("ban")
    async def admin_ban(self, event: AstrMessageEvent, user: str, reason: str = ""):
        """封禁用户

        用法：/admin ban <用户 ID> [原因]

        示例：
            /admin ban @spammer:example.com
            /admin ban @spammer:example.com 垃圾广告
        """
        async for result in self.cmd_ban(event, user, reason):
            yield result

    @admin_group.command("unban")
    async def admin_unban(self, event: AstrMessageEvent, user: str):
        """解除封禁

        用法：/admin unban <用户 ID>

        示例：
            /admin unban @user:example.com
        """
        async for result in self.cmd_unban(event, user):
            yield result

    @admin_group.command("invite")
    async def admin_invite(self, event: AstrMessageEvent, user: str):
        """邀请用户加入房间

        用法：/admin invite <用户 ID>

        示例：
            /admin invite @friend:example.com
        """
        async for result in self.cmd_invite(event, user):
            yield result

    # -------------------- 权限管理命令 --------------------

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
        async for result in self.cmd_promote(event, user, level):
            yield result

    @admin_group.command("demote")
    async def admin_demote(self, event: AstrMessageEvent, user: str):
        """降低用户权限为普通成员

        用法：/admin demote <用户 ID>

        示例：
            /admin demote @user:example.com
        """
        async for result in self.cmd_demote(event, user):
            yield result

    @admin_group.command("power")
    async def admin_power(self, event: AstrMessageEvent, user: str, level: int):
        """设置用户权限等级

        用法：/admin power <用户 ID> <等级>

        等级说明：
            0 - 普通成员
            50 - 管理员
            100 - 房主

        示例：
            /admin power @user:example.com 50
        """
        async for result in self.cmd_power(event, user, level):
            yield result

    @admin_group.command("admins")
    async def admin_list_admins(self, event: AstrMessageEvent):
        """列出房间管理员

        用法：/admin admins
        """
        async for result in self.cmd_admins(event):
            yield result

    # -------------------- 查询命令 --------------------

    @admin_group.command("whois")
    async def admin_whois(self, event: AstrMessageEvent, user: str):
        """查询用户信息

        用法：/admin whois <用户 ID>

        示例：
            /admin whois @user:example.com
        """
        async for result in self.cmd_whois(event, user):
            yield result

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
        async for result in self.cmd_search(event, keyword, limit):
            yield result

    # -------------------- 屏蔽列表命令 --------------------

    @admin_group.command("ignore")
    async def admin_ignore(self, event: AstrMessageEvent, user: str):
        """屏蔽用户

        用法：/admin ignore <用户 ID>

        示例：
            /admin ignore @annoying:example.com
        """
        async for result in self.cmd_ignore(event, user):
            yield result

    @admin_group.command("unignore")
    async def admin_unignore(self, event: AstrMessageEvent, user: str):
        """取消屏蔽用户

        用法：/admin unignore <用户 ID>

        示例：
            /admin unignore @user:example.com
        """
        async for result in self.cmd_unignore(event, user):
            yield result

    @admin_group.command("ignorelist")
    async def admin_ignorelist(self, event: AstrMessageEvent):
        """查看屏蔽列表

        用法：/admin ignorelist
        """
        async for result in self.cmd_ignorelist(event):
            yield result

    # -------------------- 房间管理命令 --------------------

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
        async for result in self.cmd_createroom(event, name, is_public):
            yield result

    @admin_group.command("dm")
    async def admin_dm(self, event: AstrMessageEvent, user: str):
        """创建与用户的私聊房间

        用法：/admin dm <用户 ID>

        示例：
            /admin dm @friend:example.com
        """
        async for result in self.cmd_dm(event, user):
            yield result

    # -------------------- Bot 资料管理命令 --------------------

    @admin_group.command("setname")
    async def admin_setname(self, event: AstrMessageEvent, name: str):
        """修改 Bot 的显示名称

        用法：/admin setname <新名称>

        示例：
            /admin setname MyBot
            /admin setname 我的机器人
        """
        async for result in self.cmd_setname(event, name):
            yield result

    @admin_group.command("setavatar")
    async def admin_setavatar(self, event: AstrMessageEvent):
        """通过引用图片修改 Bot 的头像

        用法：引用一条包含图片的消息，然后发送 /admin setavatar

        示例：
            1. 先发送或找到一张图片
            2. 引用该图片消息
            3. 发送 /admin setavatar
        """
        async for result in self.cmd_setavatar(event):
            yield result
