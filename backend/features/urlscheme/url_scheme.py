"""
URL Scheme 模块 - 接收外部网页推送的待办事项

协议格式: todolist://add?data=<urlencoded-json>
data 支持三种形态: JSON 数组、单个任务对象、{"tasks": [...]}
"""
import json
from urllib.parse import urlsplit, unquote
from backend.utils.logger import LogManager

URL_SCHEME = 'todolist'
LISTENER_PORT = 5200

VALID_PRIORITIES = ('high', 'medium', 'low', 'none')


def _to_bool(value) -> bool:
    """把常见布尔表示归一化为 bool"""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes', 'on')
    return False


def _is_valid_url(url: str) -> bool:
    """校验 URL 是否属于本应用 scheme"""
    try:
        return urlsplit(url).scheme.lower() == URL_SCHEME
    except ValueError:
        return False


def parse_url(url: str) -> list:
    """解析 URL，提取待办任务原始字典列表

    Returns:
        任务字典列表；解析失败返回空列表
    """
    if not url or not _is_valid_url(url):
        return []

    try:
        split = urlsplit(url)
        data_param = unquote(split.query or '')
        if not data_param.startswith('data='):
            return []
        raw = data_param[len('data='):]
        parsed = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        return []

    if isinstance(parsed, dict):
        if isinstance(parsed.get('tasks'), list):
            return parsed['tasks']
        return [parsed]
    if isinstance(parsed, list):
        return parsed
    return []


def normalize_task(raw: dict, category_ids: set = None) -> dict:
    """把外部传入的任务字段归一化为 db.add_task 兼容格式

    Returns:
        归一化后的任务字典；缺少 title 时返回 None（该任务被跳过）
    """
    if not isinstance(raw, dict):
        return None

    title = str(raw.get('title') or '').strip()
    if not title:
        return None

    priority = str(raw.get('priority') or 'none').strip().lower()
    if priority not in VALID_PRIORITIES:
        priority = 'none'

    category_id = raw.get('category_id')
    if category_id is None:
        category_id = raw.get('categoryId')
    if category_id is not None:
        category_id = str(category_id)
        # 分类不存在时忽略，避免写入无效外键
        if category_ids is not None and category_id not in category_ids:
            category_id = None

    due_date = raw.get('due_date')
    if due_date is None:
        due_date = raw.get('dueDate')
    if due_date is not None:
        due_date = str(due_date)

    return {
        'title': title,
        'description': str(raw.get('description') or ''),
        'completed': _to_bool(raw.get('completed', False)),
        'priority': priority,
        'categoryId': category_id,
        'dueDate': due_date,
    }


class UrlSchemeManager(LogManager):
    """处理 URL scheme 推送的待办，写入本地数据库"""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._category_ids = None

    def _load_category_ids(self) -> set:
        if self._category_ids is None:
            try:
                self._category_ids = {str(c['id']) for c in self.db.get_all_categories()}
            except Exception:
                self._category_ids = set()
        return self._category_ids

    def handle_url(self, url: str) -> dict:
        """解析并入库一个 URL 中的全部待办

        Returns:
            {'added': int, 'skipped': int, 'error': str|None}
        """
        result = {'added': 0, 'skipped': 0, 'error': None}
        try:
            raw_tasks = parse_url(url)
            category_ids = self._load_category_ids()
            for raw in raw_tasks:
                task = normalize_task(raw, category_ids)
                if task is None:
                    result['skipped'] += 1
                    continue
                try:
                    self.db.add_task(task)
                    result['added'] += 1
                except Exception as e:
                    self.get_logger.error(f"[URLScheme] 待办入库失败: {e}")
                    result['skipped'] += 1
            self.get_logger.info(f"[URLScheme] 处理完成，新增 {result['added']} 条，跳过 {result['skipped']} 条")
        except Exception as e:
            result['error'] = str(e)
            self.get_logger.error(f"[URLScheme] 处理 URL 异常: {e}")
        return result
