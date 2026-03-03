from __future__ import annotations

from astrbot.api import logger


def normalize_room_ids(raw_rooms) -> list[str]:
    if isinstance(raw_rooms, str):
        raw_iterable = list(raw_rooms.split(","))
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


def normalize_verify_room_templates(raw_templates) -> dict[str, list[str]]:
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
        rooms = normalize_room_ids(item.get("rooms", []))

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


def split_reason_and_room_id(reason_or_room: str) -> tuple[str, str]:
    raw = str(reason_or_room or "").strip()
    if not raw:
        return "", ""
    parts = raw.split()
    last_part = parts[-1]
    if last_part.startswith("!") and ":" in last_part:
        return " ".join(parts[:-1]).strip(), last_part
    return raw, ""


def apply_admin_room_config(plugin) -> None:
    matrix_utils_cls = plugin._get_matrix_utils_cls()
    if matrix_utils_cls is None:
        return

    adapter_ids = matrix_utils_cls.list_matrix_platform_ids(plugin.context)
    if not adapter_ids:
        logger.debug("[MatrixAdmin] 未发现 Matrix adapter，跳过验证通知配置下发")
        return

    for adapter_id in adapter_ids:
        e2ee_manager = matrix_utils_cls.get_matrix_e2ee_manager(
            plugin.context,
            adapter_id,
            fallback_to_first=False,
        )
        verification = (
            getattr(e2ee_manager, "_verification", None) if e2ee_manager else None
        )
        if not verification:
            continue

        rooms = plugin.verify_room_templates.get(adapter_id, [])
        verification.set_admin_notify_rooms(rooms)
        verification.set_admin_notify_room(plugin.verify_room_id)
        logger.debug(
            "[MatrixAdmin] 已下发验证通知配置：adapter=%s rooms=%s fallback=%s",
            adapter_id,
            rooms,
            bool(plugin.verify_room_id),
        )
