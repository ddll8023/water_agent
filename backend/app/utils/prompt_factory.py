from functools import lru_cache
import os
import yaml
from app.utils.file import ROOT_DIR

# 获取脚本所在目录，用于定位配置文件
SCRIPT_DIR = os.path.join(ROOT_DIR, "app", "prompt")


class PromptFactory:

    @property
    def chat(self):
        """获取对话模型提示词"""
        config_path = os.path.join(SCRIPT_DIR, "chat.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @property
    def alert(self):
        """获取预警提示词"""
        config_path = os.path.join(SCRIPT_DIR, "alert.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @property
    def report(self):
        """获取报告生成提示词"""
        config_path = os.path.join(SCRIPT_DIR, "report.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


@lru_cache()
def get_prompt_factory():
    return PromptFactory()


get_prompt = get_prompt_factory()
