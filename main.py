"""
Matrix Admin Plugin - 提供 Matrix 房间管理命令

此插件依赖于 astrbot_plugin_matrix_adapter 提供的 Matrix 客户端。
提供用户管理、权限控制、房间管理等功能。
"""

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .commands import (
    AdminCommandMixin,
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

    # ========== Command Bindings ==========
    # 装饰器必须定义在 main.py 中，否则 handler 的 __module__ 不匹配

    @filter.command_group("admin")
    def admin_group(self):
        """Matrix 房间管理命令"""

    @admin_group.command("kick")
    async def admin_kick(self, event: AstrMessageEvent, user: str, reason: str = ""):
        """踢出用户"""
        async for result in self.cmd_kick(event, user, reason):
            yield result

    @admin_group.command("ban")
    async def admin_ban(self, event: AstrMessageEvent, user: str, reason: str = ""):
        """封禁用户"""
        async for result in self.cmd_ban(event, user, reason):
            yield result

    @admin_group.command("unban")
    async def admin_unban(self, event: AstrMessageEvent, user: str):
        """解除封禁"""
        async for result in self.cmd_unban(event, user):
            yield result

    @admin_group.command("invite")
    async def admin_invite(self, event: AstrMessageEvent, user: str):
        """邀请用户加入房间"""
        async for result in self.cmd_invite(event, user):
            yield result

    @admin_group.command("promote")
    async def admin_promote(
        self, event: AstrMessageEvent, user: str, level: str = "mod"
    ):
        """提升用户权限"""
        async for result in self.cmd_promote(event, user, level):
            yield result

    @admin_group.command("demote")
    async def admin_demote(self, event: AstrMessageEvent, user: str):
        """降低用户权限为普通成员"""
        async for result in self.cmd_demote(event, user):
            yield result

    @admin_group.command("power")
    async def admin_power(self, event: AstrMessageEvent, user: str, level: int):
        """设置用户权限等级"""
        async for result in self.cmd_power(event, user, level):
            yield result

    @admin_group.command("admins")
    async def admin_list_admins(self, event: AstrMessageEvent):
        """列出房间管理员"""
        async for result in self.cmd_admins(event):
            yield result

    @admin_group.command("whois")
    async def admin_whois(self, event: AstrMessageEvent, user: str):
        """查询用户信息"""
        async for result in self.cmd_whois(event, user):
            yield result

    @admin_group.command("search")
    async def admin_search(
        self, event: AstrMessageEvent, keyword: str, limit: int = 10
    ):
        """搜索用户"""
        async for result in self.cmd_search(event, keyword, limit):
            yield result

    @admin_group.command("ignore")
    async def admin_ignore(self, event: AstrMessageEvent, user: str):
        """屏蔽用户"""
        async for result in self.cmd_ignore(event, user):
            yield result

    @admin_group.command("unignore")
    async def admin_unignore(self, event: AstrMessageEvent, user: str):
        """取消屏蔽用户"""
        async for result in self.cmd_unignore(event, user):
            yield result

    @admin_group.command("ignorelist")
    async def admin_ignorelist(self, event: AstrMessageEvent):
        """查看屏蔽列表"""
        async for result in self.cmd_ignorelist(event):
            yield result

    @admin_group.command("createroom")
    async def admin_createroom(
        self, event: AstrMessageEvent, name: str, is_public: str = "no"
    ):
        """创建新房间"""
        async for result in self.cmd_createroom(event, name, is_public):
            yield result

    @admin_group.command("dm")
    async def admin_dm(self, event: AstrMessageEvent, user: str):
        """创建与用户的私聊房间"""
        async for result in self.cmd_dm(event, user):
            yield result

    @admin_group.command("setname")
    async def admin_setname(self, event: AstrMessageEvent, name: str):
        """修改 Bot 的显示名称"""
        async for result in self.cmd_setname(event, name):
            yield result

    @admin_group.command("setavatar")
    async def admin_setavatar(self, event: AstrMessageEvent):
        """通过引用图片修改 Bot 的头像"""
        async for result in self.cmd_setavatar(event):
            yield result

    @admin_group.command("setstatus")
    async def admin_setstatus(
        self, event: AstrMessageEvent, status: str = "", message: str = ""
    ):
        """修改 Bot 的在线状态"""
        async for result in self.cmd_setstatus(event, status, message):
            yield result

    @admin_group.command("statusmsg")
    async def admin_statusmsg(self, event: AstrMessageEvent, message: str = ""):
        """设置或清除 Bot 的状态消息"""
        async for result in self.cmd_statusmsg(event, message):
            yield result
