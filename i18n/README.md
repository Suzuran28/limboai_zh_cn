# LimboAI 中文本地化（i18n）

本目录是 LimboAI 的中文本地化工作区：**英文原文始终保留**，中文以独立数据文件提供，
构建时分别注入编辑器界面（翻译域）与类参考文档（双语 XML）。

## 效果

| 部分 | 语言切换 | 说明 |
|---|---|---|
| 编辑器界面（按钮/菜单/提示/对话框） | ✅ 跟随编辑器语言；也可用项目设置强制 | 英文源码字符串作为 msgid；中文放在 `i18n/ui/*.po` |
| 内置类参考文档（F1） | ❌ 编译进二进制，不能运行时切换 | 中英并列：中文段落 + `[b]English[/b]` 原文 |
| 运行时控制台信息（`RTR`） | ✅ 跟随游戏语言 | 使用项目自身的翻译（Project Settings → Localization） |

## 目录结构

```
i18n/
├── README.md                  # 本文件
├── docs/
│   ├── GLOSSARY.md            # 术语表与翻译规范
│   └── docs_zh.json           # 类参考中文译文（唯一数据源）
├── tools/
│   ├── extract_ui_strings.py  # 从源码提取 TTR() 字符串 → .po（可 --check 校验）
│   ├── build_doc_classes.py   # 生成中英双语的 doc XML → gen/doc_classes_zh
│   └── merge_doc_parts.py     # 可选：合并临时 parts/*.json → docs_zh.json
└── ui/
    └── limboai.zh_CN.po       # 编辑器界面译文（构建时复制到 addons/limboai/translations/）
```

## 编辑器界面

* 运行时由 `compat/translation.cpp` 把 `res://addons/limboai/translations/*.po`
  解析进名为 `limboai` 的 `TranslationDomain`，`TTR()` 通过它查表。
  这样绕开了编辑器启动阶段禁用主翻译域的问题（GDExtension 的原实现走主域）。
* **修改 `.po` 后无需重新编译**：把文件同步到项目的 `addons/limboai/translations/`
  并重启编辑器即可。只有修改了 C++ 源码里的 `TTR()` 原文才需要重新提取并构建。
* 语言选择：默认跟随编辑器语言（`TranslationServer.get_locale()`）。
  若想在英文编辑器里也显示中文，在 `project.godot` 里加：

  ```ini
  [limbo_ai]
  editor/language="zh_CN"
  ```

  留空/删除则跟随编辑器语言。
* 增加其他语言：新增 `i18n/ui/limboai.<locale>.po`（头部 `Language: <locale>`），
  重新构建（或手动复制到项目）即可。

### 更新界面译文的流程

```powershell
# 1. 修改源码里的 TTR() 文案后，重新生成 PO 骨架（保留已有译文）
python i18n/tools/extract_ui_strings.py --po i18n/ui/limboai.zh_CN.po
# 2. 校验（缺译/多余条目会列出来）
python i18n/tools/extract_ui_strings.py --check --po i18n/ui/limboai.zh_CN.po
```

## 类参考文档（F1）

* 上游英文 XML 位于 `doc_classes/`，**不做修改**，便于合并上游更新。
* 中文译文位于 `i18n/docs/docs_zh.json`，按类名 / 字段 / 成员名索引。
* `i18n/tools/build_doc_classes.py` 在构建时读取二者，输出双语 XML 到
  `gen/doc_classes_zh/`，再由 `GodotCPPDocData` 编译进编辑器二进制。

双语排布规则（由脚本自动完成）：

* `brief_description`：`中文（English）`
* `description` / `member` / `method` / `signal` / `constant`：
  * 英文为单段且不超过 200 字符 → `中文（English）`
  * 否则 → 中文段落 + 空行 + `[b]English[/b]` + 空行 + 英文原文

翻译规范与术语见 [`docs/GLOSSARY.md`](docs/GLOSSARY.md)。

```powershell
# 合并分批译文并校验覆盖率
python i18n/tools/merge_doc_parts.py
python i18n/tools/build_doc_classes.py --check
```

## 构建

仅构建 Windows x86_64（MinGW，静态链接 C++ 运行时）。`api_version=4.6` 与官方 CI
（`GODOT_CPP_API_VERSION`，见 `deps.env`）一致：产出的扩展可在 Godot 4.6+ 加载，
在 4.7 上正常使用：

```powershell
$env:PATH = "C:\mingw64\bin;" + $env:PATH
# 编辑器（含文档 + 界面翻译部署）
scons platform=windows target=editor arch=x86_64 use_mingw=yes use_static_cpp=yes api_version=4.6 --project=demo -j8
# 导出模板（运行时）
scons platform=windows target=template_release arch=x86_64 use_mingw=yes use_static_cpp=yes api_version=4.6 --project=demo -j8
```

`--project=DIR` 会把产物部署到 `DIR/addons/limboai/{bin,icons,translations}`。
若只面向 Godot 4.7+，可以去掉 `api_version=4.6`（默认 4.7），但 4.6 上会拒绝加载。

## 已知限制

* 类参考文档编译进二进制，**改动文档译文必须重新构建**；运行时不可切换语言。
* 任务类型名（`BTSequence` → `Sequence`）属于类标识符，保持英文（与 Godot 类名一致）。
* 运行时 `RTR()` 走项目翻译，需要在项目中把对应 `.po` 加入
  Project Settings → Localization → Translations 才会生效。
