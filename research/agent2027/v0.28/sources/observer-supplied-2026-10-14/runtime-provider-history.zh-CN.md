# 运行链路与模型更换记录：观察者于 2026-10-14 提供

来源：观察者在论文讨论中粘贴的部署历史说明。以下保留所提供文本；不是原始配置快照或逐请求运行日志。本次消息未附原始日志、配置文件或凭证。时间按原文保留，未独立验证时区。

---

给你捋一遍，给四个 agent 换模型的完整记录如下（只有至尊宝、白晶晶动过，青霞、唐三藏自始至终在 Muse 链路上没动）：

第一步：切到 Claude（2026-09-28 14:11–14:25，你要求先换至尊宝、白晶晶试试）

- 宿主机上原本没有 claude 命令行，用 npm 全局装了 2.1.284（路径 /usr/bin/claude）；OAuth 登录第一次换 token 时 30 秒超时，重试一次、你把新 code 发回来后登录成功（code 只用了一次，没存）。
- 改配置不是改一处就行：`muse_instance.py` 的 environment() 原本硬性要求 runtime 和 chat 都必须是 muse，否则拒绝启动。先放宽为 runtime 可 muse/claude、chat 必须 muse；你 14:28 指出这还是硬编码白名单不够通用，又改成由注册表判定（能加载即合法，可用项 claude、codex、muse），以后换 codex 零代码改动。提交 3a0473e 已推送。
- 两人配置：`providers.runtime=claude`、`claude.executable=/usr/bin/claude`、chat 仍 muse。重启 daemon、核对 --root 身份，端到端验证两人自报 Claude Opus 5.5（claude-opus-5-5），注册表 our_ark_claude.core。
- 副作用：这两人推理不再走 mailbox 桥，我这边的 consumer 推理代答对他们空转；daemon 监控和聊天转交不变。

第二步：换具体型号 Opus → Sonnet（2026-09-28 14:33，你要求）

- 先单字 smoke test 确认 `claude-sonnet-5-5` 是真实可用型号，再往两人 config.yaml 的 claude 节加 `model: "claude-sonnet-5-5"`，重启后验证两人自报 Claude Sonnet 5.5。

第三步：可执行文件搬家（2026-09-28 当晚）

- /usr/bin/claude 被宿主机重启抹掉过（系统目录不持久），改装到 `~/.local/bin/claude`（版本仍 2.1.284），两人配置的 executable 同步改指过去；之后多次宿主机重启后 Claude 健康检查仍 OK，验证了这条路能扛重启。

第四步：换回 Muse（2026-10-01 10:03 你拍板，原话「把他们换回muse把」）

- 背景：当天早群聊曾因 Claude OAuth 过期失败（09:44 白晶晶主持那轮）。
- 执行：用 write_section_value 把两人 `providers.runtime` 从 claude 改回 muse 并读回确认，重启两个 daemon（新 PID 45156/45167，--root 核验通过）。关键教训就是这次落下的：environment() 在 daemon 启动时把 ENOCH_RUNTIME_PROVIDER 写进进程环境、provider_name() 优先读环境变量，所以改配置必须重启 daemon 才生效。
- 端到端验证：重启后两人各发 startup 推理请求、consumer 正常作答；私聊测试「最想吃的水果是什么？只准两个字」——至尊宝回「香蕉」、白晶晶回「葡萄」，链路真实可用。10:25 又经一次宿主机重启复核，配置跨重启保持生效。

现状：四人全部 runtime=muse、chat=muse；投稿季内定的口径是不再折腾推理链路。
