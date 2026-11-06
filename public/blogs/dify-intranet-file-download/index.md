# 内网 Dify 文件下载全链路：路径查找、多 Web 入口、手机访问与历史重签名

我在内网部署 Dify 时，遇到过一个看起来很简单、实际涉及好几层的问题：定时工作流已经生成了日报 PDF，用户在另一个聊天应用里说“下载昨天的日报”，系统应该找到原文件，让电脑和手机都能下载。

问题陆续表现为：工作流明明返回了文件，手机打不开；改成相对路径后，聊天里的文字不能点击；即时回复与历史记录表现不同；刷新后，相对路径又变成了固定 IP。

这篇文章把前面的排查串起来，说明文件究竟怎样被找到、下载地址怎样生成、多入口怎样处理，以及在不联网的 Dify 服务器上如何部署和验证。

本文记录的是 **Dify 1.13.3 定制部署与当时的本地补丁**。其他版本、第三方聊天前端需要核对各自实现。文中的 IP、域名、应用 ID 均为示例，不对应真实部署；部署目录和容器名也需要按现场调整。此前的本地测试、镜像打包不代表本文发布时已重新验收内网生产环境。

## 1. 先把四种“路径”分开

文件存在服务器上，不等于浏览器能拿着这个路径下载。排查时，我先区分下面四层：

| 层次 | 示例 | 谁使用 |
| --- | --- | --- |
| 宿主机物理路径 | `/srv/dify/docker/volumes/app/storage/tools/<tenant>/<object>` | 服务器管理员、挂载配置 |
| 容器内路径 | `/app/api/storage/tools/<tenant>/<object>` | Dify API、worker |
| 存储键 `file_key` | `tools/<tenant>/<object>` | 文件元数据、存储适配器 |
| 浏览器下载 URL | `/files/tools/<file-id>.pdf?timestamp=...&nonce=...&sign=...` | 用户浏览器、文件接口 |

URL 中的文件 ID 用来查元数据，不应假设它就是磁盘文件名。文件接口根据记录和存储配置读取数据；不能凭 URL 后缀直接拼出宿主机路径。

我的查询服务使用本地存储，因此可以通过只读挂载找到物理文件。如果部署使用 S3、MinIO 等对象存储，就需要通过相应存储接口读取，不能照搬“本地目录拼接”的部分。

`D:\reports\日报.pdf`、`/app/api/storage/...`、`http://report-download:8090/...` 都不是可以直接发给手机的通用下载地址。前两个属于文件系统，最后一个属于 Docker 内部网络。

## 2. 完整链路：生成一次，按日期查询已有日报

我把“生成日报”和“查询日报”分成两个应用。

```text
定时生成工作流 A
  → 收集数据、生成 PDF
  → 保存文件，产生文件元数据
  → 成功运行的 outputs 包含 report_date、pdf_files

聊天查询工作流 B
  → 识别用户要哪一天，或 latest
  → HTTP 调用 report-download 查询服务
  → 查询 A 的成功定时运行及其文件引用
  → 找到并验证已有 PDF
  → HTTP 节点读取 PDF，获得本次返回的 Dify 文件对象
  → 从文件对象取完整签名 URL，转换成 /files/... 根相对链接
  → 回答节点输出 Markdown

电脑或手机浏览器
  → 当前页面入口 + /files/...
  → 入口 Nginx 转发到同一套 Dify 文件接口
  → 校验签名、读取文件并返回 PDF
```

这里有两类容易混淆的接口：查询服务内部接口和浏览器文件接口。

| 接口 | 作用 | 使用者 |
| --- | --- | --- |
| `http://report-download:8090/reports?date=latest` | 查日期对应的报告元数据 | Dify HTTP 节点，带服务令牌 |
| `/reports/<run-id>/files/<file-id>` | 查询服务内部读取已生成文件 | Dify HTTP 节点，带服务令牌 |
| `/files/tools/<file-id>.pdf?...` | Dify 对外文件访问接口 | 浏览器，带文件签名 |

查询服务令牌和文件 URL 的 `sign` 是两套不同凭据。不能把服务令牌附到公开下载链接，也不能把内部 `/reports/...` 地址直接交给浏览器。

HTTP 节点读取原 PDF 后，本次响应产生的文件对象可能对应新的文件记录，**不应假定对外链接里的 ID 与源日报 ID 相同**。这个方案复用已生成的 PDF 内容，没有重新生成日报，但仍可能产生新的文件存储和元数据。

## 3. 文件查找逻辑：从运行记录定位到实际文件

当前查询服务限定一个来源应用和租户，避免同名日报、其他工作空间文件混在一起。它不让模型猜路径，也不扫描全盘寻找“看起来像日报”的文件。

查找顺序如下：

1. 解析 `latest` 或 `YYYY-MM-DD`，校验日期有效且不在未来；日期边界按北京时间处理。
2. 从 `workflow_runs` 筛选来源 `app_id`、`tenant_id`，只接受 `status='succeeded'`、`triggered_from='schedule'`。
3. 读取输出中的 `report_date` 与 `pdf_files`。调试运行、失败运行、其他应用的结果不会进入候选。
4. 从文件引用中提取真实文件 ID。兼容文件对象中的 ID、URL，以及可解码的 `dify-file-ref:` 引用。
5. 查询 `tool_files`，检查租户、MIME 类型、`file_key`。
6. 在配置的只读存储根目录内解析路径，确认实际文件存在，且文件头为 `%PDF-`。
7. 返回报告日期、文件名、运行 ID、文件 ID 和内部读取路径；没有匹配时返回 `found:false`。

`latest` 依据**报告日期**选择，随后按完成时间和运行 ID 排序，不是随便取最后执行的一条工作流。当前实现先由 SQL 排序并限制最多 100 条候选；这是查询边界，不能声称它会无限回溯所有历史。

文件定位的关键约束是：`file_key` 必须位于 `tools/<当前租户>/` 下，不能包含 `..`、空路径段、Windows 盘符或反斜杠；解析符号链接后的真实文件仍须落在允许目录内。不能把用户输入的路径直接接到 `open()` 上。

如果文件名带报告日期，还会核对它与输出日期一致，避免返回日期不符的文件。

### 在服务器上怎样查实际路径

先看 API 的真实挂载，不要先猜宿主机目录：

```bash
docker inspect docker-api-1 --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

例如输出：

```text
/srv/dify/docker/volumes/app/storage -> /app/api/storage
```

然后在服务器上交互查询文件元数据，替换为自己的文件 ID：

```bash
docker exec -it docker-db_postgres-1 psql -U postgres -d dify
```

```sql
SELECT id, tenant_id, name, file_key, mimetype, size
FROM tool_files
WHERE id = '<文件ID>';
```

将查出的 `file_key` 与真实挂载对应起来，再检查文件存在性。这里的表名和 PostgreSQL 命令适用于本文这套版本与部署；其他数据库、上传文件和其他类型文件不能直接套用 `tool_files` 的查询。

## 4. 电脑、手机、多个 Web 入口为什么会互相冲突

实际部署中可能有下面几种入口：

| 入口 | 浏览器打开的页面 | 可达范围 |
| --- | --- | --- |
| 内网电脑 | `http://10.20.0.10/difyapps` | 可以访问内网 IP |
| 内网第二个 Web | `http://10.20.0.11/difyapps2` | 另一台入口代理 |
| 手机 | `https://chat.example.com/difyapps2` | 通过手机可达的域名网关 |

三个页面即使调用同一套后端，也有不同的 origin。origin 包含协议、主机和端口。

如果 `FILES_URL` 固定为电脑可达的 IP，手机得到的链接可能不可达；改成手机域名，电脑又可能因 DNS 或路由限制而打不开。只换一个固定地址不能解决双方网络不互通的问题。

可选方案：

| 方案 | 适用条件 | 限制 |
| --- | --- | --- |
| 统一文件域名，内外网分别解析 | 能管理 DNS、证书和网关 | 长期维护最直接，须保证各端解析与可达性 |
| `/files/...` 根相对链接 | 每个页面入口都能代理文件接口 | 前端须允许，历史重签名须保留相对形式 |
| 分别给电脑、手机完整链接 | 暂时无法改前端 | 用户要自己选入口，固定主机仍需维护 |
| 业务后端文件网关 | 多后端、长期归档、统一权限 | 需要独立索引和授权设计 |

本文采用第二种：**浏览器使用当前页面入口，各入口负责把 `/files/` 转到同一套文件服务。**

如果多个 Web 实际连接的是不同 Dify 实例，仅相同路径还不够。它们的数据库、存储和签名密钥可能不同，A 生成的文件不能直接让 B 校验。应为各应用建立明确的网关路由，或设计独立文件服务。

## 5. 相对路径会怎样拼接，哪些写法容易误解

假设页面是 `https://chat.example.com/difyapps2/session/123`：

| 链接写法 | 结果 |
| --- | --- |
| `/files/tools/a.pdf?...` | `https://chat.example.com/files/tools/a.pdf?...` |
| `files/tools/a.pdf?...` | 按当前文档目录解析，可能进入 `/difyapps2/session/files/...` |
| `//10.20.0.10/files/tools/a.pdf?...` | 沿用 HTTPS，主机仍固定为 `10.20.0.10` |
| `http://10.20.0.10/files/tools/a.pdf?...` | 固定 HTTP、固定主机 |

因此要用**一个斜杠开头的根相对路径**。两个斜杠只省略协议，并不会自动选择当前域名；还可能把原来的 HTTP 服务当作 HTTPS 访问。

浏览器按文档的基准 URL 解析相对地址；普通页面没有额外 `<base>` 时，就是当前页面 URL。在 iframe 场景，使用的是聊天 iframe 自己的文档地址，不能把外层业务页面的域名当作 iframe 的域名。混合内容、证书和 iframe 下载限制也要单独检查。

## 6. 从文件对象生成下载链接：保留签名，禁止模型改写

对外访问格式如下，省略号只是说明占位，不能直接用来下载：

```text
/files/tools/<uuid>.pdf?timestamp=<时间戳>&nonce=<随机值>&sign=<完整签名>&as_attachment=true
```

这条链路中的三个签名参数缺一不可。曾经的手机报错明确写着 `ToolFileQuery` 缺少 `sign`，说明请求已经到达文件接口，失败点是参数缺失；此时继续更换 IP，不能把缺失的签名补回来。

本地 `api/controllers/files/tool_files.py` 的参数模型和签名校验与此对应。接口会验证签名与时间，再查询文件、返回流。`as_attachment=true` 用于请求附件下载，与签名参数作用不同。

代码节点应该接收 HTTP 下载节点的 `status_code` 与 `files`，先验证：

- 请求成功且只有一个 PDF 文件对象。
- URL 路径符合 `/files/tools/<uuid>.pdf`。
- `timestamp`、`nonce`、`sign` 全部存在且只有一个值。
- 不接受控制字符、异常协议、片段、未知参数或截断的签名。
- 移除原 URL 的协议和主机，保留原始签名参数字节，设置 `as_attachment=true`。

本文附带 [完整代码节点 download-link.py](/blogs/dify-intranet-file-download/download-link.py)。它沿用这次 1.13.3 方案的 nonce、签名格式校验；升级签名算法或文件类型后，要同步调整，不能当作所有 Dify 版本的通用解析器。

回答节点直接引用代码节点的 `download_markdown`：

```text
已找到已生成的日报。

报告日期：{{#pdf_metadata.report_date#}}

{{#relative_link.download_markdown#}}
```

节点 ID 要替换为自己工作流里的 ID。不要让 LLM 抄写签名 URL，也不要在 URL 中手动插入转义反斜杠、换行或省略号。

使用 Markdown 文本链接时，最终响应 `files: []` 可以是正常的：文件入口已经放进 `answer`，并不一定还有附件卡片。应检查最终 `answer` 和 DOM 中的链接，不能只看卡片是否出现。

## 7. 第一个补丁：让聊天前端允许 `/files/` 链接

当时这版 Dify 的 `isValidUrl()` 默认允许 `http:`、`https:`、`//`、`mailto:` 等前缀，根相对 `/files/...` 不在这个列表内。Markdown 即使解析成功，链接组件仍可能把它降级成普通文字。

本次修改位于 `web/app/components/base/markdown-blocks/link.tsx`。在保留原有锚点和特殊链接分支的前提下，只调整原来的链接过滤条件：

```tsx
const isRelativeFileUrl = typeof href === 'string' && href.startsWith('/files/')
if (!href || (!isRelativeFileUrl && !isValidUrl(href)))
  return <span>{children}</span>
```

完整 HTTP、HTTPS 链接继续走原校验。这个例外只负责让相对文件链接成为可点击的 `<a>`，不负责签名、文件权限或存储定位。最终权限仍由文件接口执行。

对应的最小改动见 [relative-files.patch](/blogs/dify-intranet-file-download/relative-files.patch)。应用前先核对版本，不能拿它直接覆盖不同版本的完整组件。

如果手机使用了独立的 `webapp-conversation` 或其他定制前端，只更新 Dify 自带 `web` 镜像未必生效。要检查**真正提供该手机页面的前端**，确认它的 Markdown 组件也允许同样的路径。

把原生 `<a href="/files/..." download>` 直接塞进聊天回答也不能绕过问题：聊天内容会经过 Markdown、HTML 清洗和自定义渲染链。`download` 属性本身也不能修复不可达地址、丢失的签名或错误代理。

## 8. 第二个补丁：历史消息重签名后仍保持相对路径

前端可点击之后，还出现过另一个现象：刚回复是 `/files/...`，刷新后却变成 `http://某个固定IP/files/...`。

原因在历史消息读取。`Message.re_sign_file_url_answer` 会识别回答中的文件链接，重新生成签名 URL。原实现调用签名函数后，会用配置的文件地址组成完整 URL。

因此不能把“历史能点击、即时不能点击”直接归因于缓存。也不能说浏览器把当前页面的 A 地址自动补成了另一个 B 地址：如果历史接口返回的 `answer` 里已经带 B，就是后端改写。

本地补丁在重新签名之后、追加附件参数之前增加：

```python
if url.startswith("/files/"):
    # Preserve same-origin links when refreshing history signatures.
    sign_url = re.sub(r"^https?://[^/]+", "", sign_url)
```

这里继续调用原来的签名函数，**只对原本是 `/files/` 的链接去掉生成结果的主机部分**。不跳过签名校验，也不全局把 `FILES_URL` 改为空。

行为应当是：

| 原回答中的形式 | 读取历史后的形式 |
| --- | --- |
| `/files/...?...` | `/files/...?新签名` |
| `http://old.example/files/...?...` | 按原签名函数与配置生成完整地址 |
| `https://old.example/files/...?...` | 按原签名函数与配置生成完整地址 |
| 普通非文件链接 | 保持原样 |

“保留完整链接原有处理规则”不等于永远保留它最初的主机或协议；它们仍受原来的 `FILES_URL` 等配置影响。本补丁也不会自动把全部历史绝对链接迁移成相对链接。

这次修改针对该属性识别到的回答 Markdown 文件链接，并不代表所有附件字段、所有 API 返回值都已统一改造。新的回复应按工作流输出路径产生相对链接，历史路径再负责更新签名并保留形式。

## 9. Nginx 配置：每个入口都必须代理 `/files/`

相对路径成功解析，只说明浏览器选择了当前入口。入口仍要知道怎样找文件。

当时网关只配置了 `/difyapps...` 转给 Dify，其他路径落入业务 Tomcat。结果聊天页面能开，`/files/...` 却进了错误服务。

下面这段加到**每个实际承接文件请求的入口**对应 `server` 中；示例后端是 Dify 网关，不是前端 Node 服务：

```nginx
location ^~ /files/ {
    proxy_pass http://10.20.0.30;
    proxy_http_version 1.1;
    proxy_set_header Host $proxy_host;
    proxy_set_header Connection "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Port $server_port;
    proxy_connect_timeout 30s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    proxy_cache off;
}
```

这里的 `proxy_pass` 没有 URI 部分，正常情况下会把原 `/files/...` 路径与查询参数交给上游。不要随手加末尾 `/`：在这个前缀 location 中，带 `/` 的写法会按 Nginx URI 替换规则改变路径。[Nginx 官方 proxy_pass 说明](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)

最终路由关系应为：

```text
/difyapps、/difyapps2 → 对应聊天前端
/files/             → 同一套 Dify 文件接口
/                   → 原业务系统
```

如果直接代理 API 容器，使用该网关实际可达的 API 地址和端口；Docker 名 `api:5001` 只有在共享网络、可解析时才有效。

先备份网关配置，再检查语法并重载。在 Linux Nginx 上通常是：

```bash
nginx -t && nginx -s reload
```

Windows 上在对应 Nginx 安装目录执行：

```powershell
.\nginx.exe -t
# 只在上一条检查成功后执行
.\nginx.exe -s reload
```

HTTPS 手机入口应提供可信证书。相对链接可以避免显式写死 HTTP，但前提是 HTTPS 入口确实转发到文件服务；它不会自动补齐网关配置。

## 10. FILES_URL 与内部服务地址怎样配置

浏览器入口和服务之间的网络要分开考虑：

| 配置 | 用途 |
| --- | --- |
| `FILES_URL` | 外部文件地址的基础 URL，生成完整链接时使用 |
| `INTERNAL_FILES_URL` | 需要内部文件地址的服务调用，可回退到 `FILES_URL` |
| `REPORT_DOWNLOAD_BASE_URL` | 本文自建查询服务的 Docker 内部地址 |
| `REPORT_DOWNLOAD_TOKEN` | 查询服务令牌，在工作流设为 Secret |
| `FILES_ACCESS_TIMEOUT` | 文件签名访问有效期，不是物理文件保留期 |

本地 `api/core/tools/signature.py` 中的工具文件签名函数根据调用参数选择外部或内部基础地址。不能把 `INTERNAL_FILES_URL` 当作“手机应该打开的域名”。

示例：

```dotenv
FILES_URL=https://files.example.com
INTERNAL_FILES_URL=http://api:5001
FILES_ACCESS_TIMEOUT=300
```

这里 `files.example.com` 应是该部署为外部文件消费者准备的有效入口。聊天回答即使采用相对路径，插件、模型或其他 API 调用仍可能需要完整可达地址，因此不要为了聊天下载随意清空配置。

Dify 工作流环境变量另行设置：

```text
REPORT_DOWNLOAD_BASE_URL = http://report-download:8090
REPORT_DOWNLOAD_TOKEN    = <在服务器生成并安全保存的令牌>
```

更改 Docker `.env` 后，单纯 `docker restart` 通常不会重新读取 Compose 的环境变量。应根据部署实际服务清单重建相关容器；常见组合为：

```bash
cd /srv/dify/docker
docker compose up -d --no-deps --force-recreate api worker worker_beat
docker compose exec -T api python -c 'from configs import dify_config as c; print(c.FILES_URL); print(c.INTERNAL_FILES_URL); print(c.FILES_ACCESS_TIMEOUT)'
```

已有定制镜像或额外 Compose 覆盖文件时，应沿用它们，避免重建时回到官方镜像。以上操作会短暂影响请求与任务，安排在维护窗口。

## 11. 在内网部署查询服务与补丁

### 查询服务

此前的 `dify-report-download` 部署脚本复用服务器现有 Dify API 镜像中的 Python 和依赖，无需内网服务器再联网装包。它读取现有 PostgreSQL 配置，连接 API、数据库和 SSRF 代理共同可达的 Docker 网络，并把报告存储只读挂载到 `/reports-storage`。

```bash
cd /srv/packages
tar -xzf dify-report-download.tar.gz
cd dify-report-download
python3 deploy.py
```

上述压缩包是此前生成的服务分发包，本文没有将带环境信息的完整包上传到博客仓库。复用时要先适配来源应用与租户配置、本地存储挂载及容器名称。

服务默认只在 Docker 网络内监听 `8090`，不开放宿主机端口。数据库连接使用只读事务，代码和存储也只读挂载。部署后生成的 `runtime.env` 与 `REPORT_TOKEN.txt` 含敏感配置，应留在服务器上。

HTTP 节点可能经过 Dify 的 SSRF 代理。**API 容器能直连查询服务，不代表 HTTP 节点经代理也能访问。** 应通过真实 HTTP 节点验收；若被拦截，按现场策略精确处理内部服务访问，不要全局关闭 SSRF 防护。

### 前端与后端补丁

此前离线交付分别包含：

- 前端镜像包：解决 Markdown `/files/` 可点击，适配当时的 Linux amd64 / Dify Web 1.13.3。
- API 小补丁包：基于已有 1.13.3 API 镜像离线构建，修复历史重签名形式。
- 各自的部署、回退和校验文件。

离线构建时不应复制整个旧版 `model.py` 覆盖已经叠加其他修改的新镜像。要把本文的最小逻辑合并到当前版本，验证后构建；尤其要保留此前语音等其他补丁。

通用交付步骤是：在联网或已有依赖的构建机准备目标架构镜像，`docker save` 导出，生成 SHA-256 清单，传入内网后校验，`docker load` 导入，再用保留现有参数的 Compose 覆盖文件更新对应服务。

```bash
# 内网服务器，包内清单与镜像名称以实际交付为准
sha256sum -c SHA256SUMS
docker load -i dify-web-image.tar
```

脚本使用 LF 换行。之前部署曾在校验阶段报出文件名尾部带 `$'\r'`，原因是 `SHA256SUMS` 使用了 CRLF。应由打包端修复并重新校验；若确认只有清单行尾受影响，可在服务器转换清单行尾后再执行校验：

```bash
sed -i 's/\r$//' SHA256SUMS
sha256sum -c SHA256SUMS
```

更改清单行尾不能掩盖真实哈希不一致；脚本或资源本体也有变化时，应重新生成可信分发包。

保留原镜像、原 Compose 配置和补丁覆盖文件。若使用此前包内 `deploy.sh`，就按其说明使用同目录的 `rollback.sh`，并保留状态文件。更新后检查网关是否仍指向有效容器，必要时重载网关。

缓存也要验证：修改已构建 JS 却沿用原文件名，可能遇到长期缓存。优先完整构建产生新的资源哈希；临时补丁需要处理缓存更新。无痕窗口可用于定位缓存问题，但不能替代发布时的缓存策略。

## 12. 300 秒过期、文件保留和删除工作流是三回事

当时配置中的 `FILES_ACCESS_TIMEOUT=300` 表示签名 URL 有效期约 300 秒。它不是“PDF 只保存 300 秒”，也不表示服务器一定会在 30 天后删除日报。

需要分别保留：

| 对象 | 丢失后的影响 |
| --- | --- |
| PDF 内容 | 元数据还在也不能返回原文件 |
| 文件元数据 | 文件接口无法按文件 ID 定位 |
| 成功定时运行及输出 | 当前查询服务失去“日期 → 文件引用”的来源 |
| 来源应用与租户配置 | 预检查或查询可能失败 |
| 当前签名 URL | 过期后需要重新查询或重新签名 |

历史读取会更新被识别到的签名链接，但页面已经打开后一直不刷新，旧 URL 仍会过期。刷新或重新查询是获取新链接的手段，前提是相应文件和记录仍在。

可以在实际运行调度任务的容器里核对清理设置：

```bash
docker exec docker-worker_beat-1 python -c 'from configs import dify_config as c; keys=("WORKFLOW_LOG_CLEANUP_ENABLED","WORKFLOW_LOG_RETENTION_DAYS","ENABLE_WORKFLOW_RUN_CLEANUP_TASK","SANDBOX_EXPIRED_RECORDS_RETENTION_DAYS"); print("\n".join(k+"="+str(getattr(c,k,"unset")) for k in keys))'
```

保留天数有值不代表对应定时任务已开启；还要看开关、调度及版本实现。清理开关关闭也不能阻止人工清理、删除应用触发的关联清理或运维脚本删除文件。

同一应用中修改并发布工作流，应用 ID 不变时，保留 `report_date`、`pdf_files` 输出结构，通常可以继续查询旧报告。导入成新应用则会获得新的应用 ID，当前单来源服务必须更新来源配置。

此前那版服务的 `APP_ID`、`TENANT_ID` 在部署脚本和服务代码中都有约束校验；只改环境变量不足以切换。要同步适配两处配置，再使用 `python3 deploy.py --replace`。切换来源并不会迁移旧日报。

如果要求“生成应用删掉以后，历史日报仍长期可查”，应新增独立归档：保存报告日期、业务范围、文件位置、校验值、生成版本和访问权限，让查询不再依赖 `workflow_runs`。这属于后续架构方案，当前服务尚未实现。

## 13. 按证据定位问题，并完成两端验收

我会从响应内容、渲染、网络、文件服务四层逐步检查：

| 现象 | 优先检查 |
| --- | --- |
| `found:false` | 是否存在对应应用的成功定时运行，输出日期与文件引用是否完整 |
| 数据库有记录，服务查不到 | 来源 ID、租户、候选上限、存储挂载、文件校验 |
| 下载文字不可点击 | 最终 `answer`、前端链接白名单、实际部署前端、资源缓存 |
| 刷新后变成固定 IP | 历史接口返回的 `answer`，以及后端重签名逻辑 |
| 手机 `sign Field required` | 比较节点输出、接口响应、DOM href 与最终请求 URL，定位截断点 |
| 403 | 签名是否完整、是否过期、各节点时钟、是否转到错误实例 |
| 404 或返回业务页面 | `/files/` 路由、文件记录与物理对象 |
| 502 | 上游连接、端口、容器状态与网关解析 |
| 电脑能下、手机不能下 | 各自入口的 DNS、证书、路由，以及手机实际发出的完整 URL |

测试参数保留时，应复制一条新生成的完整签名链接，尽快在目标端访问，并根据目标端网络选择其可达入口。不要拿已经过期的旧链接判断补丁效果，也不要把带签名链接贴入公开日志。

最终验收矩阵：

| 场景 | 预期 |
| --- | --- |
| 电脑入口，新查询 | 链接可点击，返回 PDF |
| 手机入口，新查询 | 使用手机当前入口，签名完整 |
| 第二个 Web 入口 | 自己的 `/files/` 路由也能到达同一文件服务 |
| 刷新并读取历史 | 签名更新，相对路径仍是 `/files/...` |
| 保留一个旧 HTTP/HTTPS 文件链接 | 继续遵循原签名逻辑，无相对链接补丁引入的回归 |
| 超过签名有效期 | 旧 URL 拒绝访问，重新查询或历史重签名后可用 |
| 无对应日期、无成功定时运行 | 清晰提示没有匹配文件 |
| 网关更新、容器重建、服务回退 | 路由与已有业务仍正常 |

本文没有在发布时连接内网生产服务器执行这些验收。这里记录的是已查明的原因、已有补丁与可重复操作步骤，现场仍应按上表验证真实电脑和手机链路。

## 14. 代码与版本参考

本文附带的是便于核对与复用的最小代码，没有上传服务器令牌、真实应用配置、完整业务工作流或旧镜像：

- [下载链接代码节点](/blogs/dify-intranet-file-download/download-link.py)：校验文件对象并产生根相对下载链接。
- [前后端最小补丁示例](/blogs/dify-intranet-file-download/relative-files.patch)：前端允许 `/files/`，历史重签名保留相对形式；应用前核对上下文。
- [Dify 1.13.3 Markdown 链接校验](https://github.com/langgenius/dify/blob/1.13.3/web/app/components/base/markdown-blocks/utils.ts)：核对原版允许的链接前缀。
- [Dify 1.13.3 文件接口](https://github.com/langgenius/dify/blob/1.13.3/api/controllers/files/tool_files.py)：核对文件访问参数、响应与校验入口。
- [Dify 1.13.3 签名实现](https://github.com/langgenius/dify/blob/1.13.3/api/core/tools/signature.py)：核对文件 URL 的生成规则。
- [Dify 1.13.3 消息模型](https://github.com/langgenius/dify/blob/1.13.3/api/models/model.py)：核对历史回答的重签名入口。
- [Nginx 反向代理文档](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)：核对 `proxy_pass` 的 URI 转发规则。
