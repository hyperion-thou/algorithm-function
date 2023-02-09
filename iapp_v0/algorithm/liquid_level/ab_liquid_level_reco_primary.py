from typing import final, Any

from iapp_v0.algorithm.base.algorithm_base import AlgorithmInput
from iapp_v0.algorithm.liquid_level.ab_liquid_level_reco import LiquidLevelReco
from iapp_v0.constant.constant import *
from iapp_v0.exceptions.custom_exception import AlgorithmProcessException


@final
class LiquidLevelRecoPrimary(LiquidLevelReco):
    """
    液位识别
    """

    _name = "LiquidLevelReco.primary.v1"
    _description = "识别算法.主模型.版本v1"
    _cn_name = "液位识别算法(主模型)"

    def __init__(self, _inputs: AlgorithmInput, _id: int = -1):
        super(LiquidLevelRecoPrimary, self).__init__(_inputs, _id)

    def _preprocess(self):
        if self._originImg is None:
            raise AlgorithmProcessException("__originImg can not be None，please check file path/integrity")
        # 切图
        self._img_cut()
        # 二值化-根据颜色
        color_series = self._get_input_value_by_name("colorSeries")
        self._img_threshold_by_color(ColorSeriesEnum.from_str(color_series))
        # 液柱轮廓
        self._img_contours()

    def _postprocess(self) -> Any:
        pass
