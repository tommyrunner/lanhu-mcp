# Lanhu MCP 设计稿开发工作流 PR 指南

本文档用于把 fork 后的 `lanhu-mcp` 同步成一个可提交上游 Pull Request 的通用功能方案。目标是新增一套面向“根据蓝湖设计稿开发页面”的 AI 工作流约束，同时保持项目原有 MCP 能力不被破坏。

这份文档不是个人项目规则，也不绑定某个业务仓库。它描述的是一个公共项目可以接受的实现方式：默认兼容上游行为，只有在明确进入开发模式或配置严格模式时，才强制读取开发规则。

## 1. 功能目标

新增一层可配置的 Lanhu design-to-code 工作流：

- 提供一个 Markdown 规则文档，让 AI 在根据蓝湖设计稿编码前先读取。
- 引导 AI 在编码前完成模块化分析、文件结构分析、重复数据分析和界面行为分析。
- 降低还原设计稿时的常见误判，例如仅凭画板底部位置把普通列表项实现成 fixed 底栏。
- 允许团队通过外部 Markdown 替换默认规则，而不需要修改 Python 源码。
- 保持原有“查看设计稿、分析设计稿、获取切图、分析原型/PRD”等非开发场景继续可用。

## 2. 不纳入本 PR 的内容

这个 PR 不应该包含任何私有业务或个人项目内容。

不要包含：

- 私有 API 域名、Cookie、Token、用户 ID、密钥或上传凭证。
- Delta、戏鲸或任何第三方图片上传逻辑。
- `protect-token`、浏览器安全校验、私有资源迁移接口。
- 某个公司项目专属的目录结构。
- 强制所有用户使用 React、Vue、Flutter、某个组件库或某个状态管理方案。
- 会破坏原有设计分析能力的全局行为变更。

图片迁移、上传到第三方 CDN、替换资源域名等能力可以作为后续独立功能，不要混入这个 PR。

## 3. 公共兼容性要求

上游项目当前至少服务这些场景：

- 获取蓝湖设计图列表。
- 分析 UI 设计图和生成 HTML/CSS。
- 分析 PRD 或原型页面。
- 获取切图和素材。
- 通过 MCP 工具协作。

新增开发规则时必须保证：

- 没有开发意图时，`lanhu_get_ai_analyze_design_result` 仍然按原逻辑工作。
- 规则文件缺失时，不能让普通设计分析直接不可用。
- 如果上游原本会把图片 URL 本地化成本地路径占位符，默认仍保持这个行为。
- 如果需要保留蓝湖原始 URL，应通过参数或配置显式开启。
- Docker、源码运行、pip 安装三种方式都要有可工作的默认值。
- 外部自定义规则路径缺失、空文件、编码错误或过大时，要给出清晰错误。

## 4. fork 同步流程

在准备 PR 前，先同步上游：

```bash
git remote -v
git remote add upstream https://github.com/dsphper/lanhu-mcp.git
git fetch upstream
git checkout main
git merge upstream/main
git checkout -b feat/design-development-workflow
```

如果本地已有修改，先检查：

```bash
git status --short
git diff --stat
git diff
```

不要提交这些内容：

- `.env`
- 真实 Cookie、Token、密钥或账号信息
- `data/` 生成数据
- `logs/` 日志
- `venv/` 虚拟环境
- 个人 `AGENTS.md` 或 agent-memory 文件
- 本地截图、缓存和临时测试产物

## 5. 推荐实现设计

### 5.1 新增默认规则文档

新增：

```text
DEVELOPMENT_RULES.md
```

默认规则必须是通用规则。它可以提供保守的开发流程建议，但必须明确“优先遵循目标项目现有规范”。

建议覆盖：

- 开发模式下的固定执行顺序。
- 排除手机状态栏、Home Indicator、设计工具画布背景、标尺、水印等非业务 UI。
- fixed、sticky、悬浮、当前用户、选中态等业务语义的证据要求。
- 编码前的组件化模块分析。
- 跟随目标框架的推荐文件结构。
- 确认存在 Tab 时的目录结构策略。
- 静态交互的行为分析。
- 重复结构和模拟数据策略。
- 样式还原度规则。
- 图片资源策略。
- 简洁的开发前检查清单。

默认规则不能假设：

- 固定使用 React、Vue、Flutter 或其他单一框架。
- 固定使用 `src/views` 或某个业务目录。
- 固定使用某个 Toast/Message 组件。
- 固定使用某个公司 API 数据结构。
- 固定使用某个非蓝湖图片 CDN。

### 5.2 规则加载逻辑

在服务端配置区域新增规则加载能力：

```python
SERVER_DIR = Path(__file__).resolve().parent
DEFAULT_DEVELOPMENT_RULES_PATH = SERVER_DIR / "DEVELOPMENT_RULES.md"
MAX_DEVELOPMENT_RULES_BYTES = 256 * 1024
```

支持环境变量：

```bash
LANHU_DEVELOPMENT_RULES_PATH=/absolute/path/to/team-development-rules.md
```

推荐行为：

- 如果设置了 `LANHU_DEVELOPMENT_RULES_PATH`，读取该路径。
- 如果显式配置的文件不存在、为空、不是 UTF-8 或超过大小限制，请返回清晰错误。
- 如果没有配置外部路径，并且默认 Markdown 在 pip 安装环境中缺失，不要直接失败；应使用内置默认规则字符串或 package data 兜底。
- 返回规则时包含 `source`、`sha256` 和完整 `content`，方便 AI 和用户确认当前规则版本。

这样可以避免一个重要问题：项目现在是单文件 setuptools 配置，如果只新增 `DEVELOPMENT_RULES.md`，pip 安装后它不一定会出现在 `lanhu_mcp_server.py` 旁边。

### 5.3 默认规则的打包方式

不要只依赖源码目录中存在 `DEVELOPMENT_RULES.md`。

推荐两种方式二选一：

方式 A：Python 内置兜底内容。

- 仓库中保留 `DEVELOPMENT_RULES.md`，便于阅读和修改。
- 在 Python 中增加一个精简版 `DEFAULT_DEVELOPMENT_RULES_CONTENT`。
- 默认文件存在时读取文件；默认文件缺失时使用内置内容。
- 如果用户显式配置了外部路径，则不静默兜底，必须提示该外部文件错误。

方式 B：通过 package data 打包。

- 把服务端改造成 package，或正确配置 setuptools package data。
- 使用 `importlib.resources` 读取默认规则文件。
- Docker 中仍然复制 `DEVELOPMENT_RULES.md`，方便容器运行时覆盖。

考虑当前项目使用：

```toml
[tool.setuptools]
py-modules = ["lanhu_mcp_server"]
```

所以第一版 PR 更建议使用“方式 A：Python 内置兜底内容”，改动小，风险低。

### 5.4 新增 MCP 工具

新增工具：

```text
lanhu_get_development_rules
```

用途：

- 返回当前完整开发规则。
- 提醒 AI 在设计稿开发前读取规则。
- 不访问蓝湖接口，不依赖网络，执行快且安全。

成功返回建议：

```json
{
  "status": "success",
  "source": "/path/to/DEVELOPMENT_RULES.md",
  "sha256": "...",
  "content": "...",
  "required_next_step": "Analyze modules, file structure, and static behavior before coding."
}
```

失败返回建议：

```json
{
  "status": "error",
  "message": "Unable to read development rules ...",
  "required_action": "Fix the rules file or unset LANHU_DEVELOPMENT_RULES_PATH."
}
```

### 5.5 开发模式 Gate

不要让所有设计分析都强依赖开发规则。推荐使用可选参数或环境变量。

方案 A：增加可选参数。

```python
async def lanhu_get_ai_analyze_design_result(
    url: str,
    design_names: Union[str, List[str]],
    for_development: bool = False,
    ...
)
```

行为：

- `for_development=False`：保持原有设计分析行为。即使默认规则文件缺失，也不阻断普通分析。
- `for_development=True`：读取并返回完整开发规则；规则不可用时，在访问蓝湖网络接口前阻断并提示错误。

方案 B：增加严格模式环境变量。

```bash
LANHU_REQUIRE_DEVELOPMENT_RULES=false
```

行为：

- 默认 `false`，保持上游兼容。
- 设置为 `true` 时，设计分析强制要求开发规则可用。

方案 A 更适合作为公共 PR 的默认设计，因为它最明确、最不影响老用户。方案 B 可以作为团队级强制策略补充。

### 5.6 工具描述更新

更新工具描述时要保持克制，不能写成会误导用户的硬保证。

`lanhu_get_designs` 和 `lanhu_get_design_slices`：

- 增加提示：当用户要根据设计稿开发 UI 时，应先调用 `lanhu_get_development_rules`。
- 不阻断正常设计列表和切图获取。

`lanhu_get_ai_analyze_design_result`：

- 如果采用方案 A，新增 `for_development` 参数说明。
- 说明开发模式会返回开发规则，并要求先完成模块化分析、文件结构分析和行为分析。
- 明确画板坐标不是运行时定位和业务语义证据。

### 5.7 图片资源策略

图片策略必须可配置，不能直接破坏上游默认行为。

推荐参数：

```python
asset_mode: Literal["existing", "lanhu_url", "local_placeholder"] = "existing"
```

行为：

- `existing`：保持上游当前行为。
- `lanhu_url`：保留蓝湖返回的图片 URL。
- `local_placeholder`：把远程 URL 替换为本地路径占位符，并返回下载映射表。

如果第一版 PR 不想扩大改动，可以先不加 `asset_mode`，只保持上游默认图片行为，并在规则文档中说明：如果团队需要使用蓝湖原始 URL，应通过后续配置或参数开启。

不要在这个 PR 中加入自动上传图片到第三方平台的逻辑。

## 6. 默认规则内容建议

默认规则文档可以按下面方向写，保持通用。

设计范围：

- 排除手机状态栏、Home Indicator、系统通知图标、设计工具画布背景、标尺、标注线、选中框和水印。
- 不要误删业务导航、标题栏、Tab、底部业务导航。

语义证据：

- 画板坐标只代表几何位置。
- 不能仅凭元素位于顶部、底部、贴边、截图裁切、颜色强调或单个数值，推断 fixed、sticky、悬浮、当前用户、选中态、推荐态等业务语义。
- 只有 CSS、设计标注、交互说明或需求文档明确支持时，才实现固定/吸附/特殊业务身份。

模块化分析：

- 编码前识别页面容器职责、组件边界、重复 Item、模拟数据、共享逻辑、状态和文件结构。
- 不为了组件化而拆空壳组件。
- 组件拆分不能引入额外 DOM 包装、默认间距、定位上下文或样式继承变化。

文件结构：

- 目标项目已有规范优先。
- 没有规范时，为当前页面创建业务模块目录。
- `index` 作为业务入口。
- `components`、`type.ts`、`database.ts/js`、`hooks` 只在确实需要时创建。

Tab：

- 确认存在页面级 Tab 时，业务根 `index` 负责 Tab 切换、当前 Tab 状态和公共背景/容器。
- 每个已确认 Tab 有独立目录和入口文件。
- 只提供某个 Tab 设计但已确认其他 Tab 名称时，可以创建其他 Tab 的框架原生最小入口，但不得虚构完整 UI。

行为分析：

- 编码前标记有行为的区域。
- 覆盖实际存在或有证据的 Tab、按钮、进度条、滚动容器、横向列表、弹窗、抽屉、轮播、输入、选择、加载和空状态。
- 每项行为说明触发方式、初始状态、交互后状态、静态反馈、证据、模拟数据需求和待确认项。
- 只实现本地状态、视图切换、提示反馈、模拟数据筛选和滚动表现。
- 不为了静态还原新增依赖。

样式还原：

- 以设计画板尺寸作为基准。
- 保留尺寸、间距、颜色、字号、字重、行高、圆角、边框、阴影、透明度、渐变、图片和裁剪。
- HTML/CSS 是主要视觉来源，Design Tokens 作为补充。
- 分析间距时先区分“屏幕/模块容器边距”和“子元素之间的间距”。如果一组内容整体距离屏幕左右边缘固定，应优先用父容器 `padding-left` / `padding-right` 或目标平台等价容器内边距表达；子元素的 `margin` 只用于组内元素间隔或局部偏移，不要用每个子元素的 margin 反复模拟同一个屏幕边距。
- 父容器 padding 不能改变设计中的背景、边框、圆角、裁剪或可点击区域语义；如果容器本身有背景/边框/圆角，需判断边距属于外层页面容器还是该业务容器内部。
- 间距方式优先遵循目标项目。如果目标项目要求兼容老环境，可以使用 margin 代替 flex gap 并控制首尾项；如果目标项目已经统一使用 gap，则遵循项目规范。

重复数据：

- 列表、表格、网格、重复卡片、标签、菜单项、统计块、步骤项、轮播项等重复结构，应优先使用一个 Item 加模拟数据循环渲染。
- 固定硬文案可以直接写在模板中。
- 未来可能来自 API 的数据放在当前业务数据文件或项目既有数据组织位置。

图片资源：

- 不用 SVG、CSS 图形、Emoji、占位图或无关图片替代设计图片。
- 根据 `asset_mode` 或项目默认策略使用蓝湖 URL 或本地占位路径。
- 图片迁移到其他平台必须作为单独功能处理。

## 7. 实现检查清单

代码：

- 新增规则加载 helper。
- 新增 `lanhu_get_development_rules`。
- 给设计分析增加显式开发模式，或增加默认关闭的严格模式。
- 只有开发模式或严格模式才强制读取并注入完整规则。
- 非开发设计分析不被规则文件缺失阻断。
- 样式规则明确区分父容器 padding 和子元素 margin：屏幕左右安全边距、页面统一左右留白优先由父容器承载，元素间距再由子元素 margin 或项目既有间距方式承载。
- 默认图片行为保持上游兼容。
- 如需蓝湖原始 URL，使用参数或配置开启。
- Docker 支持读取和覆盖规则文档。
- pip 安装环境中默认规则缺失时有安全兜底。

文档：

- README 说明 `LANHU_DEVELOPMENT_RULES_PATH`。
- README 说明开发模式或严格模式。
- 如果增加 `asset_mode`，README 说明各模式含义。
- README 明确普通设计分析默认不变。

测试：

- 规则工具返回 source、sha256、完整 content。
- 外部规则路径可以覆盖默认规则。
- 自定义规则路径错误时返回清晰错误。
- 默认 Markdown 缺失时，非开发分析不阻断。
- 默认 Markdown 缺失时，开发模式在访问网络前阻断。
- pip/package 兜底逻辑可用。
- 工具描述包含开发规则流程。
- 工具描述包含“画板坐标不是运行时语义”的约束。
- 图片策略默认保持上游行为。
- 显式蓝湖 URL 模式能保留远程 URL。
- 不出现 Delta、上传 Cookie、私有接口参数。

## 8. 验证命令

提交 PR 前运行：

```bash
python -m py_compile lanhu_mcp_server.py
python -m unittest discover -s tests -v
python -m pytest -q
git diff --check
```

如果没有安装 pytest：

```bash
pip install -e ".[dev]"
python -m pytest -q
```

最后检查 diff：

```bash
git status --short
git diff --stat
git diff
```

## 9. PR 内容建议

推荐分支名：

```text
feat/design-development-workflow
```

推荐提交标题：

```text
feat: add configurable Lanhu design-to-code workflow rules
```

推荐 PR Summary：

```markdown
## Summary

- Add a configurable development rules workflow for Lanhu design-to-code tasks.
- Expose a local MCP tool for reading the current development rules.
- Add explicit development mode so UI implementation guidance can be prepended
  without breaking normal design analysis.
- Document modular analysis, behavior analysis, evidence requirements, and asset
  handling for AI-generated UI code.

## Compatibility

- Existing design analysis behavior remains unchanged by default.
- Development rules become mandatory only in explicit development mode or strict
  server mode.
- Default rules can be overridden with LANHU_DEVELOPMENT_RULES_PATH.
- No private upload service, cookie, token, or third-party asset migration logic
  is included.

## Verification

- python -m py_compile lanhu_mcp_server.py
- python -m unittest discover -s tests -v
- python -m pytest -q
- git diff --check
```

## 10. PR 审查前必须避免的问题

提交前重点检查：

- 不能让 `DEVELOPMENT_RULES.md` 成为 pip 安装后缺失就崩的隐藏运行时依赖。
- 不能阻断只想看设计图或分析设计图的用户。
- 不能默认改变上游图片本地化行为。
- 不能提交私有服务、私有 Cookie、Token 或内部 API 名称。
- 不要让测试依赖大段 Markdown 的精确措辞，除非这些措辞是公开契约。
- 不要提交生成数据、日志、虚拟环境、本地缓存或个人 agent-memory 文件。

## 11. 推荐拆分策略

如果 PR 变大，可以拆成两个：

1. 规则基础设施：
   - `DEVELOPMENT_RULES.md`
   - 规则加载 helper
   - `lanhu_get_development_rules`
   - README、配置、Docker 更新
   - pip 安装兜底
   - 测试

2. 开发模式分析增强：
   - `for_development` 或严格模式
   - 模块化分析和行为分析提示注入
   - 可选图片资源模式
   - 更多契约测试

如果 diff 仍然聚焦、测试完整，一个 PR 也可以接受。
