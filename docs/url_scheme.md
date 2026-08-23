# TodoList URL Scheme 协议文档

通过自定义 URL Scheme，外部网页（或其他应用）可以唤起 TodoList，并向其推送一批待办事项。收到链接后应用会**自动入库、显示主窗口并刷新任务列表**。

## 协议格式

```
todolist://add?data=<urlencoded-json>
```

| 部分 | 说明 |
|---|---|
| `todolist://` | 自定义协议名，Windows 与 Android 已注册 |
| `add` | 操作名，当前仅支持添加待办 |
| `data` | 待办数据的 JSON，需经 URL 编码（`encodeURIComponent`） |

## 待办数据格式

`data` 参数支持三种 JSON 形态：

- **数组**：`[{...}, {...}]`（推荐，一次推送多条）
- **单个对象**：`{...}`
- **包裹对象**：`{"tasks": [{...}, ...]}`

每个待办项支持以下字段（**仅 `title` 必填**，其余可选）：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `title` | string | — | 任务标题，**必填**，空值任务会被跳过 |
| `description` | string | `""` | 任务备注，支持 `**加粗**` 与换行 |
| `completed` | bool | `false` | 完成状态，接受 `true/false/1/0/yes/no` |
| `priority` | string | `"none"` | 优先级：`high` / `medium` / `low` / `none`，其他值归为 `none` |
| `category_id` | string | `null` | 分类 ID，必须与库内已有分类一致，否则忽略该分类 |
| `due_date` | string | `null` | 开始日期时间，如 `"2026-08-30 18:00"`，原样透传 |

导入行为为**追加**，不会覆盖本地已有数据。

## 平台支持

| 平台 | 支持 | 实现方式 |
|---|---|---|
| Windows | ✅ | 注册表注册 scheme + localhost:5200 端口转发 |
| Android | ✅ | Manifest intent-filter 声明 + onNewIntent 捕获 |
| Linux / macOS | ❌ | 未实现 |

## 调用方式

### 方式一：网页唤起

在网页中触发协议跳转即可，推荐用隐藏 iframe（比 `location.href` 更稳，不会跳走页面）：

```html
<a href="todolist://add?data=%5B...%5D">添加到 TodoList</a>
```

```javascript
function pushToTodoList(tasks) {
    const url = 'todolist://add?data=' + encodeURIComponent(JSON.stringify(tasks));
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = url;
    document.body.appendChild(iframe);
    setTimeout(() => iframe.remove(), 1500);
}
```

### 方式二：命令行（Windows 冷启动）

应用未运行时，可用命令行唤起：

```bash
python main.py --url "todolist://add?data=<urlencoded-json>"
```

- **应用已运行**：URL 会转发给运行中的实例，由主窗口处理并显示
- **应用未运行**：应用启动后自动处理该 URL

## 示例

### 单条待办

```json
{"title": "买牛奶", "priority": "high", "due_date": "2026-08-30 18:00"}
```

```text
todolist://add?data=%7B%22title%22%3A%22%E4%B9%B0%E7%89%9B%E5%A5%B6%22%2C%22priority%22%3A%22high%22%2C%22due_date%22%3A%222026-08-30%2018%3A00%22%7D
```

### 多条待办（数组）

```json
[
  {"title": "高优先级示例", "priority": "high", "due_date": "2027-01-01 09:00"},
  {"title": "已完成示例", "completed": true},
  {"title": "普通示例"}
]
```

### JavaScript 生成完整 URL

```javascript
const tasks = [{ title: '买牛奶', priority: 'high' }, { title: '写周报' }];
const url = 'todolist://add?data=' + encodeURIComponent(JSON.stringify(tasks));
```

## 注意事项

1. **URL 长度限制**：Windows 下 URL 有约 2KB 长度限制，一次不要推送太多任务（每条约 100~200 字符）。
2. **分类校验**：`category_id` 必须与库内已有分类一致才会生效，否则该任务将不带分类。
3. **完成后自动刷新**：应用收到链接后会自动显示主窗口、刷新任务列表并弹出「已添加 N 个待办」提示。
4. **测试页**：项目提供 [tests/url_scheme_test.html](../tests/url_scheme_test.html)，可直接填表或一键推送示例任务测试。
