"""
Matrix Admin Plugin - Runtime Commands
Matrix 适配器运行态与验证辅助命令
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.message.components import Image

from .base import AdminCommandMixin


class RuntimeCommandsMixin(AdminCommandMixin):
    """运行态命令：scanqr, matrixstatus, reconnect, resendpending"""

    @staticmethod
    def _normalize_qr_input(qr_input: str) -> str:
        normalized = str(qr_input or "").strip()
        if normalized.startswith("data:") and ";base64," in normalized:
            return normalized.split(";base64,", 1)[1].strip()
        return normalized

    async def _resolve_scan_qr_input(
        self,
        event: AstrMessageEvent,
        qr_input: str = "",
    ) -> tuple[str | None, str | None]:
        normalized_input = self._normalize_qr_input(qr_input)
        if normalized_input:
            return normalized_input, None

        for component in event.get_messages() or []:
            if not isinstance(component, Image):
                continue
            try:
                payload = await component.convert_to_base64()
                payload = self._normalize_qr_input(payload)
                if payload:
                    return payload, None
            except Exception as exc:
                logger.debug(f"从消息图片提取二维码载荷失败：{exc}")

        return None, (
            "请提供二维码图片路径、base64 载荷，或在网页消息中直接附带二维码图片"
        )

    async def cmd_scanqr(
        self,
        event: AstrMessageEvent,
        user_id: str,
        device_id: str,
        qr_input: str,
        matrix_platform_id: str = "",
    ):
        """扫描 Matrix 设备验证二维码。"""
        e2ee_manager = self._get_event_e2ee_manager(event)
        if not e2ee_manager:
            e2ee_manager, error = self._resolve_matrix_e2ee_manager(
                event,
                matrix_platform_id,
            )
            if error:
                yield event.plain_result(error)
                return

        verification = getattr(e2ee_manager, "_verification", None)
        if not verification:
            yield event.plain_result("验证模块未初始化")
            return

        resolved_qr_input, input_error = await self._resolve_scan_qr_input(
            event, qr_input
        )
        if input_error:
            yield event.plain_result(input_error)
            return

        scan_method = getattr(verification, "scan_qr", None)
        if not callable(scan_method):
            yield event.plain_result("当前验证模块不支持扫码验证")
            return

        try:
            ok, message = await scan_method(user_id, device_id, resolved_qr_input)
            prefix = "✅" if ok else "❌"
            yield event.plain_result(f"{prefix} {message}")
        except Exception as exc:
            logger.error(f"扫码验证失败：{exc}")
            yield event.plain_result(f"❌ 扫码验证失败：{exc}")

    async def cmd_matrixstatus(
        self,
        event: AstrMessageEvent,
        matrix_platform_id: str = "",
    ):
        """查看 Matrix 运行状态。"""
        platform, error = self._resolve_matrix_platform(event, matrix_platform_id)
        if error:
            yield event.plain_result(error)
            return

        get_status = getattr(platform, "get_runtime_status", None)
        if not callable(get_status):
            yield event.plain_result("当前 Matrix 适配器未提供运行状态")
            return

        status = get_status()
        sync = status.get("sync", {}) if isinstance(status, dict) else {}
        outbound = status.get("outbound", {}) if isinstance(status, dict) else {}
        recent_errors = (
            status.get("recent_errors", []) if isinstance(status, dict) else []
        )

        lines = [
            f"平台：{getattr(platform.meta(), 'id', 'matrix')}",
            f"用户：{status.get('user_id') or '-'}",
            f"Homeserver：{status.get('homeserver') or '-'}",
            f"设备：{status.get('device_id_masked') or '-'}",
            f"生命周期：{status.get('lifecycle_state') or '-'}",
            f"认证：{status.get('auth_state') or '-'}",
            f"Sync：{status.get('sync_state') or '-'}",
            (
                "同步统计：成功 "
                f"{sync.get('sync_success_count', 0)} / 失败 {sync.get('sync_failure_count', 0)} "
                f"/ 连续失败 {sync.get('consecutive_failures', 0)}"
            ),
            (
                "出站统计：pending "
                f"{outbound.get('pending', 0)} / failed {outbound.get('failed', 0)} "
                f"/ sent {outbound.get('sent', 0)}"
            ),
            (
                "最后错误："
                f"{status.get('last_error_category') or '-'} "
                f"{status.get('last_error_message') or '-'}"
            ),
        ]
        if recent_errors:
            lines.append("最近错误：")
            for item in recent_errors[:3]:
                lines.append(
                    f"- [{item.get('category', '-')}] {item.get('message', '-')}"
                )

        yield event.plain_result("\n".join(lines))

    async def cmd_reconnect(
        self,
        event: AstrMessageEvent,
        matrix_platform_id: str = "",
    ):
        """请求 Matrix sync 立即重连。"""
        platform, error = self._resolve_matrix_platform(event, matrix_platform_id)
        if error:
            yield event.plain_result(error)
            return

        request_reconnect = getattr(platform, "request_reconnect", None)
        if not callable(request_reconnect):
            yield event.plain_result("当前 Matrix 适配器不支持主动重连")
            return

        ok = request_reconnect()
        if ok:
            yield event.plain_result("✅ 已请求 Matrix sync 重连")
        else:
            yield event.plain_result("❌ Matrix sync 当前未运行，无法触发重连")

    async def cmd_resendpending(
        self,
        event: AstrMessageEvent,
        matrix_platform_id: str = "",
        limit: str = "20",
    ):
        """重试最近失败或挂起的出站消息。"""
        platform, error = self._resolve_matrix_platform(event, matrix_platform_id)
        if error:
            yield event.plain_result(error)
            return

        outbound_tracker = getattr(platform, "outbound_tracker", None)
        client = getattr(platform, "client", None)
        if outbound_tracker is None or client is None:
            yield event.plain_result("当前 Matrix 适配器未启用待发送队列跟踪")
            return

        try:
            retry_limit = max(1, min(100, int(limit)))
        except Exception:
            retry_limit = 20

        results = await outbound_tracker.resend_pending(client, limit=retry_limit)
        ok_count = sum(1 for item in results if item.get("ok"))
        fail_count = len(results) - ok_count
        lines = [
            f"已尝试重发 {len(results)} 条出站记录",
            f"成功：{ok_count}",
            f"失败：{fail_count}",
        ]
        for item in results[:5]:
            if item.get("ok"):
                lines.append(
                    f"- ✅ {item.get('txn_id')} -> {item.get('event_id') or '-'}"
                )
            else:
                lines.append(f"- ❌ {item.get('txn_id')} -> {item.get('error') or '-'}")
        yield event.plain_result("\n".join(lines))
