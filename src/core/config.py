import json, os, pathlib

def load_config():
    # 配置文件路径：项目根目录/assets/units.json
    root = pathlib.Path(__file__).resolve().parent.parent.parent
    path = root / "assets" / "units.json"
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 全局实例，只需在启动时调用一次
_config = None

def get_config():
    global _config
    if _config is None:
        _config = load_config()
    return _config