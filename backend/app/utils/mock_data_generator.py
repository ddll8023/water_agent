"""模拟数据生成器：12座自动站的硬编码映射与指标值生成"""

import random

# ========== 12座自动站硬编码映射 ==========

RTU_STATION_CONFIG = {
    1: {
        "code": "QLS-A01",
        "reservoir_id": 1,
        "reservoir_name": "青龙山水库",
        "water_grade": "Ⅱ类",
    },
    2: {
        "code": "BLH-A01",
        "reservoir_id": 2,
        "reservoir_name": "白鹭湖水库",
        "water_grade": "Ⅱ类",
    },
    3: {
        "code": "MSH-A01",
        "reservoir_id": 3,
        "reservoir_name": "梅山水库",
        "water_grade": "Ⅲ类",
    },
    4: {
        "code": "XHD-A01",
        "reservoir_id": 4,
        "reservoir_name": "响洪甸水库",
        "water_grade": "Ⅱ类",
    },
    5: {
        "code": "FZL-A01",
        "reservoir_id": 5,
        "reservoir_name": "佛子岭水库",
        "water_grade": "Ⅱ类",
    },
    6: {
        "code": "MZT-A01",
        "reservoir_id": 6,
        "reservoir_name": "磨子潭水库",
        "water_grade": "Ⅱ类",
        "offline": True,
    },
    7: {
        "code": "LHK-A01",
        "reservoir_id": 7,
        "reservoir_name": "龙河口水库",
        "water_grade": "Ⅲ类",
    },
    8: {
        "code": "HLT-A01",
        "reservoir_id": 8,
        "reservoir_name": "花凉亭水库",
        "water_grade": "Ⅲ类",
    },
    9: {
        "code": "CCS-A01",
        "reservoir_id": 9,
        "reservoir_name": "陈村水库",
        "water_grade": "Ⅱ类",
    },
    10: {
        "code": "DPS-A01",
        "reservoir_id": 10,
        "reservoir_name": "董铺水库",
        "water_grade": "Ⅲ类",
    },
    11: {
        "code": "DFY-A01",
        "reservoir_id": 11,
        "reservoir_name": "大房郢水库",
        "water_grade": "Ⅲ类",
    },
    12: {
        "code": "HLS-A01",
        "reservoir_id": 12,
        "reservoir_name": "黄栗树水库",
        "water_grade": "Ⅱ类",
    },
}

# ========== 各水质等级指标正常范围 (min, max) ==========

GRADE_RANGES = {
    "Ⅱ类": {
        "pH": (6.8, 7.8),
        "DO": (6.2, 8.5),
        "CODMn": (1.5, 3.8),
        "COD": (8.0, 14.5),
        "NH3N": (0.05, 0.45),
        "TP": (0.010, 0.023),
        "TN": (0.10, 0.48),
        "TEMP": (20.0, 28.0),
    },
    "Ⅲ类": {
        "pH": (6.8, 7.8),
        "DO": (5.2, 7.5),
        "CODMn": (3.0, 5.8),
        "COD": (12.0, 19.5),
        "NH3N": (0.20, 0.95),
        "TP": (0.020, 0.048),
        "TN": (0.30, 0.98),
        "TEMP": (20.0, 28.0),
    },
}

# ========== 8 项核心指标元信息 ==========
# (code, name, unit, decimal_places)

INDICATOR_META = [
    ("pH", "pH值", "无量纲", 2),
    ("DO", "溶解氧", "mg/L", 3),
    ("CODMn", "高锰酸盐指数", "mg/L", 3),
    ("COD", "化学需氧量", "mg/L", 3),
    ("NH3N", "氨氮", "mg/L", 3),
    ("TP", "总磷", "mg/L", 3),
    ("TN", "总氮", "mg/L", 3),
    ("TEMP", "水温", "℃", 1),
]


def generate_rtu_indicators(water_grade: str):
    """根据水质等级生成 8 项核心指标的模拟值

    返回: list[(indicator_code, indicator_name, value, unit)]
    """
    ranges = GRADE_RANGES.get(water_grade, GRADE_RANGES["Ⅱ类"])
    result = []
    for code, name, unit, decimals in INDICATOR_META:
        range_min, range_max = ranges[code]
        value = round(random.uniform(range_min, range_max), decimals)
        result.append((code, name, value, unit))
    return result
