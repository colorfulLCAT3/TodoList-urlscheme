"""
TodoList应用的前后端通信API
"""
import sys
from pathlib import Path
from backend.database.operations import TodoDatabase
from backend.database.data_export import DataExportManager
from backend.api.mixins.category_mixin import CategoryMixin
from backend.api.mixins.config_mixin import ConfigMixin
from backend.api.mixins.datafile_mixin import DatafileMixin
from backend.api.mixins.tag_mixin import TagMixin
from backend.api.mixins.task_mixin import TaskMixin
from backend.api.mixins.task_relation_mixin import TaskRelationMixin
from backend.api.mixins.urlscheme_mixin import UrlSchemeMixin
from backend.api.mixins.utility_mixin import UtilityMixin
from backend.api.mixins.webdav_mixin import WebDAVMixin
from backend.features.urlscheme.url_scheme import UrlSchemeManager
from backend.utils.logger import LogManager

# 确保能找到database模块
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

class TodoApi(
    CategoryMixin, ConfigMixin, DatafileMixin, TagMixin,
    TaskMixin, TaskRelationMixin, UrlSchemeMixin, UtilityMixin, WebDAVMixin, LogManager
):
    """TodoList应用的API类，提供前后端通信接口"""

    def __init__(self, is_android, sync_manager):
        super().__init__()
        self.db = TodoDatabase()
        self.is_android = is_android
        self.sync_manager = sync_manager
        self._data_manager = DataExportManager(self.service)
        self._url_scheme_manager = UrlSchemeManager(self.db)
        try:
            self.service.add_new_desktop_task_reminder()
            self.get_logger.info("任务提醒器已重置")
        except Exception as e:
            self.get_logger.warning(f"重置任务提醒器失败: {e}")