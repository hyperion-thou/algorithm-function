import logging
import os
from abc import abstractmethod
from typing import Any

import cv2

from iapp_v0.algorithm.base.algorithm_base import AlgorithmInput, AlgorithmBase, AlgorithmParam, AlgorithmStrategy
from iapp_v0.constant.constant import *
from iapp_v0.exceptions.custom_exception import AlgorithmProcessException
from iapp_v0.utils.utils import RectUtils

# 是否输出中间过程图片
WRITE_PROCESS_IMAGE = True
# 是否show中间过程图片
SHOW_PROCESS_IMAGE = False
# 透视变化阈值角度
# theta = 15
# THRESHOLD = math.tan(theta * math.pi / 180)
# 最小量程精度百分比
MIN_PRECISION_PERCENT = 0.1


class LiquidLevelReco(AlgorithmBase):
    """
    液位识别
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema_.json")

    _name = "LiquidLevelReco.Base.v1"
    _description = "识别算法.基础.版本v1"
    _cn_name = "液位识别算法"

    # 支持的算法分类个数
    __supported_classify = (AlgorithmClassifyEnum.Primary, AlgorithmClassifyEnum.Secondary)
    # 支持的算法策略，primary -> main & secondary -> main
    __supported_strategies = [
        AlgorithmStrategy(__supported_classify[0], AlgorithmStrategyEnum.Main, "液位主识别策略",
                          "基于颜色的液位识别主策略", kv_param={}),
        AlgorithmStrategy(__supported_classify[1], AlgorithmStrategyEnum.Main, "液位主识别策略",
                          "基于轮廓的液位识别主策略", kv_param={})
    ]

    # 支持的算法参数，若干
    __supported_params = AlgorithmBase.json_schema_2_algorithm_params(schema_path)

    def __init__(self, _inputs: AlgorithmInput, _id: int = -1):
        super(LiquidLevelReco, self).__init__(self.__class__._name, self.__class__._description,
                                              self.__class__._cn_name, self.__class__.__supported_classify,
                                              self.__class__.__supported_strategies, self.__class__.__supported_params)
        self._inputs = _inputs
        # 算法实例参数
        self._instance = None
        self._processFinalArea = None
        self._processFinalNum = None

        self._originImg = cv2.imread(self._get_input_value_by_name("imgPath"))
        self._thresholdUpper = self._get_input_value_by_name("thresholdUpper")
        self._thresholdLower = self._get_input_value_by_name("thresholdLower")
        self._rangeUp = self._get_input_value_by_name("rangeUp")
        self._rangeDown = self._get_input_value_by_name("rangeDown")

        self._columnLeftTop = self._get_input_value_by_name("column")[0]
        self._columnLeftBottom = self._get_input_value_by_name("column")[1]
        self._columnRightBottom = self._get_input_value_by_name("column")[2]
        self._columnRightTop = self._get_input_value_by_name("column")[3]

        self._processOutputDir = os.getcwd()  # TODO

    def _temp_show_contour(self, contour, area=None):
        temp = self._processCutTarget.copy()
        if area is not None:
            print("__area,", area)

        cv2.drawContours(temp, contour, -1, (0, 255, 255), 3)
        cv2.imshow("__process_img", temp)
        cv2.waitKey()

    def _img_cut(self):
        """
        图像预处理,根据给定坐标直接切图
        """
        img = cv2.GaussianBlur(self._originImg, (3, 3), 0)

        box = [self._columnLeftTop, self._columnLeftBottom, self._columnRightBottom, self._columnRightTop]
        if WRITE_PROCESS_IMAGE:
            cv2.imwrite(self._processOutputDir + "/11_origin.jpg", self._originImg)

        # self.mask = np.zeros(img.shape, dtype=np.uint8)
        # roi_corners = np.array([points], dtype=np.int32)
        # # # 创建mask层
        # cv2.fillPoly(self.mask, roi_corners, (255, 255, 255))
        # # # 为每个像素进行or操作，除mask区域外，全为0
        # self._processCutTarget = cv2.bitwise_and(img, self.mask)
        # 白
        mask = np.ones(img.shape, dtype="uint8") * 255
        roi_corners = np.array([box], dtype=np.int32)
        # 黑
        cv2.fillPoly(mask, roi_corners, (0, 0, 0))
        self._processCutTarget = cv2.bitwise_or(self._originImg, mask)

        if WRITE_PROCESS_IMAGE:
            cv2.imwrite(self._processOutputDir + "/11_origin.jpg", self._originImg)
            cv2.imwrite(self._processOutputDir + "/12_matchRet.jpg", self._processCutTarget)

    def _img_threshold(self):
        """
        图像二值化
        :return:
        """
        gray = cv2.cvtColor(self._processCutTarget, cv2.COLOR_BGR2GRAY)
        # gray = cv2.bitwise_not(gray)
        H = int((self._columnRightBottom[1] - self._columnRightTop[1]) * 0.01) + 1
        H1 = H * 2 + 1
        kernel = np.ones((H, 1), np.uint8)
        dilate = cv2.dilate(gray, kernel, iterations=5)
        erode = cv2.erode(dilate, kernel, iterations=3)
        if WRITE_PROCESS_IMAGE:
            cv2.imwrite(self._processOutputDir + "/21_gray.jpg", erode)
        thre = cv2.adaptiveThreshold(erode, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, H1, 2)
        # reval_T, thre = cv2.threshold(erode, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        kernel = np.ones((H, 1), np.uint8)
        dilate2 = cv2.dilate(thre, kernel, iterations=3)
        self._processBinaryTarget = cv2.erode(dilate2, kernel, iterations=1)
        if WRITE_PROCESS_IMAGE:
            cv2.imwrite(self._processOutputDir + "/22_binary.jpg", self._processBinaryTarget)

    def _img_threshold_by_color(self, color=ColorSeriesEnum.Red):
        """
        图像二值化
        :return:
        """
        H = int((self._columnRightBottom[1] - self._columnRightTop[1]) * 0.01)
        # # H1 = H * 2 + 1`
        kernel = np.ones((H, 1), np.uint8)
        dilate = cv2.dilate(self._processCutTarget, kernel, iterations=3)
        erode = cv2.erode(dilate, kernel, iterations=3)
        # closing = cv2.morphologyEx(self._processCutTarget, cv2.MORPH_CLOSE, kernel, iterations=30)

        if WRITE_PROCESS_IMAGE:
            cv2.imwrite(self._processOutputDir + "/21_gray.jpg", erode)
        # 将图像转化为HSV格式，便于颜色提取
        img_hsv = cv2.cvtColor(erode, cv2.COLOR_BGR2HSV)
        # 去除红颜色范围外的其余颜色
        if color == ColorSeriesEnum.Red:
            mask0 = cv2.inRange(img_hsv, LOWER_RED1, UPPER_RED1)
            mask1 = cv2.inRange(img_hsv, LOWER_RED2, UPPER_RED2)
            mask = mask0 + mask1
        elif color == ColorSeriesEnum.Green:
            mask = cv2.inRange(img_hsv, LOWER_GREEN, UPPER_GREEN)
        elif color == ColorSeriesEnum.Blue:
            mask = cv2.inRange(img_hsv, LOWER_BLUE, UPPER_BLUE)
        elif color == ColorSeriesEnum.Yellow:
            mask = cv2.inRange(img_hsv, LOWER_YELLOW, UPPER_YELLOW)
        elif color == ColorSeriesEnum.Cyan:
            mask = cv2.inRange(img_hsv, LOWER_CYAN, UPPER_CYAN)
        elif color == ColorSeriesEnum.Purple:
            mask = cv2.inRange(img_hsv, LOWER_PURPLE, UPPER_PURPLE)
        else:
            raise AlgorithmProcessException('Unknown ColorSeriesEnum.')

        reval_t, thre = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        # kernel = np.ones((H, 1), np.uint8)
        dilate2 = cv2.dilate(thre, kernel, iterations=3)
        self._processBinaryTarget = cv2.erode(dilate2, kernel, iterations=3)
        # self._processBinaryTarget = dilate2
        if WRITE_PROCESS_IMAGE:
            cv2.imwrite(self._processOutputDir + "/22_threshold.jpg", self._processBinaryTarget)

    def _img_contours(self):
        """
        图像边界
        :return:
        """
        contours, hierarchy = cv2.findContours(self._processBinaryTarget, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        min_area, min_contour = None, None
        full_area = RectUtils.rect_area(self._columnLeftTop, self._columnRightBottom)
        print("full_area, ", full_area)
        for cnt in contours:
            # 最小矩形框
            rect = cv2.minAreaRect(cnt)
            center, (w, h), c = rect
            area = RectUtils.rect_area2(w, h)
            if SHOW_PROCESS_IMAGE:
                self._temp_show_contour(cnt, area)

            # rect面积大于整个图形面积的10%(防止面积过小的燥点) and  rect中心应当低于整个检测区域中心
            if full_area * MIN_PRECISION_PERCENT < area and center[1] >= (
                (self._columnRightBottom[1] - self._columnLeftTop[1]) / 2 + self._columnRightTop[1]):
                # 首次 or 面积最小
                if min_area is None or area < min_area:
                    min_area, min_contour = area, cnt
        if min_contour is not None:
            self._processFinalArea = min_contour
            print("target_area,", min_area)
            if SHOW_PROCESS_IMAGE:
                self._temp_show_contour(min_contour, min_area)
        else:
            raise AlgorithmProcessException('没有检测到符合条件的轮廓区域')

    def _calc_numerical(self):
        """按液柱占全柱比例计算读数"""
        full_range = abs(self._rangeDown - self._rangeUp)
        ch = self._columnRightBottom[1] - self._processFinalLiquid[1]
        h = self._columnRightBottom[1] - self._columnRightTop[1]

        self._processFinalNum = ch / h * full_range + self._rangeDown

    @abstractmethod
    def _preprocess(self) -> Any:
        """
        本算法的预处理由不同分类不同策略重写
        """
        pass

    def _do_detect(self, _classify: AlgorithmClassifyEnum, _strategy: AlgorithmStrategyEnum) -> (bool, Any, tuple):
        """
        核心检测算法
        return:
            ret: 检测是否成功
            val: 数值化结果(如果有,若没有留空)
            points: 检测到的关键结果点集(具体每个点含义由各算法自行约定)

        """
        min_w, min_h = None, None
        # ret, val, points = False, None, None
        for contour in self._processFinalArea:
            #  寻找最高点
            if min_h is None or contour[0][1] < min_h:
                min_w, min_h = contour[0]

        self._processFinalLiquid = (min_w, min_h)
        try:
            self._calc_numerical()
        except Exception as e:
            logging.error(f"检测异常 {e}")
            return False, None, None

        return True, self._processFinalNum, (self._processFinalLiquid,)

    @abstractmethod
    def _postprocess(self) -> Any:
        """
        本算法的预处理由不同分类不同策略重写
        """
        pass

    def gen_result_img(self) -> None:
        if self._processFinalNum is None or self._processFinalArea is None:
            return

        temp = self._originImg.copy()
        p_color, t_color, a_color = (0, 0, 255), (60, 255, 0), (0, 255, 255)

        # self._resultImg = cv2.drawContours(temp, self.min_area, -1, (0, 255, 255), 1)
        box = cv2.boxPoints(cv2.minAreaRect(self._processFinalArea))
        cv2.fillPoly(temp, np.array([box], dtype=np.int32), a_color)

        cv2.circle(temp, self._thresholdUpper, 2, p_color, thickness=-1)
        cv2.putText(temp, "upper", self._thresholdUpper, cv2.FONT_HERSHEY_PLAIN, 1.0, t_color, thickness=1)

        # cv2.circle(temp, self._processFinalLiquid, 2, p_color, thickness=-1)
        # cv2.putText(temp, "liquid", self._processFinalLiquid, cv2.FONT_HERSHEY_PLAIN, 1.0, t_color, thickness=1)
        cv2.putText(temp, "{:.1f}".format(self._processFinalNum), self._processFinalLiquid,
                    cv2.FONT_HERSHEY_PLAIN, 1.0,
                    t_color, thickness=2)

        cv2.circle(temp, self._thresholdLower, 2, p_color, thickness=-1)
        return cv2.putText(temp, "lower", self._thresholdLower, cv2.FONT_HERSHEY_PLAIN, 1.0, t_color, thickness=1)
