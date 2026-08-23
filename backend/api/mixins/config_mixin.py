# backend/api/mixins/config_mixin.py

import backend.globals
from backend.utils import utils
from backend.utils.response_wrapper import api_handler

class ConfigMixin:
    """配置操作 Mixin"""
    CONFIG_REGISTRY = {
        'window_on_top': {
            'key': 'window_on_top',
            'default': False,
            'transform': utils.str_to_bool,
            'post_set': lambda self, value: setattr(
                backend.globals.window, 'on_top',
                utils.str_to_bool(self.db.get_setting('window_on_top', False))
            )
        },
        'theme': {
            'key': 'theme',
            'default': 'light'
        },
        'language': {
            'key': 'language',
            'default': 'zh'
        },
        'auto_start': {
            'key': 'auto_start_enabled',
            'default': False,
            'transform': utils.str_to_bool,
            'post_set': lambda self, value: self.service.set_auto_start_system(value)
        },
        'remind_enabled': {
            'key': 'remind_enabled',
            'default': True,
            'transform': utils.str_to_bool
        },
        'remind_offsets': {
            'key': 'remind_offsets',
            'default': '30,10,5'
        }
    }

    @api_handler
    def get_config(self, keys=None):
        """
        获取配置项
        :param keys: 可选，字符串（逗号分隔）或列表，指定要获取的配置名称；不传则返回全部
        """
        # 确定要遍历的条目
        if keys is None:
            items = self.CONFIG_REGISTRY.items()
        else:
            if isinstance(keys, str):
                keys = [k.strip() for k in keys.split(',') if k.strip()]
            items = [(k, v) for k, v in self.CONFIG_REGISTRY.items() if k in keys]
        result = {}
        for name, cfg in items:
            result[name] = self.db.get_setting(cfg['key'], cfg.get('default'))
            transform = cfg.get('transform')
            if transform:
              result[name] = transform(result[name])
        return result

    @api_handler
    def set_config(self, key, value):
        cfg = self.CONFIG_REGISTRY.get(key)
        if not cfg:
            raise Exception(f'未知配置项: {key}')
        self.db.set_setting(cfg['key'], value)
        post_set = cfg.get('post_set')
        if post_set:
            result = post_set(self, value) if callable(post_set) else getattr(self, post_set)(value)
            if result is False:
                raise Exception(f"后处理执行失败")