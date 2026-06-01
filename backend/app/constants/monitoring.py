"""监测数据服务常量定义"""

# ========== 真实API配置 ==========
API_URL = "http://111.47.99.130:8081/water-quality/list"
API_HEADERS = {
    "Authorization": (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9."
        "eyJzdWIiOiJhZG1pbjAxIiwiaWF0IjoxNzgwMjk5NjYxLCJleHAiOjE3ODA5MDQ0NjF9."
        "wihaN5us9Qzx0fC5okU_pagLstOlvMVCMQtsYgWGj6Dal4vO10qv_beI0V6wWJWqJbvhghrzkP71C0ISq2xRDg"
    ),
}
API_PARAMS = {
    "currentPage": 1,
    "pageSize": 10,
    "position": "水厂",
}

FIELD_TO_INDICATOR: dict[str, int] = {
    "ph": 1,  # pH → PH
    "rjy": 2,  # 溶解氧 → RJY
    "cod": 3,  # 化学需氧量 → COD
    "ad": 4,  # 氨氮 → AD
    "swt": 5,  # 水温 → SWT
    "zd": 6,  # 浊度 → ZD
    "ddl": 7,  # 电导率 → DDL
    "yl": 8,  # 余氯 → YL
}
