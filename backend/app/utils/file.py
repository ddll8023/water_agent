import json
import os

import aiofiles

# 根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def save_file(content: bytes, path: str):
    """异步保存文件"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)
    return path


async def save_json(dir_path: str, file_name: str, data: dict) -> str:
    """异步保存结构化数据为JSON文件"""
    file_path = os.path.join(dir_path, file_name)
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    return file_path
