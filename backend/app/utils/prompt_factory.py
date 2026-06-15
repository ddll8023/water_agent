from functools import lru_cache
import os
import yaml
from app.utils.file import ROOT_DIR

# 获取脚本所在目录，用于定位配置文件
SCRIPT_DIR = os.path.join(ROOT_DIR, "app", "prompt")


class PromptFactory:

    def __init__(self):
        self._cache = {}

    @property
    def chat(self):
        """获取对话模型提示词"""
        if "chat" not in self._cache:
            config_path = os.path.join(SCRIPT_DIR, "chat.yaml")
            with open(config_path, "r", encoding="utf-8") as f:
                self._cache["chat"] = yaml.safe_load(f)
        return self._cache["chat"]

    @property
    def alert(self):
        """获取预警提示词"""
        if "alert" not in self._cache:
            config_path = os.path.join(SCRIPT_DIR, "alert.yaml")
            with open(config_path, "r", encoding="utf-8") as f:
                self._cache["alert"] = yaml.safe_load(f)
        return self._cache["alert"]

    @property
    def report(self):
        """获取报告生成提示词"""
        if "report" not in self._cache:
            config_path = os.path.join(SCRIPT_DIR, "report.yaml")
            with open(config_path, "r", encoding="utf-8") as f:
                self._cache["report"] = yaml.safe_load(f)
        return self._cache["report"]

    @property
    def chat_agent(self):
        """获取智能问答 Agent 提示词"""
        if "chat_agent" not in self._cache:
            config_path = os.path.join(SCRIPT_DIR, "chat_agent.yaml")
            with open(config_path, "r", encoding="utf-8") as f:
                self._cache["chat_agent"] = yaml.safe_load(f)
        return self._cache["chat_agent"]


@lru_cache()
def get_prompt_factory():
    return PromptFactory()


get_prompt = get_prompt_factory()
