from HMR_calibration_data           import *
from HMR_error_analyzer             import HMR_ErrorAnalyzer
from numpy                          import arctan2, inf, deg2rad
from pathlib                        import Path


HORZ_DEGREE = deg2rad(10)
VERT_DEGREE = deg2rad(80)
class HMR_CorrectionAnalyzer():
    def __init__(
        self,
        data: HMR_EVTestData,
        errs: HMR_Errors,
        dutDimensions: HMR_DUTDimensions,
        margins: HMR_Margins,
        thresholds: HMR_Thresholds,
        csvFilePath:str
    ) -> None:
        self.data = data
        self.errs = errs
        self.dutDimensions = dutDimensions
        self.margins = margins
        self.thresholds = thresholds
        self.name = Path(csvFilePath).stem
        self.directory = str(Path(csvFilePath).parent)

        self.scaleFactor = HMR_CalibrationPoint()
        self.offset = HMR_CalibrationPoint()

    def markDirections(self) -> None:
        for (i, calPath) in enumerate(self.data.segmented_derotated_deskewed.case):
            if calPath.isSizeEnough:
                X, Y = HMR_ErrorAnalyzer.getPathArray(calPath)
                slope = HMR_ErrorAnalyzer.getSlope(X, Y)
                if slope is not None:
                    angle = arctan2(slope, 1.0)

                if abs(angle) < HORZ_DEGREE:
                    calPath.isHorizontal = True

                elif abs(angle) > VERT_DEGREE:
                    calPath.isHorizontal = False

                else:
                    print(f'cannot identify line {i}.')

    def correct(self, pt:HMR_CalibrationPoint) -> HMR_CalibrationPoint:
        return HMR_CalibrationPoint(
            pt.x*self.scaleFactor.x + self.offset.x,
            pt.y*self.scaleFactor.y + self.offset.y
        )

    def correctData(self) -> None:
        self.data.segmented_calibrated.case = [None]*len(self.data.segmented_derotated_deskewed.case)
        for (i, calPath) in enumerate(self.data.segmented_derotated_deskewed.case):
            newCalPath = HMR_CalibrationPath()
            newCalPath.path = [None]*len(calPath.path)
            for (j, pt) in enumerate(calPath.path):
                newCalPath.path[j] = self.correct(pt)

            newCalPath.getProperties()
            self.data.segmented_calibrated.case[i] = newCalPath

        self.data.segmented_calibrated.getRange()
        self.data.segmented_calibrated.calLongestpath(self.thresholds.midline)

        print('Calculated DUT dimensions:')
        print(f'xmin: {self.data.segmented_calibrated.xmin}, xmax: {self.data.segmented_calibrated.xmax}')
        print(f'ymin: {self.data.segmented_calibrated.ymin}, ymax: {self.data.segmented_calibrated.ymax}\n')

    def calCorrectedDutDimensions(self) -> None:
        self.markDirections()

        # Specify the lines along the top and bottom edges
        h_top_y = -inf
        h_bot_y = inf
        v_left_x = -inf
        v_right_x = inf
        for calPath in self.data.segmented_derotated_deskewed.case:
            if calPath.isSizeEnough and calPath.isHorizontal:
                if calPath.ymean < self.data.raw_ymax*(self.margins.interior + self.margins.exterior)/self.dutDimensions.w:
                    h_top_y = max(h_top_y, calPath.ymean)

                elif calPath.ymean > self.data.raw_ymax*(self.dutDimensions.w - self.margins.interior)/self.dutDimensions.w:
                    h_bot_y = min(h_bot_y, calPath.ymean)

            elif calPath.isSizeEnough and not calPath.isHorizontal:
                if calPath.xmean < self.data.raw_xmax*(self.margins.interior + self.margins.exterior)/self.dutDimensions.l:
                    v_left_x = max(v_left_x, calPath.xmean)

                elif calPath.xmean > self.data.raw_xmax*(self.dutDimensions.l - self.margins.interior)/self.dutDimensions.l:
                    v_right_x = min(v_right_x, calPath.xmean)

        # Calculate scale factor and offset
        self.scaleFactor.x = (self.dutDimensions.l - 2*self.margins.interior)/(v_right_x - v_left_x)
        self.scaleFactor.y = (self.dutDimensions.w - 2*self.margins.interior)/(h_bot_y - h_top_y)
        self.offset.x = self.margins.interior - v_left_x*self.scaleFactor.x
        self.offset.y = self.margins.interior - h_top_y*self.scaleFactor.y

        self.correctData()

    def exportCorrectionMatrix(self) -> None:
        result = f'rot_err,{self.errs.rotation}\nskew_err,{self.errs.skew}\nSFx,{self.scaleFactor.x}\nSFy,{self.scaleFactor.y}\nOSx,{self.offset.x}\nOSy,{self.offset.y}\nymax,{self.data.raw_ymax}'
        print(f'Result:\n{result}\n')
        log = open(f"{self.directory}/{self.name}.log", "w")
        log.write(result)
        log.close()
        print(f'Result is exported to {self.directory}/{self.name}.log\n')

    def getCalibratedData(self) -> HMR_EVTestData:
        return self.data
