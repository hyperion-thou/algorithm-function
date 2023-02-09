from enum import Enum


class RuleType(Enum):
    ExceedLimit = 0
    Deviation = 1
    ChangeRate = 2

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


class AlarmRule:
    """
    报警规则
    """

    def __init__(self, rule_type: RuleType, name):
        self.type = rule_type
        self.name = name


class ExceedLimitAlarmRule(AlarmRule):
    """
    越限报警规则
    """

    def __init__(self, hh_limit, h_limit, l_limit, ll_limit, hh_txt: str = "越高高限报警", h_txt: str = "越高限报警",
                 l_txt: str = "越低限报警", ll_txt: str = "越低低限报警"):
        super(ExceedLimitAlarmRule, self).__init__(RuleType.ExceedLimit, "越限报警")
        self.hh_limit = hh_limit
        self.h_limit = h_limit
        self.l_limit = l_limit
        self.ll_limit = ll_limit
        self.hh_txt = hh_txt
        self.h_txt = h_txt
        self.l_txt = l_txt
        self.ll_txt = ll_txt


class DeviationAlarmRule(AlarmRule):

    def __init__(self):
        super(DeviationAlarmRule, self).__init__(RuleType.Deviation, "偏差报警")
    # TODO


class ChangeRateAlarmRule(AlarmRule):

    def __init__(self):
        super(ChangeRateAlarmRule, self).__init__(RuleType.ChangeRate, "变化率报警")
    # TODO
