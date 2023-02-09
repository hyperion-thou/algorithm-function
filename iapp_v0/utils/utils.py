import json
import os
from typing import AnyStr

import cv2

from iapp_v0.algorithm.base.algorithm_base import AlgorithmParam


class RectUtils:
    """
    矩形相关 工具类
    """

    @staticmethod
    def rect_contains(rect, pt, *args):
        # a < x < a + c and b < y < b + d
        # （中心点坐标，（宽度，高度）,旋转的角度
        rectCent, (w, h), c = rect
        # 最小矩形框的四个点坐标（左下，左上，右下，右上）
        _, lt, rb, _ = cv2.boxPoints(rect)

        first, others = lt[0] < pt[0] < rb[0] and lt[0] < pt[1] < rb[1], True
        for o_pt in args:
            other = lt[0] < o_pt[0] < rb[0] and lt[0] < o_pt[1] < rb[1]
            if not other:
                others = False
                break
        return first and others

    @staticmethod
    def rect_area(lt, rb):
        # w * h
        return abs(lt[0] - rb[0]) * abs(lt[1] - rb[1])

    @staticmethod
    def rect_area2(w, h):
        # w * h
        return abs(w * h)




