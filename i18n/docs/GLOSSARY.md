# LimboAI 中文本地化术语表与翻译规范

本文件供翻译者（人或 AI）参考，用于保持编辑器界面与类参考文档的中文用词一致。

## 一、总体要求

1. **中文在前，英文原文必须完整保留**（由 `i18n/tools/build_doc_classes.py` 自动拼装，不要手写英文段）。
2. 只翻译自然语言；**不翻译**标识符：类名（`BTTask`）、方法名（`_tick`）、属性名（`custom_name`）、枚举常量（`SUCCESS`）、信号名（`task_finished`）、GDScript/C++ 代码。
3. **完整保留 BBCode 标记**及其中的目标，例如 `[b]`、`[i]`、`[code]`、`[codeblock]`、`[member behavior_tree]`、`[method _tick]`、`[param delta]`、`[constant SUCCESS]`、`[enum BT.Status]`、`[Node]`、`[BehaviorTree]`、`[br]`。标记内部的类名/成员名保持英文，标记外的说明文字译为中文。
4. 原文中的 `[b]Note:[/b]`、`[b]Warning:[/b]` 译为 `[b]注意：[/b]`、`[b]警告：[/b]`（保留标记，只替换文字）。
5. 保留原文的段落结构（用 `\n` 分隔）；不要合并或拆分段落，不要增删信息。
6. 中文使用中文标点（，。：；！？、（）），英文缩写与代码保持原样；中英文之间留一个半角空格（如 `BehaviorTree 资源`）。
7. 语气：简洁、技术化、面向开发者；与 Godot 官方中文文档风格一致（“节点”“资源”“场景”“检查器”“信号”“属性”“方法”“枚举”）。
8. 不把 `[code]` 里的内容翻译成中文；`[codeblock]` 整块保留。
9. 专有名词首次出现可保留英文（如 `tick`），不要生造译名。

## 二、术语对照

| English | 中文 |
|---|---|
| behavior tree | 行为树 |
| task | 任务 |
| leaf task | 叶子任务 |
| composite (task) | 组合（任务） |
| composite node | 组合节点 |
| decorator | 装饰器 |
| action | 动作 |
| condition | 条件 |
| selector | 选择器 |
| sequence | 序列 |
| parallel | 并行 |
| probability / percent | 概率 / 百分比 |
| weight | 权重 |
| blackboard | 黑板 |
| blackboard plan | 黑板计划 |
| blackboard variable | 黑板变量 |
| variable | 变量 |
| value | 值 |
| hint / hint string | 提示 / 提示字符串 |
| subtree | 子树 |
| parent / child | 父任务 / 子任务（节点语境用父节点/子节点） |
| root | 根（根任务） |
| state machine | 状态机 |
| hierarchical state machine | 分层状态机 |
| state | 状态 |
| transition | 过渡 |
| event | 事件 |
| agent | 代理 |
| owner | 拥有者 |
| tick | tick（每次执行） |
| status | 状态 |
| running / success / failure | 运行中 / 成功 / 失败 |
| custom name | 自定义名称 |
| enabled / disabled | 启用 / 禁用 |
| editor / inspector | 编辑器 / 检查器 |
| scene / node / resource / script | 场景 / 节点 / 资源 / 脚本 |
| runtime | 运行时 |
| instance | 实例 |
| frame / delta | 帧 / 时间增量 |
| cooldown | 冷却 |
| prefetch | 预取 |
| debugger | 调试器 |
| documentation / class reference | 文档 / 类参考 |
| favorite tasks | 收藏任务 |
| category | 类别 |
| filter | 过滤 |
| snapshot | 快照 |
| random | 随机 |
| dynamic | 动态 |
| utility | 工具 |
| scene tree | 场景树 |
| NodePath | NodePath（不译） |

## 三、常见句式

- "Base class for ..." → “……的基类。”
- "Called when ..." → “当……时调用。”
- "Returns ..." → “返回……”
- "If ..., ..." → “如果……，则……”
- "See also [method x]." → “另请参阅 [method x]。”
- "**Note:** ..." → “**注意：**……”
- 方法说明的第二人称/祈使句保持简洁，如 “设置任务的持续时间。”

## 四、输出 JSON 格式

```json
{
  "BTWait": {
    "brief": "等待指定 [member duration] 结束后返回 [code]SUCCESS[/code] 的行为树动作。",
    "desc": "",
    "methods": {"_tick": "……"},
    "members": {"duration": "……"},
    "constants": {"STATUS_SUCCESS": "……"},
    "signals": {"finished": "……"}
  }
}
```

- `brief` 对应 `<brief_description>`；`desc` 对应 `<description>`。
- 只收录英文原文**非空**的条目；英文为空的字段直接省略（`desc` 可为空字符串或省略）。
- 键名必须与 XML 中的 `name` 属性完全一致（区分大小写、包含下划线）。
