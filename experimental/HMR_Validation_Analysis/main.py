from HMR_DataCorrection     import HMR_DataCorrection
from HMR_DataExtraction     import HMR_DataExtraction
from HMR_DataAnalysis       import HMR_DataAnalysis
from HMR_TestCasePlotter    import HMR_TestCasePlotter
from HMR_Data               import HMR_DUTDimensions
from HMR_EvaluationLogger   import HMR_EvaluationLogger
from HMR_EvaluationConfig   import MSE_THRESHOLD
import os


def runEvaluation(
    refCsvFilePath:str,
    resultCsvFilePath:str,
    calibrationLogPath:str,
    refTestDimensions:HMR_DUTDimensions,
    resTestDimensions:HMR_DUTDimensions,
    needCurveFittingPlots:bool
) -> str:
    logger = HMR_EvaluationLogger(resultCsvFilePath)

    logger.info(f'Evaluation starts.\n')
    dataCorr = HMR_DataCorrection(calibrationLogPath)
    ref = HMR_DataExtraction(dataCorr, logger)
    res = HMR_DataExtraction(dataCorr, logger)

    ref.getDataFromCSV(refCsvFilePath, refTestDimensions)
    res.getDataFromCSV(resultCsvFilePath, resTestDimensions, True)

    ref.readRefCSV()
    refTestCase = ref.getTestCase()
    res.readResCSV(refTestCase)
    resTestCase = res.getTestCase()

    dataAna = HMR_DataAnalysis(logger)
    caseResult = dataAna.runSlidingWindow(refTestCase, resTestCase)

    testResult = "PASS" if caseResult.mse <= MSE_THRESHOLD else "FAIL"
    logger.info(f'Evaluation result - {testResult}.\n')

    dataPlot = HMR_TestCasePlotter(refTestCase, resTestCase, caseResult, logger, resultCsvFilePath, needCurveFittingPlots)
    dataPlot.plotAll()
    logger.info(f'This logging is saved at: {logger.destFolder}/{logger.name}.log')
    return testResult

def isPathValid(path:str) -> None:
    if not os.path.exists(path):
        raise ValueError(f'{path} is not valid.')


if __name__ == "__main__":
    refCsvFilePath          = ''
    resultCsvFilePath       = ''
    calibrationLogPath      = ''
    refTestDimensions       = HMR_DUTDimensions(0, 0)
    resTestDimensions       = HMR_DUTDimensions(0, 0)
    needCurveFittingPlots   = False

    for path in [refCsvFilePath, resultCsvFilePath, calibrationLogPath]:
        isPathValid(path)

    testResult = runEvaluation(
        refCsvFilePath,
        resultCsvFilePath,
        calibrationLogPath,
        refTestDimensions,
        resTestDimensions,
        needCurveFittingPlots
    )
