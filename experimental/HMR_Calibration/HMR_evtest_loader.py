from HMR_calibration_data   import *
from typing                 import List, Any
from copy                   import deepcopy
import csv


class HMR_EVTestLoader():
    def __init__(self, csvFilePath:str, thresholds:HMR_Thresholds) -> None:
        self.csvFilePath = csvFilePath
        self.thresholds = thresholds
        self.expectedFieldNames:List[str] = ['x', 'y', 'pressure', 'time']

        self.raw_evtest = []
        self.data = HMR_EVTestData()

    def stringToValue(self, value:str) -> int:
        return float(0) if value == '' else float(value)

    def getPoint(self, row:dict) -> List[float]:
        coorX = self.stringToValue(row['x'])
        coorY = self.stringToValue(row['y'])
        pressure = self.stringToValue(row['pressure'])
        self.data.raw_xmax = max(self.data.raw_xmax, coorX)
        self.data.raw_ymax = max(self.data.raw_ymax, coorY)
        return [coorX, coorY, pressure]

    def getRawData(self, data: list[dict[str | Any, str | Any]]) -> None:
        self.raw_evtest = [None]*len(data)
        for idx in range(len(data)):
            self.raw_evtest[idx] = self.getPoint(data[idx])

    def getSegmentedData(self) -> None:
        # Get and record paths with pressure > 0
        idx = 0
        while idx < len(self.raw_evtest):
            [coorX, coorY, pressure] = self.raw_evtest[idx]
            if pressure > 0: # pressure > 0, Source start point
                calPath = HMR_CalibrationPath()
                while not pressure == 0: # pressure = 0, Source end point
                    calPath.path.append(HMR_CalibrationPoint(coorX, coorY))
                    idx += 1
                    if idx >= len(self.raw_evtest):
                        break

                    [coorX, coorY, pressure] = self.raw_evtest[idx]

                calPath.getProperties()
                calPath.isSizeEnough = (len(calPath.path) > self.thresholds.filter)

                self.data.segmented.case.append(deepcopy(calPath))

            else:
                idx += 1

        self.data.segmented.getRange()
        self.data.segmented.calLongestpath(self.thresholds.midline)

    def readDataFromCSV(self) -> None:
        data = csv.DictReader(open(self.csvFilePath))

        # Check field names:
        if len(self.expectedFieldNames) != len(data.fieldnames):
            raise Exception('Expect a csv file with data: [x, y, presssure, time] only')

        for name in self.expectedFieldNames:
            if name not in data.fieldnames:
                raise Exception('Expect a csv file with data: [x, y, presssure, time]')

        self.getRawData(list(data))
        self.getSegmentedData()
        print('Raw data loaded successfully!\n')

    def getData(self) -> HMR_EVTestData:
        return self.data
