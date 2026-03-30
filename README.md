# AstrBot Matrix Admin Plugin

Matrix 管理插件，提供用户管理、权限控制、封禁踢出、设备验证与适配器运维命令。

## 依赖

- `astrbot_plugin_matrix_adapter`

## 配置

### 推荐：多适配器多房间通知（temple list）

```json
{
  "matrix_admin_verify_temple_list": [
    {
      "adapter_name": "matrix_main",
      "rooms": ["!ops:example.org", "!security:example.org"]
    },
    {
      "adapter_name": "matrix_backup",
      "rooms": ["!backup-ops:example.org"]
    }
  ],
  "matrix_admin_verify_room_id": "!fallback:example.org"
}
```

- `matrix_admin_verify_temple_list`：主配置。每项由 `adapter_name + rooms[]` 构成。
- `matrix_admin_verify_room_id`：旧配置兼容兜底；当 `temple_list` 未命中当前 adapter 时仍可通知此单房间。
- 代码兼容读取 `matrix_admin_verify_template_list`（仅兼容，不作为主字段）。

## 命令概览

所有命令以 `/admin` 作为命令组前缀：

- 用户管理：`kick`, `ban`, `unban`, `invite`, `promote`, `demote`, `power`
- 信息查询：`admins`, `whois`, `search`
- 忽略列表：`ignore`, `unignore`, `ignorelist`
- 房间管理：`createroom`, `dm`, `aliasset`, `aliasdel`, `aliasget`, `publicrooms`, `forget`, `upgrade`, `hierarchy`, `knock`, `roomrefresh`
- Bot 管理：`setname`, `setavatar`, `setstatus`, `statusmsg`, `purgebot`
- 验证：`verify`, `scanqr`
- 适配器运维：`matrixstatus`, `reconnect`, `resendpending`

## 使用示例

```text
/admin kick @user:example.org 违规
/admin ban @user:example.org spam
/admin unban @user:example.org
/admin invite @user:example.org
/admin promote @user:example.org mod
/admin demote @user:example.org
/admin power @user:example.org 50
/admin admins
/admin whois @user:example.org
/admin search alice 10
/admin ignore @user:example.org
/admin ignorelist
/admin createroom "My Room" yes
/admin dm @user:example.org
/admin aliasset #myroom:example.org !roomid:example.org
/admin aliasget #myroom:example.org
/admin publicrooms example.org 20
/admin upgrade 10 !roomid:example.org
/admin hierarchy !roomid:example.org 20
/admin knock #room:example.org hi
/admin setname AstrBot
/admin verify DEVICEID123
/admin scanqr @alice:matrix.org DEVICEID123 /tmp/element-verify-qr.png
/admin matrixstatus
/admin reconnect
/admin resendpending matrix-main 20
/admin purgebot 200
/admin roomrefresh
/admin roomrefresh all
```

## 运行态命令

### `/admin scanqr`

扫描同账号设备验证二维码，并发送 `m.reciprocate.v1`。若在网页中使用，可直接在消息里附带二维码图片，或引用一张历史二维码图片。

**用法**：
```text
/admin scanqr <user_id> <device_id> <二维码图片路径或 base64 载荷> [matrix_platform_id|webhook_uuid]
```

### `/admin matrixstatus`

查看 Matrix 适配器运行状态、同步统计与最近错误。

**用法**：
```text
/admin matrixstatus [matrix_platform_id|webhook_uuid]
```

### `/admin reconnect`

主动中断当前 `/sync` 长轮询并立即重连。

**用法**：
```text
/admin reconnect [matrix_platform_id|webhook_uuid]
```

### `/admin resendpending`

重试最近失败或挂起的出站消息记录。

**用法**：
```text
/admin resendpending [matrix_platform_id|webhook_uuid] [limit]
```

## 说明

- 命令仅在 Matrix 平台生效。
- 若命令来自与某个 Matrix 适配器共用统一 Webhook 的会话，可自动匹配该适配器进行扫码/状态操作。
- `matrix_platform_id` 参数也可直接填写对应适配器的 `webhook_uuid`。
- 具体权限要求依赖房间的 power level 配置。
