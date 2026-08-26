# TodoList URL 调用方法

通过自定义 URL scheme 协议，可以从**网页 / 脚本 / 其他应用**唤起 TodoList 并推送待办任务，无需打开应用手动新建。

## 协议格式

```
todolist://add?data=<urlencode(JSON)>
```

`data` 参数是 **URL 编码后的 JSON**，支持三种形态：

| 形态 | 说明 | 示例 |
|---|---|---|
| 任务数组 | 一次推送多个任务 | `[{"title":"任务1"},{"title":"任务2"}]` |
| 单个对象 | 推送一个任务 | `{"title":"任务1"}` |
| `{"tasks":[...]}` | 包裹数组 | `{"tasks":[{"title":"任务1"}]}` |

## 任务字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `title` | string | ✅ | 任务标题 |
| `description` | string | ❌ | 备注，支持 `**加粗**` 和换行 |
| `completed` | bool | ❌ | 是否已完成，默认 `false` |
| `priority` | string | ❌ | `high` / `medium` / `low` / `none`，默认 `none` |
| `category_id` | string | ❌ | 分类 ID（需与库内分类一致，不存在则忽略） |
| `due_date` | string | ❌ | 开始日期时间，格式 `YYYY-MM-DD HH:MM` 或 ISO `YYYY-MM-DDTHH:MM` |

> 兼容性：`category_id` / `due_date` 也接受驼峰写法 `categoryId` / `dueDate`。

### 完整示例 JSON

```json
{
  "title": "写季度总结",
  "description": "**重点**：本周五前提交",
  "completed": false,
  "priority": "high",
  "category_id": "work",
  "due_date": "2026-09-01 18:00"
}
```

## Windows 端调用

### 前置条件

1. 先启动一次 TodoList 应用，它会自动向注册表注册 `todolist://` 协议（写入 `HKCU\Software\Classes\todolist`）。
2. 应用启动时会监听本机 `127.0.0.1:5200` 端口，用于把 URL 转发给已运行的实例（重复唤起时不会开多个窗口）。

### 方式一：浏览器 / 网页唤起（推荐）

在网页中点击链接或按钮，用**隐藏 iframe** 触发协议（比直接跳转更稳，页面不离开）：

```html
<a href="todolist://add?data=%7B%22title%22%3A%22%E4%B9%B0%E7%89%9B%E5%A5%B6%22%7D">添加买牛奶任务</a>
```

```javascript
// 用 iframe 触发，避免页面跳转
const url = 'todolist://add?data=' + encodeURIComponent(JSON.stringify({ title: '写周报' }));
const iframe = document.createElement('iframe');
iframe.style.display = 'none';
iframe.src = url;
document.body.appendChild(iframe);
setTimeout(() => iframe.remove(), 1500);
```

> 项目自带的可视化测试页：[tests/url_scheme_test.html](tests/url_scheme_test.html)，填表即可生成 URL 并唤起。

### 方式二：命令行 / 脚本

```bash
# 单任务
start todolist://add?data=%7B%22title%22%3A%22%E5%AE%89%E6%8E%92%E4%BC%9A%E8%AE%AE%22%7D

# 多任务（数组）
start "todolist://add?data=%5B%7B%22title%22%3A%22A%22%7D%2C%7B%22title%22%3A%22B%22%7D%5D"
```

应用启动命令也支持直接传入 `--url` 参数（协议注册时使用）：`TodoList.exe --url "todolist://add?data=..."`。

## Android 端调用

### 前置条件

安装 TodoList Android 应用（应用通过 manifest 的 `intent-filter` 注册 `todolist://` 协议）。

### 方式一：浏览器 / 网页唤起

```html
<a href="todolist://add?data=%7B%22title%22%3A%22%E4%B9%B0%E8%8F%9C%22%2C%22due_date%22%3A%222026-09-01%2019%3A00%22%7D">添加买菜任务</a>
```

点击后会唤起 TodoList 应用并把任务加入待办列表。

### 方式二：adb 命令行（调试用）

```bash
adb shell am start -a android.intent.action.VIEW -d "todolist://add?data=<urlencode(JSON)>"
```

### 方式三：其他 Android 应用（Intent）

```java
Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse("todolist://add?data=" + Uri.encode(json)));
startActivity(intent);
```

### Android 字段补充

Android 端同样支持所有字段，`due_date` 推入后应用会据此设置**提前提醒**（提醒时间点在设置中配置），并参与**日历视图**展示。

## 注意事项

- `data` 里的 JSON 必须 **URL 编码**（`encodeURIComponent` / `urlencode`），否则中文和特殊字符会解析失败。
- 无 `title` 的任务会被跳过。
- 分类 ID 在库内不存在时会被忽略（任务归为无分类）。
- Windows 端需**先启动一次应用**完成协议注册；Android 端安装即注册。
- 重复推送时：Windows 会转发给已运行实例（不重开窗口）；Android 通过 `onNewIntent` 合并到当前实例。
