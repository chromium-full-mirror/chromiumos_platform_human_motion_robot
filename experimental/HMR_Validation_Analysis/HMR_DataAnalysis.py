from HMR_Data                   import HMR_TestCase, HMR_CaseResult
from HMR_Method_SlidingWindow   import HMR_Method_SlidingWindow
from HMR_EvaluationLogger       import HMR_EvaluationLogger
from typing                     import List
from math                       import sqrt


class HMR_DataAnalysis():
    def __init__(self, logger:HMR_EvaluationLogger) -> None:
        self.logger = logger

    def getTimeElapsedDistribution(self, testCase:HMR_TestCase) -> List[float]:
        size = 0 # number of points in paths
        for path in testCase.paths:
            size += path.length

        timeElapses = [None]*size

        idx = 0
        for path in testCase.paths:
            curr = path.getStart()
            while curr != path.points_tail:
                timeElapses[idx] = curr.timeToNextPointMs
                curr = curr.next
                idx += 1

        return timeElapses

    def runSlidingWindow(self, refTestCase:HMR_TestCase, resTestCase:HMR_TestCase) -> HMR_CaseResult:
        caseResult = HMR_CaseResult()
        dutSizeX, dutSizeY = refTestCase.getScreenSize()
        for i, (refPath, resPath) in enumerate(zip(refTestCase.paths, resTestCase.paths)):
            self.logger.info(f'Path: {i} start >>>>>>>>>>>>>>>>>>>>>>>>>>>')
            SW = HMR_Method_SlidingWindow(refPath, resPath, sqrt(dutSizeX**2 + dutSizeY**2), self.logger)
            SW.getBubbleRadius()
            pathResult = SW.walkPath()
            caseResult.addPathResult(pathResult)
            self.logger.info(f'Path: {i} end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n')

        caseResult.takeAverages()

        overallAnalysisTable = (
            'Table of overall analysis ==================================\n' +
            f'Total number of paths = {len(caseResult.pathResults)}\n' +
            f'Mean offset average = {caseResult.averageOffsetMean}mm\n' +
            f'Mean offset standard deviation = {caseResult.averageOffsetStd}mm\n' +
            f'Mean maximum offset = {caseResult.averageOffsetMax}mm\n' +
            f'Mean R2 average = {caseResult.averageR2Mean}\n' +
            f'Mean R2 standard deviation = {caseResult.averageR2Std}\n' +
            f'Mean minimum R2 = {caseResult.averageR2Min}\n' +
            f'Mean success factor = {caseResult.successFactor}\n' +
            f'Mean squared error = {caseResult.mse}\n' +
            f'Table of overall analysis end ==============================\n'
        )
        self.logger.saveOverallAnalysisTable(overallAnalysisTable)
        return caseResult
