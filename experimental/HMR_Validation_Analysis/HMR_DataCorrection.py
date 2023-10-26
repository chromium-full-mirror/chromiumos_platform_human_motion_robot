from HMR_Data       import HMR_Point
from math           import (sin, cos)


class HMR_DataCorrection():
    def __init__(self, calibrationLogPath:str):
        self.rot_err = 0
        self.skew_err = 0
        self.SFx = 0
        self.SFy = 0
        self.OSx = 0
        self.OSy = 0
        self.ymax = 0

        self.readCalibrationLog(calibrationLogPath)

    def readCalibrationLog(self, calibrationLogPath:str) -> None:
        with open(calibrationLogPath) as calLog:
            for line in calLog:
                attr, val = line.split(',')
                self.__setattr__(attr, float(val))

    def scaleAndTranslate(self, pt:HMR_Point):
        x = pt.coorX
        y = pt.coorY
        pt.coorX = self.SFx*x + self.OSx
        pt.coorY = self.SFy*y + self.OSy

    def deRotate(self, pt:HMR_Point) -> None:
        """
        Rotate a point counterclockwise by a given (+)angle in radian around a given origin.
        """
        x = pt.coorX
        y = pt.coorY
        pt.coorX = x*cos(self.rot_err) - y*sin(self.rot_err)
        pt.coorY = x*sin(self.rot_err) + y*cos(self.rot_err)

    def deSkew(self, pt:HMR_Point) -> None:
        """
        Skew a point around a given origin
        sh_x: skew factor along x axis (+ to right, - to left)
        sh_y: skew factor along y axis (+ to up, - to down)
        """
        x = pt.coorX
        y = pt.coorY
        pt.coorX = x + self.skew_err*y/self.ymax
        pt.coorY = y

    def correct(self, pt:HMR_Point) -> None:
        self.deRotate(pt)
        self.deSkew(pt)
        self.scaleAndTranslate(pt)
