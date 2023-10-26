from dataclasses    import dataclass
from typing         import List
from numpy          import inf

@dataclass
class HMR_DUTDimensions():
    l: float # mm
    w: float # mm

    def __init__(self, l:float = None, w:float = None) -> None:
        self.l = l
        self.w = w

@dataclass
class HMR_Margins():
    interior: float # spacing between active area edge and the inner pattern line in mm
    exterior: float

    def __init__(self, interior:float = None, exterior:float = None) -> None:
        self.interior = interior
        self.exterior = exterior

@dataclass
class HMR_Errors():
    skew: float
    rotation: float

    def __init__(self, skew:float = None, rotation:float = None) -> None:
        self.skew = skew
        self.rotation = rotation

@dataclass
class HMR_Thresholds():
    filter: float   # path size threshold
    midline: float  # how many pixels is considered possible accuracy error

    def __init__(self, filter:float = None, midline:float = None) -> None:
        self.filter = filter
        self.midline = midline

@dataclass
class HMR_CalibrationPoint():
    x: float
    y: float

    def __init__(self, x:float = None, y: float = None) -> None:
        self.x = x
        self.y = y

@dataclass
class HMR_CalibrationPath():
    path: List[HMR_CalibrationPoint]
    isHorizontal: bool | None
    isSizeEnough: bool | None
    xmin: float
    xmax: float
    xmean: float
    ymin: float
    ymax: float
    ymean: float

    def __init__(self) -> None:
        self.path = []
        self.isHorizontal = None
        self.isSizeEnough = None
        self.xmin = inf
        self.xmax = -inf
        self.xmean = 0
        self.ymin = inf
        self.ymax = -inf
        self.ymean = 0

    def getProperties(self) -> None:
        self.xmin = inf
        self.xmax = -inf
        self.xmean = 0
        self.ymin = inf
        self.ymax = -inf
        self.ymean = 0

        for pt in self.path:
            self.xmin = min(self.xmin, pt.x)
            self.xmax = max(self.xmax, pt.x)
            self.ymin = min(self.ymin, pt.y)
            self.ymax = max(self.ymax, pt.y)
            self.xmean += pt.x
            self.ymean += pt.y

        self.xmean /= len(self.path)
        self.ymean /= len(self.path)

@dataclass
class HMR_CalibrationCase():
    case: List[HMR_CalibrationPath]
    largestHorizontalPathSize: int
    largestVerticalPathSize: int
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    def __init__(self) -> None:
        self.case = []
        self.largestHorizontalPathSize = None
        self.largestVerticalPathSize = None
        self.xmin = inf
        self.xmax = -inf
        self.ymin = inf
        self.ymax = -inf

    def getRange(self) -> None:
        self.xmin = inf
        self.xmax = -inf
        self.ymin = inf
        self.ymax = -inf
        for calPath in self.case:
            self.xmin = min(self.xmin, calPath.xmin)
            self.xmax = max(self.xmax, calPath.xmax)
            self.ymin = min(self.ymin, calPath.ymin)
            self.ymax = max(self.ymax, calPath.ymax)

    def calLongestpath(self, midlineThreshold:float) -> None:
        self.largestHorizontalPathSize = 0
        self.largestVerticalPathSize = 0
        for calPath in self.case:
            if (calPath.ymax - calPath.ymin < midlineThreshold and 
                len(calPath.path) > self.largestHorizontalPathSize):
                self.largestHorizontalPathSize = len(calPath.path)

            if (calPath.xmax - calPath.xmin < midlineThreshold and
                len(calPath.path) > self.largestVerticalPathSize):
                self.largestVerticalPathSize = len(calPath.path)

@dataclass
class HMR_EVTestData():
    raw_xmax:float
    raw_ymax:float

    segmented:HMR_CalibrationCase
    segmented_derotated:HMR_CalibrationCase
    segmented_derotated_deskewed:HMR_CalibrationCase
    segmented_calibrated:HMR_CalibrationCase

    def __init__(self) -> None:
        self.raw_xmax = -inf
        self.raw_ymax = -inf

        self.segmented = HMR_CalibrationCase()
        self.segmented_derotated = HMR_CalibrationCase()
        self.segmented_derotated_deskewed = HMR_CalibrationCase()
        self.segmented_calibrated = HMR_CalibrationCase()
