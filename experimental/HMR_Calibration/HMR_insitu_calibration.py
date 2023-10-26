from HMR_evtest_loader          import HMR_EVTestLoader
from HMR_error_analyzer         import HMR_ErrorAnalyzer
from HMR_calibration_data       import (HMR_DUTDimensions, HMR_Margins, HMR_Thresholds)
from HMR_correction_analyzer    import HMR_CorrectionAnalyzer
from HMR_calibration_plotter    import HMR_CalibrationPlotter
import os


def runCalibration(csvFilePath:str, dutDimensions:HMR_DUTDimensions, margins:HMR_Margins, threshold:HMR_Thresholds, isPlotSave:bool) -> None:
    print(
    f'Input configs:\n\
    * Length {dutDimensions.l}mm, Width: {dutDimensions.w}mm\n\
    * Interior margin: {margins.interior}, Exterior margin: {margins.exterior}\n'
    )

    evTestLoader = HMR_EVTestLoader(csvFilePath, threshold)
    evTestLoader.readDataFromCSV()
    data = evTestLoader.getData()

    errFinder = HMR_ErrorAnalyzer(data, threshold)
    errFinder.analyzeError()
    errs = errFinder.getError()
    correctedData = errFinder.getCorrectedData()

    correctionAnalyzer = HMR_CorrectionAnalyzer(correctedData, errs, dutDimensions, margins, threshold, csvFilePath)
    correctionAnalyzer.calCorrectedDutDimensions()
    correctionAnalyzer.exportCorrectionMatrix()
    calibratedData = correctionAnalyzer.getCalibratedData()

    plotter = HMR_CalibrationPlotter(calibratedData, csvFilePath, isPlotSave)
    plotter.plotAll()

def isPathValid(path:str) -> None:
    if not os.path.exists(path):
        raise ValueError(f'{path} is not valid.')

if __name__ == "__main__":
    csvFilePath = ''
    dutDimensions = HMR_DUTDimensions(0, 0)

    margins = HMR_Margins(10, 2)
    threshold = HMR_Thresholds(100, 100)
    isPlotSave = True

    isPathValid(csvFilePath)
    runCalibration(
        csvFilePath,
        dutDimensions,
        margins,
        threshold,
        isPlotSave
    )
