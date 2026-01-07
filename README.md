# AstrBot Matrix Admin Plugin

Matrix 房间管理插件，提供用户管理、权限控制、封禁踢出等管理命令。

## 依赖

- `astrbot_plugin_matrix_adapter`

## 命令概览

所有命令以 `/admin` 作为命令组前缀：

- 用户管理: `kick`, `ban`, `unban`, `invite`, `promote`, `demote`, `power`
- 信息查询: `admins`, `whois`, `search`
- 忽略列表: `ignore`, `unignore`, `ignorelist`
- 房间管理: `createroom`, `dm`, `aliasset`, `aliasdel`, `aliasget`, `publicrooms`, `forget`, `upgrade`, `hierarchy`, `knock`
- Bot 资料: `setname`, `setavatar`, `setstatus`, `statusmsg`

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
```

## 说明

- 命令仅在 Matrix 平台生效。
- 具体权限要求依赖房间的 power level 配置。
