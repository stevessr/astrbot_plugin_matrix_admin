"""
Matrix Admin Plugin - 提供 Matrix 房间管理命令

此插件依赖于 astrbot_plugin_matrix_adapter 提供的 Matrix 客户端。
提供用户管理、权限控制、房间管理等功能。
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.star.filter.command import GreedyStr
from astrbot.core.star.filter.permission import PermissionType

from .commands import (
    BotCommandsMixin,
    IgnoreCommandsMixin,
    PowerCommandsMixin,
    QueryCommandsMixin,
    RoomCommandsMixin,
    UserCommandsMixin,
)


@register(
    "astrbot_plugin_matrix_admin",
    "stevessr",
    "Matrix 房间管理插件，提供用户管理、权限控制、封禁踢出等管理命令",
    "0.1.0",
)
class Matrix_Admin_Plugin(
    Star,
    UserCommandsMixin,
    PowerCommandsMixin,
    QueryCommandsMixin,
    IgnoreCommandsMixin,
    RoomCommandsMixin,
    BotCommandsMixin,
):
    def __init__(self, context: Context, config: dict | None = None) -> None:
        super().__init__(context, config)
        self.context = context
        self.config = config or {}
        self.verify_room_id = str(
            self.config.get("matrix_admin_verify_room_id", "") or ""
        ).strip()
        self.verify_room_templates = self._normalize_verify_room_templates(
            self.config.get("matrix_admin_verify_temple_list")
            or self.config.get("matrix_admin_verify_template_list")
        )
        self._maybe_apply_admin_room_config()

    @staticmethod
    def _normalize_room_ids(raw_rooms) -> list[str]:
        if isinstance(raw_rooms, str):
            raw_iterable = [part for part in raw_rooms.split(",")]
        elif isinstance(raw_rooms, list):
            raw_iterable = raw_rooms
        else:
            return []

        rooms: list[str] = []
        for room in raw_iterable:
            room_id = str(room or "").strip()
            if room_id and room_id not in rooms:
                rooms.append(room_id)
        return rooms

    def _normalize_verify_room_templates(self, raw_templates) -> dict[str, list[str]]:
        if raw_templates in (None, ""):
            logger.debug("[MatrixAdmin] 未配置 matrix_admin_verify_temple_list")
            return {}
        if not isinstance(raw_templates, list):
            logger.warning(
                "[MatrixAdmin] matrix_admin_verify_temple_list 格式非法，期望 list，已忽略"
            )
            return {}

        normalized: dict[str, list[str]] = {}
        for index, item in enumerate(raw_templates):
            if not isinstance(item, dict):
                logger.warning(
                    "[MatrixAdmin] matrix_admin_verify_temple_list[%s] 不是对象，已跳过",
                    index,
                )
                continue

            adapter_name = str(item.get("adapter_name", "") or "").strip()
            rooms = self._normalize_room_ids(item.get("rooms", []))

            if not adapter_name:
                logger.warning(
                    "[MatrixAdmin] matrix_admin_verify_temple_list[%s] 缺少 adapter_name，已跳过",
                    index,
                )
                continue
            if not rooms:
                logger.warning(
                    "[MatrixAdmin] matrix_admin_verify_temple_list[%s] rooms 为空，已跳过",
                    index,
                )
                continue

            merged = normalized.setdefault(adapter_name, [])
            for room_id in rooms:
                if room_id not in merged:
                    merged.append(room_id)

        logger.debug(
            "[MatrixAdmin] 验证通知模板归一化完成：adapters=%s",
            list(normalized.keys()),
        )
        return normalized

    def _maybe_apply_admin_room_config(self):
        matrix_utils_cls = self._get_matrix_utils_cls()
        if matrix_utils_cls is None:
            return

        adapter_ids = matrix_utils_cls.list_matrix_platform_ids(self.context)
        if not adapter_ids:
            logger.debug("[MatrixAdmin] 未发现 Matrix adapter，跳过验证通知配置下发")
            return

        for adapter_id in adapter_ids:
            e2ee_manager = matrix_utils_cls.get_matrix_e2ee_manager(
                self.context,
                adapter_id,
                fallback_to_first=False,
            )
            verification = (
                getattr(e2ee_manager, "_verification", None) if e2ee_manager else None
            )
            if not verification:
                continue

            rooms = self.verify_room_templates.get(adapter_id, [])
            verification.set_admin_notify_rooms(rooms)
            verification.set_admin_notify_room(self.verify_room_id)
            logger.debug(
                "[MatrixAdmin] 已下发验证通知配置：adapter=%s rooms=%s fallback=%s",
                adapter_id,
                rooms,
                bool(self.verify_room_id),
            )

    @staticmethod
    def _split_reason_and_room_id(reason_or_room: str) -> tuple[str, str]:
        raw = str(reason_or_room or "").strip()
        if not raw:
            return "", ""
        parts = raw.split()
        last_part = parts[-1]
        if last_part.startswith("!") and ":" in last_part:
            return " ".join(parts[:-1]).strip(), last_part
        return raw, ""

    @filter.on_astrbot_loaded()
    async def on_astrbot_loaded(self):
        self._maybe_apply_admin_room_config()

    @filter.on_platform_loaded()
    async def on_platform_loaded(self):
        self._maybe_apply_admin_room_config()

    # ========== Command Bindings ==========
    # 装饰器必须定义在 main.py 中，否则 handler 的 __module__ 不匹配

    @filter.command_group("admin")
    def admin_group(self):
        """Matrix 房间管理命令"""

    @admin_group.command("kick")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_kick(
        self,
        event: AstrMessageEvent,
        user: str,
        reason_or_room: GreedyStr = "",
    ):
        """踢出用户"""
        reason, room_id = self._split_reason_and_room_id(reason_or_room)
        async for result in self.cmd_kick(event, user, reason, room_id):
            yield result

    @admin_group.command("ban")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_ban(
        self,
        event: AstrMessageEvent,
        user: str,
        reason_or_room: GreedyStr = "",
    ):
        """封禁用户"""
        reason, room_id = self._split_reason_and_room_id(reason_or_room)
        async for result in self.cmd_ban(event, user, reason, room_id):
            yield result

    @admin_group.command("unban")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_unban(self, event: AstrMessageEvent, user: str, room_id: str = ""):
        """解除封禁"""
        async for result in self.cmd_unban(event, user, room_id):
            yield result

    @admin_group.command("invite")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_invite(self, event: AstrMessageEvent, user: str, room_id: str = ""):
        """邀请用户加入房间"""
        async for result in self.cmd_invite(event, user, room_id):
            yield result

    @admin_group.command("promote")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_promote(
        self,
        event: AstrMessageEvent,
        user: str,
        level: str = "mod",
        room_id: str = "",
    ):
        """提升用户权限"""
        async for result in self.cmd_promote(event, user, level, room_id):
            yield result

    @admin_group.command("demote")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_demote(self, event: AstrMessageEvent, user: str, room_id: str = ""):
        """降低用户权限为普通成员"""
        async for result in self.cmd_demote(event, user, room_id):
            yield result

    @admin_group.command("power")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_power(
        self, event: AstrMessageEvent, user: str, level: int, room_id: str = ""
    ):
        """设置用户权限等级"""
        async for result in self.cmd_power(event, user, level, room_id):
            yield result

    @admin_group.command("admins")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_list_admins(self, event: AstrMessageEvent, room_id: str = ""):
        """列出房间管理员"""
        async for result in self.cmd_admins(event, room_id):
            yield result

    @admin_group.command("whois")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_whois(self, event: AstrMessageEvent, user: str):
        """查询用户信息"""
        async for result in self.cmd_whois(event, user):
            yield result

    @admin_group.command("search")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_search(
        self, event: AstrMessageEvent, keyword: str, limit: int = 10
    ):
        """搜索用户"""
        async for result in self.cmd_search(event, keyword, limit):
            yield result

    @admin_group.command("ignore")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_ignore(self, event: AstrMessageEvent, user: str):
        """屏蔽用户"""
        async for result in self.cmd_ignore(event, user):
            yield result

    @admin_group.command("unignore")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_unignore(self, event: AstrMessageEvent, user: str):
        """取消屏蔽用户"""
        async for result in self.cmd_unignore(event, user):
            yield result

    @admin_group.command("ignorelist")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_ignorelist(self, event: AstrMessageEvent):
        """查看屏蔽列表"""
        async for result in self.cmd_ignorelist(event):
            yield result

    @admin_group.command("createroom")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_createroom(
        self, event: AstrMessageEvent, name: str, is_public: str = "no"
    ):
        """创建新房间"""
        async for result in self.cmd_createroom(event, name, is_public):
            yield result

    @admin_group.command("dm")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_dm(self, event: AstrMessageEvent, user: str):
        """创建与用户的私聊房间"""
        async for result in self.cmd_dm(event, user):
            yield result

    @admin_group.command("aliasset")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_alias_set(
        self, event: AstrMessageEvent, alias: str, room_id: str = ""
    ):
        """设置房间别名"""
        async for result in self.cmd_alias_set(event, alias, room_id):
            yield result

    @admin_group.command("aliasdel")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_alias_del(self, event: AstrMessageEvent, alias: str):
        """删除房间别名"""
        async for result in self.cmd_alias_del(event, alias):
            yield result

    @admin_group.command("aliasget")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_alias_get(self, event: AstrMessageEvent, alias: str):
        """解析房间别名"""
        async for result in self.cmd_alias_get(event, alias):
            yield result

    @admin_group.command("publicrooms")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_publicrooms(
        self, event: AstrMessageEvent, server: str = "", limit: int = 20
    ):
        """列出公共房间"""
        async for result in self.cmd_publicrooms(event, server, limit):
            yield result

    @admin_group.command("forget")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_forget(self, event: AstrMessageEvent, room_id: str = ""):
        """忘记房间"""
        async for result in self.cmd_forget(event, room_id):
            yield result

    @admin_group.command("upgrade")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_upgrade(
        self, event: AstrMessageEvent, new_version: str, room_id: str = ""
    ):
        """升级房间版本"""
        async for result in self.cmd_upgrade(event, new_version, room_id):
            yield result

    @admin_group.command("hierarchy")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_hierarchy(
        self, event: AstrMessageEvent, room_id: str = "", limit: int = 20
    ):
        """获取房间层级"""
        async for result in self.cmd_hierarchy(event, room_id, limit):
            yield result

    @admin_group.command("spacecreate")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_spacecreate(
        self,
        event: AstrMessageEvent,
        name: str,
        is_public: str = "no",
        topic: str = "",
    ):
        """创建 Space"""
        async for result in self.cmd_space_create(event, name, is_public, topic):
            yield result

    @admin_group.command("spacelink")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_spacelink(
        self,
        event: AstrMessageEvent,
        space_id: str,
        child_room_id: str,
        suggested: str = "yes",
    ):
        """挂载 Space 子房间"""
        async for result in self.cmd_space_link(
            event,
            space_id,
            child_room_id,
            suggested,
        ):
            yield result

    @admin_group.command("spaceunlink")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_spaceunlink(
        self,
        event: AstrMessageEvent,
        space_id: str,
        child_room_id: str,
    ):
        """移除 Space 子房间"""
        async for result in self.cmd_space_unlink(event, space_id, child_room_id):
            yield result

    @admin_group.command("spacechildren")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_spacechildren(
        self,
        event: AstrMessageEvent,
        space_id: str,
        limit: int = 20,
    ):
        """查看 Space 子房间"""
        async for result in self.cmd_space_children(event, space_id, limit):
            yield result

    @admin_group.command("knock")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_knock(
        self, event: AstrMessageEvent, room_id_or_alias: str, reason: str = ""
    ):
        """敲门请求加入房间"""
        async for result in self.cmd_knock(event, room_id_or_alias, reason):
            yield result

    @admin_group.command("roomrefresh")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_roomrefresh(self, event: AstrMessageEvent, room_id: str = ""):
        """重新获取房间信息"""
        async for result in self.cmd_room_refresh(event, room_id):
            yield result

    @admin_group.command("setname")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_setname(self, event: AstrMessageEvent, name: GreedyStr):
        """修改 Bot 的显示名称"""
        async for result in self.cmd_setname(event, name):
            yield result

    @admin_group.command("setavatar")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_setavatar(self, event: AstrMessageEvent):
        """通过引用图片修改 Bot 的头像"""
        async for result in self.cmd_setavatar(event):
            yield result

    @admin_group.command("setstatus")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_setstatus(
        self, event: AstrMessageEvent, status: str = "", message: str = ""
    ):
        """修改 Bot 的在线状态"""
        async for result in self.cmd_setstatus(event, status, message):
            yield result

    @admin_group.command("statusmsg")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_statusmsg(self, event: AstrMessageEvent, message: str = ""):
        """设置或清除 Bot 的状态消息"""
        async for result in self.cmd_statusmsg(event, message):
            yield result

    @admin_group.command("purgebot")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_purgebot(
        self, event: AstrMessageEvent, limit: int = 100, room_id: str = ""
    ):
        """清理机器人历史消息"""
        async for result in self.cmd_purge_bot_messages(event, limit, room_id):
            yield result

    @admin_group.command("verify")
    @filter.permission_type(PermissionType.ADMIN)
    async def admin_verify(self, event: AstrMessageEvent, device_id: str):
        """手动确认 SAS 验证（支持按 adapter 推送到多房间）"""
        if str(event.get_platform_name() or "").strip().lower() != "matrix":
            yield event.plain_result("此命令仅在 Matrix 平台可用")
            return

        self._maybe_apply_admin_room_config()

        matrix_utils_cls = self._get_matrix_utils_cls()
        if matrix_utils_cls is None:
            yield event.plain_result("未检测到 Matrix 适配器插件")
            return

        e2ee_manager = None
        try:
            target_platform_id = str(event.get_platform_id() or "")
            e2ee_manager = matrix_utils_cls.get_matrix_e2ee_manager(
                self.context,
                target_platform_id,
            )
        except Exception as e:
            yield event.plain_result(f"获取适配器失败：{e}")
            return

        if not e2ee_manager or not getattr(e2ee_manager, "_verification", None):
            yield event.plain_result("端到端加密未启用或验证模块未初始化")
            return

        ok, message = await e2ee_manager._verification.approve_device(device_id)
        if ok:
            yield event.plain_result(f"✅ {message}")
        else:
            yield event.plain_result(f"❌ {message}")
