from HMR_calibration_data           import *
from typing                         import Tuple, List
from copy                           import deepcopy
from numpy                          import rad2deg, cos, sin, arctan2
from numpy.polynomial.polynomial    import Polynomial


PATH_SIZE_THRESHOLD = 0.2
class HMR_ErrorAnalyzer():
    def __init__(self, data:HMR_EVTestData, threshold:HMR_Thresholds) -> None:
        self.thresholds = threshold
        self.data = data
        self.errs = HMR_Errors()

    def derotate(self, pt:HMR_CalibrationPoint) -> HMR_CalibrationPoint:
        theta = self.errs.rotation
        x = pt.x*cos(theta) - pt.y*sin(theta)
        y = pt.x*sin(theta) + pt.y*cos(theta)
        return HMR_CalibrationPoint(x, y)

    def deskew(self, pt:HMR_CalibrationPoint) -> HMR_CalibrationPoint:
        x = pt.x - self.errs.skew*pt.y/self.data.raw_ymax
        y = pt.y
        return HMR_CalibrationPoint(x, y)

    def addRotation(self, slope:float):
        if self.errs.rotation is None:
            self.errs.rotation = 0
        self.errs.rotation += arctan2(slope, 1.0)

    def findRotationErrorFromMidline(self) -> None:
        # There should be only one middle horizontal line and vertical line
        X = []
        Y = []
        for calPath in self.data.segmented.case:
            if (calPath.ymax - calPath.ymin < self.thresholds.midline and
                len(calPath.path) > self.data.segmented.largestHorizontalPathSize*PATH_SIZE_THRESHOLD and
                abs(self.data.raw_ymax/2 - calPath.ymean) < self.thresholds.midline):
                print('Found the horizontal midline!')
                x, y = HMR_ErrorAnalyzer.getPathArray(calPath)
                X += x
                Y += y

            elif (calPath.xmax - calPath.xmin < self.thresholds.midline and
                  len(calPath.path) > self.data.segmented.largestVerticalPathSize*PATH_SIZE_THRESHOLD and
                  abs(self.data.raw_xmax/2 - calPath.xmean) < self.thresholds.midline):
                print('Found the vertical midline!')

        slope = HMR_ErrorAnalyzer.getSlope(X, Y)
        if slope is not None:
            self.errs.rotation = arctan2(slope, 1)
            self.applyDerotation()
        else:
            print('Error in finding the rotation value')

    def applyDerotation(self) -> None:
        self.data.segmented_derotated = deepcopy(self.data.segmented)
        self.errs.rotation *= -1
        print(f'Rotational error = {rad2deg(self.errs.rotation)}deg')
        print('Rotation detected and calculated. Applying derotation...')

        for (i, calPath) in enumerate(self.data.segmented.case):
            for (j, pt) in enumerate(calPath.path):
                self.data.segmented_derotated.case[i].path[j] = self.derotate(pt)
            self.data.segmented_derotated.case[i].getProperties()
        self.data.segmented_derotated.getRange()

        print('Derotation applied succesfully.\n')

    def findSkewError(self) -> None:
        if self.data.segmented_derotated.xmax == self.data.raw_xmax and self.data.segmented_derotated.xmin == 0:
            print('There is no skew.')
            self.errs.skew = 0.0

        elif self.data.segmented_derotated.xmax > self.data.raw_xmax:
            print('Data is skewed to the right.')
            self.errs.skew = self.data.segmented_derotated.xmax - self.data.raw_xmax

        elif self.data.segmented_derotated.xmin < 0:
            print('Data is skewed to the left.')
            self.errs.skew = self.data.segmented_derotated.xmin

        if self.errs.skew is not None:
            self.applyDeskew()
        else:
            print('Error in finding the skew value')

    def applyDeskew(self) -> None:
        self.data.segmented_derotated_deskewed = deepcopy(self.data.segmented_derotated)
        print(f'Skew error in x-direction: {self.errs.skew}px')
        print('Skew detected and calculated. Applying deskew...')

        for (i, calPath) in enumerate(self.data.segmented_derotated.case):
            for (j, pt) in enumerate(calPath.path):
                self.data.segmented_derotated_deskewed.case[i].path[j] = self.deskew(pt)
            self.data.segmented_derotated_deskewed.case[i].getProperties()
        self.data.segmented_derotated_deskewed.getRange()

        print('Deskew applied succesfully.\n')

    def analyzeError(self) -> None:
        self.findRotationErrorFromMidline()
        self.findSkewError()

    def getError(self) -> Tuple[float]:
        return self.errs

    def getCorrectedData(self) -> HMR_EVTestData:
        return self.data

    @staticmethod
    def getPathArray(calPath:HMR_CalibrationPath) -> Tuple[List[float]]:
        X = [0]*len(calPath.path)
        Y = [0]*len(calPath.path)
        for (i, pt) in enumerate(calPath.path):
            X[i] = pt.x
            Y[i] = pt.y
        return (X, Y)

    @staticmethod
    def getSlope(X:List[float], Y:List[float], isVertical:bool = False) -> float:
        if isVertical:
            X, Y = Y, X

        try:
            model = Polynomial.fit(X, Y, 1)
            return model.convert().coef[1]
        except:
            print('Curve fitting failed, skipping this path.\n')
