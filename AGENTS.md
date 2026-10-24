# ModpackWizard 项目交接介绍

## 一、项目定位

Minecraft 整合包（Modpack）管理工具，围绕两个包格式工作：
- **Modrinth**：`modrinth.index.json` + `.mrpack`（zip 容器）
- **CurseForge**：`manifest.json` + `.zip`（overrides 目录）

核心能力：新建/打开整合包、按 mods/resourcepacks/shaderpacks 三类管理条目、Modrinth 搜索添加、本地 JAR 识别（SHA1 反查）、自动补依赖、批量更新检查、重复检测、兼容性体检、打包导出。界面双语（zh_CN/en_US）、明暗主题。

## 二、目录结构与版本状态（重要）

```
Modpack Tools\
├── web\ModpackWizard.html      # HTML 浏览器版 —— 唯一活跃开发版本
├── web\test_search.js          # HTML 版搜索单测（node test_search.js）
├── py_ctk\ModpackWizard.py     # CustomTkinter 桌面版（旧）—— 功能与 HTML 对齐维护，UI 不再更新
├── py_ctk\test_search.py       # CTK 版搜索单测（python -m unittest test_search）
├── py_ctk\ModpackWizard.spec   # 旧 PyInstaller 配置，已弃用勿用
├── website\index.html          # 产品官网落地页（与工具本体独立）
├── _archive.7z                 # Tauri 移植版归档 —— 永远不审查、不维护、不同步
├── AGENTS.md / 改动记录.txt / RELEASE_NOTES.md(过时,已标注)
└── dist\                       # Nuitka 打包产物
```

| 版本 | 路径 | 技术栈 | 状态 |
|---|---|---|---|
| **HTML 浏览器版（主力）** | `web\ModpackWizard.html` | 单文件 HTML+CSS+JS，JSZip CDN，Fluent Web Components | 唯一活跃开发；WinUI 3 风格已对齐（风格层面暂不再迭代） |
| **PySide6 桌面版** | `C:\Users\zxt11\PySide6-FluentUI-QML\` | PySide6 6.7.2 + QML + FluentUI-QML | **暂时搁置**：代码保留不删不改不打包，除非用户明确要求 |
| **CustomTkinter 版（旧）** | `py_ctk\ModpackWizard.py` | CustomTkinter | 保留；业务逻辑与 HTML 两版功能对齐 |

改功能时以 **Python + HTML 两版功能对齐**为原则：两版同名辅助函数、同构数据结构、同一套 i18n 键。

**PySide6 版架构分层**（搁置，仅供恢复开发时参考，项目位于 `C:\Users\zxt11\PySide6-FluentUI-QML\`）：
- `backend/logic.py`：ModpackWizard.py 业务逻辑原样迁移（LANG/Cache/ModrinthAPI/工具函数）
- `backend/mod_model.py`：ModListModel(QAbstractListModel)；`backend/backend.py`：Backend(QObject) 桥接层，Slots/Properties/Signals，跨线程走 Signal
- `qml/Main.qml` + `qml/pages/{Home,Edit,Settings}Page.qml`：FluentUI-QML 组件
- `qml.qrc` → `pyside6-rcc` 编译为 `backend/qml_rc.py`：**QML 必须走 qrc 完整路径**（`qrc:/qml/pages/X.qml`），相对路径会以 FluentUI 组件自身位置为基准导致页面空白；改 QML 后必须重新 `pyside6-rcc qml.qrc -o backend\qml_rc.py`
- `main.py`：入口；`_check_keys.py`：校验 QML/backend 引用键与 LANG 键集一致（缺失须为 0）
- 运行：`cd C:\Users\zxt11\PySide6-FluentUI-QML ; .\venv\Scripts\Activate.ps1 ; python main.py`
- 打包（Nuitka onefile，先设 `$env:NUITKA_CACHE_DIR="$PWD\.nuitka_cache"`）：
`python -m nuitka --onefile --enable-plugin=pyside6 --include-qt-plugins=qml --include-package=backend --include-package=FluentUI --assume-yes-for-downloads --remove-output --lto=no --windows-console-mode=disable --output-dir=dist --output-filename=ModpackWizard.exe main.py`
（onefile 压缩用外部 Python3.14 的 zstd，内存紧张会 MemoryError，回落后重跑；C 编译走 clcache 全命中）

**website/index.html**：产品官网落地页（单文件、零依赖、中英双语 79 对键、纯 CSS 界面 mockup）；下载按钮链接集中在脚本顶部 `CONFIG`（winUrl/webUrl/repoUrl，发布前替换占位地址）。

`RELEASE_NOTES.md` 是旧版发行说明，已加 ARCHIVED 过时标注，仅作历史参考。

## 三、核心数据结构

**index 条目（Modrinth）**：
```json
{"path":"mods/xxx.jar","hashes":{"sha1":"...","sha512":"..."},"downloads":["https://cdn.modrinth.com/..."],"fileSize":123,"env":{"client":"required","server":"optional"}}
```
**CF 条目**：
```json
{"path":"mods/x.jar","hashes":{},"downloads":["https://mediafilez.forgecdn.net/files/<id/1000>/<id%1000>/<name>"],"fileSize":0,"cf":{"projectID":1,"fileID":2,"required":true}}
```
- 路径前缀即类型：`mods/`=mod、`resourcepacks/`=rp、`shaderpacks/`=sp
- 两版共享助手：`entry_type(entry)`、`entry_prefix(t)`、`TYPE_PREFIX`、`build_mod_entry(data, prefix)`、`parse_project_id_from_url()`；搜索匹配纯函数 `mod_match`(py) / `match_entry`(html)，两版同构
- **前缀必须从当前条目 path 取或由调用方显式传入**，不要依赖易脏的全局"当前添加类型"（Python `self._add_prefix` / HTML `ADD_PREFIX`）

## 四、外部 API

- Modrinth REST（`api.modrinth.com/v2`）：搜索、项目、版本、`/version_file/{sha1}` 哈希反查；加载器版本链按 loader 分派：Fabric 用 meta API、Forge 用 `maven.minecraftforge.net` maven-metadata.xml、NeoForge 用 `maven.neoforged.net` releases JSON（按 MC 版本前缀过滤、数值降序）；Mojang MC 版本列表（limit=100 翻页取全、beta/alpha 也含）
- **cfwidget**（`api.curseforge.com/v1/cfwidget/`，无需 API key）：异步排队接口——返回 **HTTP 202 + `{error:'in_queue'}`（注意 r.ok 为 true）**，必须读 body 判断并重试；成功判定是 200 且有 `files`
- 缓存：Python 模块级 `CF_WIDGET_CACHE`（成功 TTL 3600s、失败 300s）；HTML `CF_PROJ_CACHE`（Map，毫秒 TTL）
- CF 文件过滤：cfwidget 文件的 `versions` 数组同时含 MC 版本和加载器标签（Fabric/Forge/NeoForge/Quilt），过滤时"有加载器标签才按当前 loader 筛，无标签放行"；rp/sp 条目不按 loader 过滤
- 请求约束：网络操作必须有超时/异常兜底（HTML 用 `fetch_to()` 30s 超时助手）；更新检查用 20 并发池防限流；"最新版本"请求用 `limit=1`；版本判定优先 versionId 比对（versionNumber/文件名兜底）

## 五、关键架构约定

- **Python 线程**：网络任务一律子线程，更新 Tk 必须 `self.root.after(0, lambda: ...)`；`except Exception as e` 块结束后 `e` 被删除，lambda 里延迟引用 `e` 必崩——except 内先存 `err=str(e)` 再闭包引用
- **HTML 状态**：`INDEX_DATA`（当前包）、`PACK_FORMAT`、`CURRENT_PAGE`、`window._localJars`（Map：完整 path → `{file,name}`，浏览器模式的本地文件源）；异步名称回填用批次令牌（`NAME_BATCH`）隔离，回填后调 `apply_filter()` 而非 `render_rows()`；跨包竞态一律捕获包引用（`const pack=INDEX_DATA`）完成后比对丢弃
- **i18n**：Python 字典 `LANG`（zh/en 各 318 键），HTML `LANG`（各 294 键）。新增文案**必须两语言都加**；两版之间键名尽量同名；弹窗统一 `messagebox.askyesno(tr('dialog_title_tip'), tr('正文键').format(...))` 模式，标题不得用带占位符的键
- 打包：带 downloads 的条目不进 overrides（由启动器下载），只有 downloads 为空的本地条目才物理打包（进 `overrides/` 对应子目录）；arcname 必须保留子目录结构
- **覆盖目录体系**：导入时把包内 `overrides/` 与客户端专用目录（Modrinth `client-overrides/`、CF `clientoverrides/`）合并到工作区根目录（同名时客户端专用覆盖通用）；`server-overrides/` 仅原样保留不合并。导出时用户选一个文件夹：顶层名为 `client-overrides`/`server-overrides`（CF 为 `clientoverrides`）的子目录映射到包内同名根，其余内容进 `overrides/`（根级 manifest/index 清单文件跳过）；浏览器版包内覆盖文件存在 `window._ovFiles`（key=工作区相对路径或保留的 `server-overrides/...`），重打包不得丢
- 设置持久化：Python `~/.modpackwizard_config.json`（写入先 load 合并防丢键）；HTML localStorage（theme/lang/showLog）

## 六、构建与验证（Windows / PowerShell）

```powershell
# Python 静态检查（先 cd py_ctk；沙箱对 site-packages 的报错是误报，看 EXIT 码；pyflakes 装在 Python 3.14，用 py -3.14 -m pyflakes）
python -m py_compile ModpackWizard.py
python -m pyflakes ModpackWizard.py

# 搜索单测（两版）
cd web ; node test_search.js        # 34 项断言
cd py_ctk ; python -m unittest test_search   # 19 用例

# HTML/website JS 语法检查：正则提取 <script> 内容写临时 _c.js（UTF8 无 BOM）→ node --check → 删除临时文件

# i18n 校验：对比 zh/en 键集 + 所有 tr('...')/data-i18n 字面量键存在（可用括号配对法提取 LANG 块）

# 打包（Nuitka onefile，在 py_ctk 目录下执行）
python -m nuitka --onefile --enable-plugin=tk-inter --assume-yes-for-downloads --remove-output --lto=no --windows-console-mode=disable --output-dir=dist --output-filename=ModpackWizard.exe --include-package=customtkinter --include-package-data=customtkinter --include-package-data=certifi --onefile-tempdir-spec="{CACHE_DIR}/ModpackWizard" ModpackWizard.py
# 必须 --enable-plugin=tk-inter，否则 exe 静默退出；任务框架常误报 exit 1，以 exe 时间戳和冒烟运行为准
# onefile-build 目录删除失败（Defender 锁文件）是无害 FATAL；完成后删 build 中间目录、日志
# 旧 PyInstaller spec（ModpackWizard.spec）已弃用，勿再用它打包
```

## 七、当前状态

- **HTML 版（web\ModpackWizard.html）**：唯一活跃版本。WinUI 3 风格已对齐（`@fluentui/web-components@3.1.3` CDN + CSS 变量映射 Design Token：`--accent:#0078D4` 亮/`#4CC2FF` 暗，`--mica:#F3F3F3`/`#202020`，4px 控件圆角，32px 控件高度，Segoe UI Variable Text），支持明暗主题 × winui/classic 风格 4 套组合、响应式布局、双语 302 对键。已多轮全面审查修复（业务 bug 全量、文案审校、i18n 全接线、死代码清零）
- **CTK 版（py_ctk\ModpackWizard.py）**：与 HTML 同步修完同等问题，双语 326 对键，pyflakes 0 告警、单测 19/19
- **website**：双语 79 对键，SEO/健壮性已修复
- **PySide6 版**：搁置（UI 重写完成、业务逻辑已迁移、冒烟通过，但不再开发/修复/打包）
- 改动历史全量见根目录 `改动记录.txt`

## 八、协作要求

- 极简代码风格（单文件、紧凑写法），中文交流
- 修 bug 前必须读实际代码核实，不臆断；Windows 下用 PowerShell 语法（`;` 不用 `&&`）
- 改动后跑上述验证；**开发完成后先跑完整冒烟用例验证核心流程，暂缓打包，等用户单独下达打包指令再执行**
- **每次改动完成后，必须在根目录 `改动记录.txt` 追加一条记录**（格式：`序号 日期 | 涉及文件 | 改动简述`），再收尾汇报
- 不要主动新建 md 文档；不要提交 git commit（除非明确要求）
