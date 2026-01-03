"""
Matrix Admin Plugin - 提供 Matrix 房间管理命令

此插件依赖于 astrbot_plugin_matrix_adapter 提供的 Matrix 客户端。
提供用户管理、权限控制、房间管理等功能。
"""

from astrbot.api.star import Context, Star

from .commands import (
    AdminCommandBindingsMixin,
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
    AdminCommandMixin,
    UserCommandsMixin,
    PowerCommandsMixin,
    QueryCommandsMixin,
    IgnoreCommandsMixin,
    RoomCommandsMixin,
    BotCommandsMixin,
    AdminCommandBindingsMixin,
):
    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self.context = context
