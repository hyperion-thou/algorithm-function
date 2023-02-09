from enum import Enum

import numpy as np

# 红色区间1
# https://blog.csdn.net/wanggsx918/article/details/23272669
LOWER_RED1 = np.array([0, 43, 46])
UPPER_RED1 = np.array([10, 255, 255])
# 红色区间2
LOWER_RED2 = np.array([156, 43, 46])
UPPER_RED2 = np.array([180, 255, 255])
# 绿色区间
LOWER_GREEN = np.array([35, 43, 46])
UPPER_GREEN = np.array([77, 255, 255])
# 蓝色区间
LOWER_BLUE = np.array([100, 43, 46])
UPPER_BLUE = np.array([124, 255, 255])
# 橙黄色区间  11-25|26-34
LOWER_YELLOW = np.array([11, 43, 46])
UPPER_YELLOW = np.array([34, 255, 255])
# 青色
LOWER_CYAN = np.array([78, 43, 46])
UPPER_CYAN = np.array([99, 255, 255])
# 紫色
LOWER_PURPLE = np.array([125, 43, 46])
UPPER_PURPLE = np.array([155, 255, 255])


class ColorSeriesEnum(Enum):
    Red = 0
    Green = 1
    Blue = 2
    Yellow = 3
    Cyan = 4
    Purple = 5

    @classmethod
    def from_str(cls, txt):
        assert txt is not None
        for k, v in cls.__members__.items():
            if k.casefold() == txt.casefold():
                return v
        else:
            raise ValueError(f"'{cls.__name__}' enum not found for '{txt}'")

    @classmethod
    def value_of(cls, value):
        assert value is not None
        for k, v in cls.__members__.items():
            if v.value == value:
                return v
        else:
            raise ValueError(f"'{cls.__name__}' enum not found for '{value}'")


class AlgorithmOutputTypeEnum(Enum):
    # 仅质量位
    QualityOnly = 0
    # 值+质量位 ->  质量位 好0，坏1
    ValueQuality = 1
    # 报警等级 :  1->高高，低低 2->高，低
    AlarmLevel = 2
    # 根据模板:
    ByTemplate = 3

    @classmethod
    def from_str(cls, txt):
        for k, v in cls.__members__.items():
            if k.casefold() == txt.casefold():
                return v
        else:
            raise ValueError(f"'{cls.__name__}' enum not found for '{txt}'")

    @classmethod
    def value_of(cls, value):
        for k, v in cls.__members__.items():
            if v.value == value:
                return v
        else:
            raise ValueError(f"'{cls.__name__}' enum not found for '{value}'")


class AlgorithmClassifyEnum(Enum):
    # 主
    Primary = (0, "primary")
    # 次(质量)
    Secondary = (1, "secondary")

    @classmethod
    def from_str(cls, txt):
        for k, v in cls.__members__.items():
            if k.casefold() == txt.casefold():
                return v
        else:
            raise ValueError(f"'{cls.__name__}' enum not found for '{txt}'")

    @classmethod
    def value_of(cls, value):
        for k, v in cls.__members__.items():
            if v.value[0] == value:
                return v
        else:
            raise ValueError(f"'{cls.__name__}' enum not found for '{value}'")


class AlgorithmStrategyEnum(Enum):
    """
    算法策略等级枚举
    """
    # 主策略
    Main = (0, "main"),
    Second = (1, "second")
    Third = (2, "third"),
    Fourth = (3, "fourth")
    Fifth = (4, "fifth")

    @classmethod
    def from_str(cls, txt):
        for k, v in cls.__members__.items():
            if k.casefold() == txt.casefold():
                return v
        else:
            raise ValueError(f"'{cls.__name__}' enum not found for '{txt}'")

    @classmethod
    def value_of(cls, value):
        for k, v in cls.__members__.items():
            if v.value[0] == value:
                return v
        else:
            raise ValueError(f"'{cls.__name__}' enum not found for '{value}'")
