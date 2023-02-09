#!/usr/bin/env python

"""Tests for `iapp_v0` package."""
import importlib
import os

import cv2
import pytest

from iapp_v0.algorithm.base.algorithm_base import AlgorithmOutput, AlgorithmBase, AlgorithmInstance, AlgorithmInput
from iapp_v0.constant.alarm import ExceedLimitAlarmRule, AlarmRule
from iapp_v0.constant.constant import AlgorithmClassifyEnum, AlgorithmStrategyEnum, AlgorithmOutputTypeEnum
from iapp_v0.exceptions.custom_exception import AlgorithmProcessException

clazz_name_prefix = "LiquidLevelReco"


def do(classify, strategy, output_type, out_template: str = "", alarm_rule: AlarmRule = None):
    instance = AlgorithmInstance(classify, strategy, output_type, out_template=out_template, alarm_rule=alarm_rule)

    inputs = AlgorithmInput({"imgPath": "E:/workspace/PycharmProjects/iapp/iapp_v0/tests/resources/input/ywj010.jpg",
                             "colorSeries": "Red",
                             "rangeUp": 50, "rangeDown": -30,
                             "thresholdUpper": [335, 157], "thresholdLower": [335, 217],
                             "column": [[325, 116], [337, 310], [346, 310], [331, 115]],
                             "outputType": "ValueQuality"})

    liquid_reco: AlgorithmBase
    if instance.classify == AlgorithmClassifyEnum.Primary:
        module_primary = importlib.import_module(".liquid_level.ab_liquid_level_reco_primary",
                                                 package="iapp_v0.algorithm")
        clazz_ = getattr(module_primary, f"{clazz_name_prefix}{AlgorithmClassifyEnum.Primary.name}")
        liquid_reco: AlgorithmBase = clazz_(inputs, 1)
    elif instance.classify == AlgorithmClassifyEnum.Secondary:
        module_secondary = importlib.import_module(".liquid_level.ab_liquid_level_reco_secondary",
                                                   package="iapp_v0.algorithm")
        clazz_ = getattr(module_secondary, f"{clazz_name_prefix}{AlgorithmClassifyEnum.Secondary.name}")
        liquid_reco: AlgorithmBase = clazz_(inputs, 0)
    else:
        raise AlgorithmProcessException(f"Unsupported algorithm classify: {instance.classify}")

    assert liquid_reco is not None
    ret, val, points, alarm, level, desc = liquid_reco.perform(instance)
    print(f"结果 {ret, val, points, alarm, level, desc}")

    outputs = AlgorithmOutput(ret, val, points, alarm, level, desc)
    print(f"outputs {str(outputs)}")

    # 可选操作
    ret_img = liquid_reco.gen_result_img()
    if ret_img is not None:
        cv2.imwrite(os.getcwd() + "/40_result.jpg", ret_img)

    return outputs


@pytest.fixture
def primary_detect():
    classify = AlgorithmClassifyEnum.Primary
    strategy = AlgorithmStrategyEnum.Main
    output_type = AlgorithmOutputTypeEnum.AlarmLevel

    # 报警条件（可选）
    alarm_rule = ExceedLimitAlarmRule(47, 17, -1, -15)
    return do(classify, strategy, output_type, alarm_rule=alarm_rule)


@pytest.fixture
def second_detect():
    classify = AlgorithmClassifyEnum.Secondary
    strategy = AlgorithmStrategyEnum.Main
    output_type = AlgorithmOutputTypeEnum.AlarmLevel

    # 报警条件（可选）
    alarm_rule = ExceedLimitAlarmRule(47, 17, -1, -15)

    return do(classify, strategy, output_type, alarm_rule=alarm_rule)


def test_primary(primary_detect):
    assert primary_detect.ret is True


def test_second(second_detect):
    assert second_detect.alarm is True


# @pytest.fixture
# def json2_param():
#     filename = "E:\\workspace\\PycharmProjects\\iapp\\iapp_v0\\iapp_v0\\algorithm\\liquid_level\\schema.json"
#     return AlgorithmBase.json_schema_2_algorithm_params(filename)
#
#
# def test_json_reader(json2_param):
#     assert len(json2_param) > 0
