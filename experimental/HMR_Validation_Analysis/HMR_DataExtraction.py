from HMR_Data                   import (HMR_DUTDimensions, HMR_Point, HMR_Path, HMR_TestCase)
from HMR_DataCorrection         import HMR_DataCorrection
from HMR_DataAnalysisUtility    import l2CoorNorm
from HMR_EvaluationConfig       import PATH_SIZE_THRESHOLD
from HMR_EvaluationLogger       import HMR_EvaluationLogger
from typing                     import (Tuple, List)
from copy                       import copy
from math                       import sqrt
import csv


class HMR_DataExtraction():
    def __init__(self, dataCorr:HMR_DataCorrection, logger:HMR_EvaluationLogger) -> None:
        self.reset()
        self.dataCorr = dataCorr
        self.logger = logger

    def reset(self) -> None:
        self.expectedFieldNames:List[str] = ['x', 'y', 'pressure', 'time']
        self.data:List[HMR_Point] = []
        self.testCase:HMR_TestCase = HMR_TestCase()

    def stringToRoundedValue(self, value:str, scale:float = 1) -> int:
        if value is None:
            raise ValueError('Received None (null). File possibly corrupted!')

        if value == '':
            return 0

        return float(value)*scale

    def getPoint(self, row:dict) -> HMR_Point:
        coorX = self.stringToRoundedValue(row['x'])
        coorY = self.stringToRoundedValue(row['y'])
        pressure = self.stringToRoundedValue(row['pressure'])
        timeMs = self.stringToRoundedValue(row['time'], 1000)

        return HMR_Point(coorX, coorY, pressure, timeMs)

    def processPoint(self, pt:HMR_Point) -> None:
        # minus time offset and append to path:
        pt.timeMs -= self.testCase.startTimeMs
        self.testCase.length += 1

        if pt.pressure != 0:
            self.testCase.maxCoorX = max(self.testCase.maxCoorX, pt.coorX)
            self.testCase.maxCoorY = max(self.testCase.maxCoorY, pt.coorY)
            self.testCase.maxPressure = max(self.testCase.maxPressure, pt.pressure)
            self.testCase.minCoorX = min(self.testCase.minCoorX, pt.coorX)
            self.testCase.minCoorY = min(self.testCase.minCoorY, pt.coorY)
            self.testCase.minPressure = min(self.testCase.minPressure, pt.pressure)

    def getTestCaseStartPoint(self) -> HMR_Point:
        return self.data[0]

    def getDataFromCSV(self, csvFilePath:str, dutDimensions:HMR_DUTDimensions, isResult:bool = False) -> None:
        self.reset()

        # read csv data:
        data = csv.DictReader(open(csvFilePath))

        # Check field names:
        if len(self.expectedFieldNames) != len(data.fieldnames):
            raise Exception('Expect a csv file with data: [x, y, presssure, time] only')

        for name in self.expectedFieldNames:
            if name not in data.fieldnames:
                raise Exception('Expect a csv file with data: [x, y, presssure, time]')

        # Get data:
        data = list(data)
        for idx in range(len(data)):
            pt = self.getPoint(data[idx])
            if idx == 0:
                self.testCase.startTimeMs = pt.timeMs

            if isResult:
                self.dataCorr.scaleAndTranslate(pt)
            else:
                self.dataCorr.correct(pt)

            self.processPoint(pt)
            self.data.append(pt)

        self.testCase.setScreenSize(dutDimensions.l, dutDimensions.w)

    def readRefCSV(self) -> None:
        self.logger.info('Extracting reference paths.')
        idx = 0
        pathCount = 0
        nNoisePath = 0
        while idx < len(self.data):
            pt = self.data[idx]
            if pt.pressure > 0: # Source start point
                path = HMR_Path()
                prev_pt = HMR_Point()
                pathSize = 0
                while not pt.pressure == 0: # Source end point
                    if not pt.hasSameCoorAs(prev_pt):
                        path.addToTail(pt)
                        prev_pt = pt
                        pathSize += 1

                    idx += 1
                    if idx >= len(self.data):
                        break
                    pt = self.data[idx]

                pathCount += 1
                if pathSize < PATH_SIZE_THRESHOLD:
                    self.logger.warning(f'Path {pathCount} has a size = {pathSize} less than size threshold {PATH_SIZE_THRESHOLD}.')
                    nNoisePath += 1
                    continue
                self.testCase.addPath(copy(path))

            else:
                idx += 1

        if nNoisePath > 0:
            self.logger.warning(f'[WARN]: There are {nNoisePath} paths that has a size less than {PATH_SIZE_THRESHOLD}, which can be noise.')
            self.logger.warning(f'[WARN]: If this is not intentional please consider preprocessing the referrence case.')
        self.testCase.getTestCaseProperties()
        self.logger.info(f'[INFO]: Reference path extraction done.\n')

    def isStylusDown(self, idx:int) -> bool:
        if idx < 0 or idx >= len(self.data):
            raise ValueError('Index out of range')

        if idx == 0:
            return self.data[idx].pressure > 0
        else:
            return self.data[idx - 1].pressure == 0 and self.data[idx].pressure > 0

    def isStylusUp(self, idx:int) -> bool:
        if idx < 0 or idx >= len(self.data):
            raise ValueError('Index out of range')

        if idx == 0:
            return self.data[idx] == 0
        else:
            return self.data[idx - 1].pressure > 0 and self.data[idx].pressure == 0

    def getResStartPointIdxs(self, refTestCase:HMR_TestCase, epsilon:int) -> List[int]:
        nRefPaths = len(refTestCase.paths)
        startPointIdxs = [None]*nRefPaths
        refPathIdx = 0
        idx = 0

        while idx < len(self.data) and refPathIdx < nRefPaths:
            if (self.isStylusDown(idx) and
                l2CoorNorm(self.data[idx], refTestCase.paths[refPathIdx].getStart()) <= epsilon):

                startPointIdxs[refPathIdx] = idx
                idx += 1
                while (idx < len(self.data) and
                    not (self.isStylusUp(idx) and
                         l2CoorNorm(self.data[idx], refTestCase.paths[refPathIdx].getEnd()) <= epsilon)):
                    idx += 1
                refPathIdx += 1
            else:
                idx += 1

        return startPointIdxs

    def getResEndPointIdxs(self, refTestCase:HMR_TestCase, epsilon:int) -> List[int]:
        nRefPaths = len(refTestCase.paths)
        endPointIdxs = [None]*nRefPaths
        refPathIdx = nRefPaths - 1
        idx = len(self.data) - 1
        while idx >= 0 and refPathIdx >= 0:
            if (self.isStylusUp(idx) and
                l2CoorNorm(self.data[idx], refTestCase.paths[refPathIdx].getEnd()) <= epsilon):
                endPointIdxs[refPathIdx] = idx - 1 if idx != 0 else 0
                idx -= 1
                while (idx >= 0 and
                    not (self.isStylusDown(idx) and
                         l2CoorNorm(self.data[idx], refTestCase.paths[refPathIdx].getStart()) <= epsilon)):
                    idx -= 1
                refPathIdx -= 1
            else:
                idx -= 1

        return endPointIdxs

    def getResStartAndEndPointIdxs(self, refTestCase:HMR_TestCase, epsilon:int) -> Tuple[List[int]]:
        nRefPaths = len(refTestCase.paths)
        startPointIdxs = [None]*nRefPaths
        endPointIdxs = [None]*nRefPaths
        refPathIdx = 0
        idx = 0

        while idx < len(self.data) and refPathIdx < nRefPaths:
            if (self.isStylusDown(idx) and l2CoorNorm(self.data[idx], refTestCase.paths[refPathIdx].getStart()) <= epsilon):
                # found a start point
                startPointIdxs[refPathIdx] = idx
                idx += 1

                # find the end point for this path
                while idx < len(self.data):
                    if ((idx == len(self.data) - 1) or
                        (self.isStylusUp(idx + 1) and l2CoorNorm(self.data[idx], refTestCase.paths[refPathIdx].getEnd()) <= epsilon)):
                        endPointIdxs[refPathIdx] = idx
                        idx += 1
                        break
                    idx += 1
                refPathIdx += 1
            else:
                idx += 1

        return (startPointIdxs, endPointIdxs)

    def linkPaths(self, refTestCase:HMR_TestCase, epsilon:int) -> None:
        self.logger.info(f'[INFO]: Result paths extraction radius is determined to be {epsilon}mm.')
        startPointIdxs, endPointIdxs = self.getResStartAndEndPointIdxs(refTestCase, epsilon)

        prevEnd = -1
        for start, end in zip(startPointIdxs, endPointIdxs):
            if start > end:
                raise ValueError('Index Error')

            if prevEnd >= start:
                raise ValueError('Path overlap!')
            prevEnd = end

            path = HMR_Path()
            idx = start
            while idx <= end:
                pt = self.data[idx]
                path.addToTail(pt)
                idx += 1
            self.testCase.addPath(copy(path))
        self.testCase.getTestCaseProperties()

    def numberOfResPaths(self, refTestCase:HMR_TestCase, epsilon:int) -> bool:
        startPointIdxs, endPointIdxs = self.getResStartAndEndPointIdxs(refTestCase, epsilon)
        nResPaths = 0
        for s_idx, e_idx in zip(startPointIdxs, endPointIdxs):
            if s_idx is None or e_idx is None:
                continue
            nResPaths += 1

        return nResPaths

    def readResCSV(self, refTestCase:HMR_TestCase) -> None:
        # Push the number of result paths found to
        # the number of source paths, while minimizing
        # the L2 criteria epsilon.
        self.logger.info('Extracting result paths.')
        dutSizeX, dutSizeY = refTestCase.getScreenSize()
        left = 0
        right = sqrt(dutSizeX**2 + dutSizeY**2)
        epsilon = -1
        while left <= right:
            mid = (left + right) // 2
            nResPaths = self.numberOfResPaths(refTestCase, mid)
            if nResPaths < len(refTestCase.paths):
                left = mid + 1

            else:
                right = mid - 1
                if nResPaths == len(refTestCase.paths):
                    epsilon = mid

        if epsilon < 0:
            raise ValueError('Epsilon is not valid')

        self.linkPaths(refTestCase, epsilon)
        self.logger.info('Result paths extraction done.\n')

    def getTestCase(self) -> HMR_TestCase:
        return self.testCase
