# backend/api/mixins/tag_mixin.py
from backend.utils.response_wrapper import api_handler

class TagMixin:
    """标签核心操作 Mixin"""

    @api_handler
    def get_all_tags(self):
        """获取所有标签"""
        return self.db.get_all_tags()

    @api_handler
    def delete_tag(self, tag_id):
        """删除标签"""
        self.db.delete_tag(tag_id)