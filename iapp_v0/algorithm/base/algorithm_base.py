import json
import logging
import os
from abc import abstractmethod, ABCMeta
from types import CodeType
from typing import Any, Union, AnyStr

from iapp_v0.constant.alarm import AlarmRule, ExceedLimitAlarmRule
from iapp_v0.constant.constant import AlgorithmClassifyEnum, AlgorithmStrategyEnum, AlgorithmOutputTypeEnum
from iapp_v0.exceptions.custom_exception import AlgorithmCheckException, AlgorithmProcessException

"""
写在前面 UML类图请参考
https://www.processon.com/view/link/63d87ff3d2c3891f02fc7c95 访问密码：PB4F
"""

typing_map = {'string': str, 'number': float, 'point': tuple, 'double': float, 'audio': AnyStr,
              'square': tuple[tuple]}
"""
python类型和前端类型的映射
"""


class AlgorithmInput(dict):
    """
    算法输入
    :key 输入参数名
    :value 输入参数值
    """

    def __init__(self, json: dict = None, **kwargs):
        super(AlgorithmInput, self).__init__(kwargs=kwargs)

        self.update(json)


class AlgorithmOutput:
    """
    算法输出
    :ret 是否成功
    :val 识别结果值
    :points 关键点坐标
    :alarm (是否报警，报警等级，报警描述)
    """

    def __init__(self, ret: bool, val: Any, points: list[tuple], alarm: tuple, level: str, desc: str):
        self.ret = ret
        self.val = val
        self.points = points

        self.alarm = alarm
        self.level = level
        self.desc = desc

    def __str__(self):
        return f"ret: {self.ret}, val: {self.val}, points: {self.points}, \
        alarm: {self.alarm}, level: {self.level}, desc : {self.desc}"


class AlgorithmInstance(object):

    def __init__(self, classify: AlgorithmClassifyEnum, strategy: AlgorithmStrategyEnum,
                 output_type: AlgorithmOutputTypeEnum,
                 out_template: Union[str, bytes, CodeType] = None,
                 alarm_rule: AlarmRule = None):
        self.classify = classify
        self.strategy = strategy
        self.output_type = output_type
        self.output_template = out_template
        self.alarm_rule = alarm_rule


class Base(object):
    """
    # _id: int
    :_name: str
    :_description: str
    """
    __meta_class__ = ABCMeta

    def __init__(self, _id, name, description):
        self._id = _id
        self._name = name
        self._description = description

    def __getitem__(self, item):
        return self.__dict__.get(item, None)


class AlgorithmParam(Base):
    """
    算法参数
    :cn_name str
    # 值类型
    :val_type Type
    # 取值范围
    :val_range tuple[float]
    """

    def __init__(self, name, description, cn_name, val_type: type, val_range: tuple, nullable: bool = False,
                 _id: int = -1):
        super(AlgorithmParam, self).__init__(_id, name, description)

        # if not val_typing.__contains__(val_type):
        #     raise AlgorithmCheckException(f"Unsupported param type: {val_type}")

        self.cn_name = cn_name
        self.val_type = val_type
        self.val_range = val_range
        self.nullable = nullable


class AlgorithmStrategy(Base):
    """
    算法策略
    :cn_name: str
    # 策略对应的多个配置项及其值 AlgorithmParam
    :kv_param: dict
    """

    def __init__(self, owner: AlgorithmClassifyEnum, strategy: AlgorithmStrategyEnum, cn_name, description,
                 kv_param=None, _id: int = -1):
        super(AlgorithmStrategy, self).__init__(_id, str(strategy), description)

        self.cn_name = cn_name
        # 所属算法分类
        self.owner = owner
        self.kv_param = kv_param


class AlgorithmBase(Base):
    """
    算法 Base
    TODO 从概念上将 算法定义&算法实例&算法配置(输入输出) 区分开来
    TODO 其他 1. 参数预检查 (如入参是否在指定范围内 √
             2. 报警(越限）逻辑的实现  __alarm_trig √
             3. 算法输出根据类型变化适配  output_type √
    """
    # 实例相关
    # is_primary: bool = False
    _base_params: dict[str, AlgorithmParam] = {
        "classify": AlgorithmParam("classify", "算法分类", "算法分类", str, tuple(AlgorithmClassifyEnum.__members__)),
        "strategy": AlgorithmParam("strategy", "算法策略", "算法策略", str, tuple(AlgorithmStrategyEnum.__members__))}

    def __init__(self, name, description, cn_name, classify, strategies: list[AlgorithmStrategy],
                 params: dict[str, AlgorithmParam], _id: int = -1):
        super(AlgorithmBase, self).__init__(_id, name, description)

        self._instance = None
        self._inputs = None

        self.cn_name = cn_name
        # 支持的算法实例
        self.classify = classify
        # 支持的算法策略
        self.strategies = strategies
        # 支持的算法参数
        self.params = params

    def __param_check(self) -> (bool, str):
        """
        参数预检查
        return:
            :bool 是否通过
            :str 校验不通过的异常原因
        """

        # 少传参了
        for define in self._supported_params().values():
            all_inputs = [input_name for input_name in self._inputs.keys()]
            if not all_inputs.__contains__(define._name) and not define.nullable:
                return False, f"Missing param named '{define._name}' for {self._name}"

        for input_name in self._inputs.keys():
            if input_name == "kwargs":
                continue
            # 参数定义
            define = self._supported_params().get(input_name)
            value = self._inputs.get(input_name)
            #  1.检查参数是否已预定义
            if define is None:
                return False, f"Wrong param named '{input_name}' for {self._name}"
            # 2. 检查是否可以为空
            if define['nullable'] is False and value is None:
                return False, f"Value of '{input_name}' can't be {value}"
            # 3. 对应参数所传入的值是否在区间内
            valid_range = len(define.val_range) > 0
            if valid_range and not define.val_range.__contains__(value):
                return False, f"Value '{value}' of '{input_name}' not in range {define.val_range} for {self._name}"
        return True, ""

    def __output_format(self, detect_ret: tuple, alarm: tuple) -> (
        bool, Any, list[tuple], tuple):
        """
        对输出进行格式化,
            内置变量 质量位： STATUS
                   数值：  VALUE
                   报警等级： ALEVEL
        return:
            ret : 是否报警
            level: 报警等级
            desc: 报警描述
        """
        # 默认失败, 未报警, 无坐标点
        # detect_ret = False, None, ()
        # alarm = False, None, None
        STATUS, VALUE, points = detect_ret
        is_alarm, ALEVEL, desc = alarm

        # 如果识别失败或 输出类型非‘根据模板',则原样输出
        if not STATUS or self._instance.output_type != AlgorithmOutputTypeEnum.ByTemplate or self._instance.output_template is None:
            return *detect_ret, *alarm

        # if output_type == AlgorithmOutputTypeEnum.QualityOnly:
        #     return STATUS, None, points, *alarm
        # elif output_type == AlgorithmOutputTypeEnum.ValueQuality:
        #     return *detect_ret, *alarm
        # elif output_type == AlgorithmOutputTypeEnum.AlarmLevel:
        #     return STATUS, VALUE, points,
        #  TODO 此处没有对output_type 进行分类处理, 主要考虑
        #       1. 当前返回值中 检测结果和报警信息 都已具备，没必要再细分
        #       2. 返回值 在后续使用时再根据 output_type 细分处理即可

        format_val = eval(self._instance.output_template)
        return STATUS, format_val, points, is_alarm, ALEVEL, desc

    def __alarm_trig(self, detect_ret) -> (bool, str, str):
        """
        根据报警规则触发报警
        return:
            ret : 是否报警
            level: 报警等级
            desc: 报警描述
        """
        status, val, points = detect_ret
        ret, level, desc = False, None, None
        rule = self._instance.alarm_rule
        if isinstance(rule, ExceedLimitAlarmRule):
            if val >= rule.hh_limit:
                ret, level, desc = True, "HH", "越高高限报警" if rule.hh_txt is None else rule.hh_txt
            elif val >= rule.h_limit:
                ret, level, desc = True, "H", "越高限报警" if rule.h_txt is None else rule.h_txt
            elif val <= rule.l_limit:
                ret, level, desc = True, "L", "越低限报警" if rule.l_txt is None else rule.l_txt
            elif val <= rule.ll_limit:
                ret, level, desc = True, "LL", "越低低限报警" if rule.ll_txt is None else rule.ll_txt
        return ret, level, desc

    def _get_strategy_by_name(self, name: str):
        """
        根据策略名获取具体策略对象
        """
        ls = [s for s in self._supported_strategy() if s._name == name]
        if len(ls) != 1:
            raise AlgorithmProcessException(f"Unsupported strategy :{name}")
        return ls[0]

    def _get_input_value_by_name(self, param_name: str):
        """
        根据参数名获取具体 参数值
        """
        param_dict = {**self._supported_params(), **self._base_params}
        lp = [self._inputs.get(pname) for pname in param_dict.keys() if pname == param_name]
        if len(lp) != 1:
            raise AlgorithmProcessException(f"Unsupported param : {param_name}")
        return lp[0]

    def _supported_classify(self):
        return self.classify

    def _supported_strategy(self):
        return self.strategies

    def _supported_params(self):
        return self.params

    @abstractmethod
    def _preprocess(self) -> Any:
        """
        图像预处理，比如 灰度、二值化、膨胀、腐蚀 等, 预处理结果内部保存
        """
        pass

    @abstractmethod
    def _do_detect(self, classify: AlgorithmClassifyEnum, strategy: AlgorithmStrategyEnum) -> (bool, Any, tuple):
        """
        核心检测算法
        return:
            ret: 检测是否成功
            val: 数值化结果(如果有,若没有留空)
            points: 检测到的关键结果点集(具体每个点含义由各算法自行约定)
        """
        pass

    @abstractmethod
    def _postprocess(self) -> Any:
        """
        后置处理： 可选, 比如结果展示等
        """
        pass

    @abstractmethod
    def gen_result_img(self) -> None:
        """
        生成绘制结果图像
        """
        pass

    def perform(self, instance: AlgorithmInstance) -> (
        bool, Any, list[tuple], tuple):
        """
        算法调用主入口
        Usage:
            AlgorithmBase ab = LiquidLevelReco(xxx)
            ret,val,points,*alarm = ab.perform(**)
            ...
        return:
            ret: bool 是否识别成功
            val: Any 核心识别结果
            points: list[tuple] 可选项,关键识别结果点的坐标列表
            alarming: tuple 是否报警,报警等级,报警描述
        """
        # lock.acquire()
        self._instance = instance
        # lock.release()

        b, msg = self.__param_check()
        if not b:
            raise AlgorithmCheckException(f"Param check exception: {msg}")
        # 默认失败, 无值, 无坐标点
        detect_ret = False, None, ()
        alarm = False, None, None
        try:
            logging.debug(f"{self.cn_name}_{self._id} start to preprocessing image... ")
            self._preprocess()

            logging.debug(f"{self.cn_name}_{self._id} start to do_detect... ")
            detect_ret = self._do_detect(self._instance.classify, self._instance.strategy)
        except AlgorithmProcessException as e:
            logging.error(f"pre AlgorithmProcessException {e}")

        detect_success = detect_ret[0]
        # 是否需要检测报警
        is_trig_alarm = self._instance.output_type == AlgorithmOutputTypeEnum.AlarmLevel or self._instance.output_type == AlgorithmOutputTypeEnum.ByTemplate
        if detect_success and is_trig_alarm and self._instance.alarm_rule is not None:
            logging.debug(f"{self.cn_name}_{self._id} start to trig alarm ... ")
            alarm = self.__alarm_trig(detect_ret)

        try:
            logging.debug(f"{self.cn_name}_{self._id} start to postprocess ...")
            self._postprocess()
        except AlgorithmProcessException as e:
            logging.error(f"post AlgorithmProcessException {e}")

        logging.info(f"{self.cn_name}_{self._id} perform success ")
        return self.__output_format(detect_ret, alarm)

    @staticmethod
    def json_schema_2_algorithm_params(file_abspath: AnyStr):
        abspath = os.path.abspath(file_abspath)

        with open(abspath, encoding='utf-8', errors='ignore') as f:
            schema = json.load(f)
        assert schema['inputParam'] is not None

        def __c2param(key: dict) -> AlgorithmParam:
            assert schema['inputParam'][key] is not None

            description = schema['inputParam'][key].get('des')
            cn_name = schema['inputParam'][key].get('name')
            # 默认为 string 类型
            raw_type = schema['inputParam'][key].get('type', 'string')
            val_type = typing_map[raw_type]

            val_range = schema['inputParam'][key].get('val_range', ())
            # nullable 默认为 False
            nullable = schema['inputParam'][key].get('nullable', False)
            _id = schema['inputParam'][key].get('id', True)

            return AlgorithmParam(key, description, cn_name, val_type, val_range, nullable, _id)

        return {key: __c2param(key) for key in schema['inputParam'].keys()}
