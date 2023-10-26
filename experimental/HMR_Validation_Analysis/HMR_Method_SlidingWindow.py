from HMR_Data                       import *
from HMR_DataAnalysisUtility        import (l2CoorNorm, getOffset)
from HMR_CurveFitting               import HMR_LeastSquareRegressionCurveFitting
from HMR_EvaluationConfig           import (MIN_WINDOW_SIZE, MAX_WINDOW_SIZE, SUCCESS_FACTOR_THRESHOLD)
from HMR_EvaluationLogger           import HMR_EvaluationLogger
from numpy                          import (mean, std)


class HMR_Method_SlidingWindow():
    def __init__(
        self,
        refPath:HMR_Path,
        resPath:HMR_Path,
        screenDiagSizeMm:float,
        logger:HMR_EvaluationLogger
    ) -> None:
        self.l2RadiusMm = screenDiagSizeMm

        self.refPath = refPath
        self.resPath = resPath
        self.isInRadiusSearch = False
        self.logger = logger
        self.reinit()

    def reinit(self) -> None:
        self.steps = 0
        self.currWindowSize = 0
        self.minWindowSize = MIN_WINDOW_SIZE
        self.maxWindowSize = MAX_WINDOW_SIZE

        self.currRefWindowFront = self.refPath.getStart()
        self.currRefWindowEnd = self.currRefWindowFront
        self.currResWindowFront = self.resPath.getStart()
        self.currResWindowEnd = self.currResWindowFront

        self.refDoi = HMR_DataOfInterest()
        self.resDoi = HMR_DataOfInterest()
        self.curveFitting = HMR_LeastSquareRegressionCurveFitting()
        self.pathResult = HMR_PathResult()

    def addRefPointToWindow(self, point:HMR_Point) -> None:
        self.refDoi.addPoint(point)
        self.currWindowSize += 1

    def expandFront(self) -> None:
        # Add ref point to refDoi.
        # Propagate one point only, loop until a different point is found.
        while self.currRefWindowFront != self.refPath.points_tail:
            self.addRefPointToWindow(self.currRefWindowFront)
            self.currRefWindowFront = self.currRefWindowFront.next
            if not self.currRefWindowFront.hasSameCoorAs(self.currRefWindowFront.prev):
                break

        # Add points in the res data which are within the L2 norm imaginary circle.
        while (
            self.currResWindowFront != self.resPath.points_tail and
            l2CoorNorm(self.currRefWindowFront.prev, self.currResWindowFront) <= self.l2RadiusMm
        ):
            self.resDoi.addPoint(self.currResWindowFront)
            self.currResWindowFront = self.currResWindowFront.next

    def removeRefPointFromWindow(self, point:HMR_Point) -> None:
        self.refDoi.removePoint(point)
        self.currWindowSize -= 1

    def contractBack(self) -> None:
        # Contract the back window in ref path.
        # Propagate one point only, loop until a different point is found.
        while (self.currWindowSize > self.minWindowSize and
               self.currRefWindowEnd != self.currRefWindowFront):
            self.removeRefPointFromWindow(self.currRefWindowEnd)
            self.currRefWindowEnd = self.currRefWindowEnd.next
            if not self.currRefWindowEnd.hasSameCoorAs(self.currRefWindowEnd.prev):
                break

        # Remove all the res points behind the back normal from resDoi.
        while (
            self.currResWindowEnd != self.currResWindowFront and
            l2CoorNorm(self.currRefWindowEnd.prev, self.currResWindowEnd) <= self.l2RadiusMm
        ):
            self.resDoi.removePoint(self.currResWindowEnd)
            self.currResWindowEnd = self.currResWindowEnd.next

        if self.currWindowSize < 0:
            raise Exception('Current window size < 0!')

    def propagate(self) -> None:
        # propagate for 1 step
        self.expandFront()

        while self.currWindowSize > self.maxWindowSize:
            self.contractBack()

    def walkPath(self) -> HMR_PathResult:
        self.reinit()
        totalErr = 0
        nCalculation = 0
        nSuccessFit = 0

        while self.currRefWindowFront != self.refPath.points_tail:
            self.propagate()

            # Calculate squared error.
            if self.currWindowSize >= self.minWindowSize and len(self.resDoi.points) != 0:
                totalErr += self.curveFitting.getError(self.refDoi.points, self.resDoi.points)
                nSuccessFit += 1 if self.curveFitting.isSuccess() else 0
                nCalculation += 1
                self.addCurveFittingResults(nCalculation)

            self.addIterCalResults(nCalculation)
            self.steps += 1

        self.calculateSuccessFactor(nSuccessFit, nCalculation)
        self.calculatePathMse(totalErr, nCalculation)
        return self.pathResult

    def addIterCalResults(self, nCalculation:int) -> None:
        if self.isInRadiusSearch:
            return

        self.pathResult.nCalculation.append(nCalculation)
        self.pathResult.nSteps.append(self.steps)

    def addCurveFittingResults(self, nCalculation:int) -> None:
        if self.isInRadiusSearch:
            return

        self.pathResult.R2.append(self.curveFitting.R2)
        self.pathResult.offset.append(getOffset(self.refDoi.points, self.resDoi.points))
        self.pathResult.squaredError.append(self.curveFitting.err)
        self.pathResult.currWindowSize.append(self.currWindowSize)
        self.pathResult.nRefPoints.append(len(self.refDoi.points))
        self.pathResult.nResPoints.append(len(self.resDoi.points))

        self.pathResult.curveFittings.append(HMR_CurveFittingResult(
            self.refDoi,
            self.resDoi,
            self.curveFitting.getCurveFittingResult(),
            self.maxWindowSize,
            self.steps,
            nCalculation
        ))

    def calculatePathMse(self, totalErr:float, nCalculation:int) ->float:
        # Calculate MSE for this path.
        # Value divided by iterations because the manipulator can stand still
        # in which case we propagate until it moves. So the number of averages
        # that totalDirSquaredError takes != the length of the path.
        self.pathResult.pathMse = totalErr/nCalculation if nCalculation > 0 else 0

    def calculateSuccessFactor(self, nSuccessFit, nCalculation) -> None:
        if self.isInRadiusSearch:
            return

        if nCalculation > 0:
            self.pathResult.pathSuccessFactor = nSuccessFit/nCalculation
            self.pathResult.offsetMean = mean(self.pathResult.offset)
            self.pathResult.offsetStd = std(self.pathResult.offset)
            self.pathResult.offsetMax = max(self.pathResult.offset)
            self.pathResult.R2Mean = mean(self.pathResult.R2)
            self.pathResult.R2Std = std(self.pathResult.R2)
            self.pathResult.R2Min = min(self.pathResult.R2)

            self.logger.info(f'{nCalculation} curve fitting(s) performed in total.')
            self.logger.info(f'Offset average = {self.pathResult.offsetMean}mm')
            self.logger.info(f'Offset standard deviation = {self.pathResult.offsetStd}mm')
            self.logger.info(f'Maximum offset = {self.pathResult.offsetMax}mm')
            self.logger.info(f'R2 average = {self.pathResult.R2Mean}')
            self.logger.info(f'R2 standard deviation = {self.pathResult.R2Std}')
            self.logger.info(f'Minimum R2 = {self.pathResult.R2Min}')
            self.logger.info(f'Success rate: {self.pathResult.pathSuccessFactor} (rate of curve fittings having R2 >= 0.95).')

            if self.pathResult.pathSuccessFactor < SUCCESS_FACTOR_THRESHOLD:
                self.logger.warning(f'Success factor {self.pathResult.pathSuccessFactor} less than threshold {SUCCESS_FACTOR_THRESHOLD}.')

        else:
            self.logger.warning('There is no calculation!')

    def getBubbleRadius(self) -> None:
        self.isInRadiusSearch = True
        left = 0
        right = self.l2RadiusMm # init to screen diag size

        # search a radius that can include all result points
        res = None
        while (left <= right):
            mid = (left + right) // 2
            self.l2RadiusMm = mid
            self.walkPath()

            if (self.currResWindowFront == self.resPath.points_tail):
                res = mid
                right = mid - 1
            else:
                left = mid + 1

        if res is None:
            raise ValueError('Cannot find a bubble radius!')

        self.l2RadiusMm = res
        self.isInRadiusSearch = False
        self.logger.info(f'Bubble radius is determined to be: {self.l2RadiusMm}mm.')
