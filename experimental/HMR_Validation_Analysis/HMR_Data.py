from typing             import (Tuple, List, Set, Any)
from math               import (inf, sqrt, ceil)
from dataclasses        import dataclass
from ordered_set        import OrderedSet

@dataclass
class HMR_DUTDimensions():
    l: float # mm
    w: float # mm

    def __init__(self, l:float = None, w:float = None) -> None:
        self.l = l
        self.w = w

@dataclass(eq=False)
class HMR_Point():
    coorX:float                 # coordinate x
    coorY:float                 # coordinate y
    pressure:float              # pressure level
    timeMs:float                # timestamp (milliseconds)
    timeToNextPointMs:float     # time to the next point

    distanceFromPrev:float      # distance from the previous point
    direction:Tuple[float]      # direction to the next point (dx, dy)
    velocity:Tuple[float]       # velocity to the next point (dx/dt, dy/dt)

    prev: 'HMR_Point'
    next: 'HMR_Point'

    def __init__(self, coorX:float = -inf, coorY:float = -inf, pressure:float = -inf, timeMs:float = -inf) -> None:
        self.coorX = coorX
        self.coorY = coorY
        self.pressure = pressure
        self.timeMs = timeMs
        self.timeToNextPointMs = -inf

        self.distanceFromPrev = -inf
        self.direction = tuple()
        self.velocity = tuple()

        self.prev = None
        self.next = None

    def __repr__(self) -> str:
        return f'Point(x={self.coorX}, y={self.coorY}, p={self.pressure}, t={self.timeMs})'

    def isValid(self) -> bool:
        return False if (
            self.coorX == -inf and
            self.coorY == -inf and
            self.pressure == -inf and
            self.timeMs == -inf and
            self.timeToNextPointMs == -inf and
            self.distanceFromPrev == -inf and
            self.direction == () and
            self.velocity == () and
            self.prev == None and
            self.next == None
        ) else True

    def calDistanceFromPrev(self) -> float:
        if not self.isValid():
            return

        p = self.prev
        self.distanceFromPrev = sqrt(
            (self.coorX - p.coorX)**2 + (self.coorY - p.coorY)**2
        ) if p.coorX != -inf else 0

    def calDurationToNextMs(self) ->float:
        if not self.isValid():
            return

        n = self.next
        if n.timeMs == -inf: # current point is end point
            self.timeToNextPointMs = 0
        else:
            self.timeToNextPointMs = n.timeMs - self.timeMs
        return self.timeToNextPointMs

    def calDirectionToNext(self) -> Tuple[float]:
        if not self.isValid():
            return

        n = self.next
        if n.coorX == -inf:
            self.direction = (0, 0)
        else:
            self.direction = (n.coorX - self.coorX, n.coorY - self.coorY)

        return self.direction

    def calVelocityToNext(self) -> Tuple[float]:
        if not self.isValid():
            return

        n = self.next
        if n.timeMs == -inf:
            self.velocity = (0, 0)
        else:
            # If the times are the same set to inf so that the velocity is 0
            timeToNextPointMs = n.timeMs - self.timeMs if n.timeMs != self.timeMs else inf
            self.velocity = (
                (n.coorX - self.coorX)/timeToNextPointMs,
                (n.coorY - self.coorY)/timeToNextPointMs
            )
        return self.velocity

    def getPointProperties(self) -> None:
        self.calDurationToNextMs()
        self.calDirectionToNext()
        self.calVelocityToNext()
        self.calDistanceFromPrev()

    def hasSameCoorAs(self, pt:'HMR_Point') -> bool:
        return self.coorX == pt.coorX and self.coorY == pt.coorY

    def distFromOrigin(self) -> float:
        return sqrt(self.coorX**2 + self.coorY**2)

@dataclass
class HMR_Path():
    points_head: HMR_Point # dummy head
    points_tail: HMR_Point # dummy tail
    length: int
    minCoorX: float
    minCoorY: float
    minPressure: float
    maxCoorX: float
    maxCoorY: float
    maxPressure: float
    startTimeMs: float
    endTimeMs: float

    def __init__(self) -> None:
        self.resetProperties()

        self.points_head = HMR_Point()
        self.points_tail = HMR_Point()

        self.points_head.next = self.points_tail
        self.points_tail.prev = self.points_head

    def resetProperties(self) -> None:
        self.minCoorX = inf
        self.minCoorY = inf
        self.minPressure = inf
        self.maxCoorX = -inf
        self.maxCoorY = -inf
        self.maxPressure = -inf
        self.startTimeMs = 0
        self.endTimeMs = 0
        self.length = 0

    def addToTail(self, pt:HMR_Point) -> None:
        p = self.points_tail.prev
        pt.prev = p
        pt.next = self.points_tail

        p.next = pt
        self.points_tail.prev = pt

    def insertAfter(self, target:HMR_Point, ptToAdd:HMR_Point) -> None:
        n = target.next
        ptToAdd.prev = target
        ptToAdd.next = n

        target.next = ptToAdd
        n.prev = ptToAdd

    def getStart(self) -> HMR_Point:
        return self.points_head.next

    def getEnd(self) -> HMR_Point:
        return self.points_tail.prev

    def getPathProperties(self) -> None:
        if self.getStart() == self.points_tail:
            raise ValueError('Empty path!')

        self.resetProperties()
        self.startTimeMs = self.points_head.next.timeMs
        self.endTimeMs = self.points_tail.prev.timeMs

        curr = self.getStart()
        while curr != self.points_tail:
            curr.getPointProperties()
            self.minCoorX = min(self.minCoorX, curr.coorX)
            self.maxCoorX = max(self.maxCoorX, curr.coorX)

            self.minCoorY = min(self.minCoorY, curr.coorY)
            self.maxCoorY = max(self.maxCoorY, curr.coorY)

            self.minPressure = min(self.minPressure, curr.pressure)
            self.maxPressure = max(self.maxPressure, curr.pressure)

            self.length += 1
            curr = curr.next

    def getDurationMs(self) -> float:
        return self.endTimeMs - self.startTimeMs

    def getUpperLeftCoor(self) -> Tuple[int]:
        return (self.minCoorX, self.minCoorY)

    def getLowerRightCoor(self) -> Tuple[int]:
        return (self.maxCoorX, self.maxCoorY)

    def getSize(self) -> Tuple[int]:
        return (self.maxCoorX - self.minCoorX, self.maxCoorY - self.minCoorY)

@dataclass
class HMR_TestCase():
    paths:List[HMR_Path]
    dutSizeX:int
    dutSizeY:int
    maxCoorX:int
    maxCoorY:int
    minCoorX:int
    minCoorY:int
    minPressure:int
    maxPressure:int
    length:int
    startTimeMs:int
    endTimeMs:int

    def __init__(self) -> None:
        self.resetProperties()
        self.dutSizeX = 0
        self.dutSizeY = 0
        self.paths:List[HMR_Path] = []

    def resetProperties(self) -> None:
        self.maxCoorX = -inf
        self.maxCoorY = -inf
        self.maxPressure = -inf
        self.minCoorX = inf
        self.minCoorY = inf
        self.minPressure = inf
        self.startTimeMs = 0
        self.endTimeMs = 0
        self.length = 0

    def setScreenSize(self, dutSizeX:int, dutSizeY:int) -> None:
        self.dutSizeX = dutSizeX
        self.dutSizeY = dutSizeY

    def getScreenSize(self) -> Tuple[int]:
        return (self.dutSizeX, self.dutSizeY)

    def addPath(self, path:HMR_Path) -> None:
        self.paths.append(path)

    def getTestCaseProperties(self) -> None:
        if len(self.paths) == 0:
            raise ValueError('This test case is empty')

        self.resetProperties()
        for path in self.paths:
            path.getPathProperties()
            self.maxCoorX = max(self.maxCoorX, path.maxCoorX)
            self.maxCoorY = max(self.maxCoorY, path.maxCoorY)
            self.maxPressure = max(self.maxPressure, path.maxPressure)
            self.minCoorX = min(self.minCoorX, path.minCoorX)
            self.minCoorY = min(self.minCoorY, path.minCoorY)
            self.minPressure = min(self.minPressure, path.minPressure)
            self.length += path.length

        self.startTimeMs = self.paths[0].startTimeMs
        self.endTimeMs = self.paths[-1].endTimeMs

    def getDurationMs(self) -> float:
        return self.endTimeMs - self.startTimeMs

    def getUpperLeftCoor(self) -> Tuple[int]:
        return (self.minCoorX, self.minCoorY)

    def getLowerRightCoor(self) -> Tuple[int]:
        return (self.maxCoorX, self.maxCoorY)

    def getTestCaseCentre(self) -> Tuple[int]:
        return (self.maxCoorX - self.minCoorX)/2, (self.maxCoorY - self.minCoorY)/2

    def getSize(self) -> Tuple[int]:
        return ceil(self.maxCoorX - self.minCoorX), ceil(self.maxCoorY - self.minCoorY)

@dataclass
class HMR_DataOfInterest():
    points:OrderedSet[HMR_Point]
    directionX:float
    directionY:float
    distance:float

    def __init__(self, directionX:float = 0, directionY:float = 0, distance:float = 0) -> None:
        self.points = OrderedSet()
        self.directionX = directionX
        self.directionY = directionY
        self.distance = distance

    def __add__(self, doi:'HMR_DataOfInterest') -> 'HMR_DataOfInterest':
        return HMR_DataOfInterest(
            self.directionX + doi.directionX,
            self.directionY + doi.directionY,
            self.distance + doi.distance
        )

    def __sub__(self, doi:'HMR_DataOfInterest') -> 'HMR_DataOfInterest':
        return HMR_DataOfInterest(
            self.directionX - doi.directionX,
            self.directionY - doi.directionY,
            self.distance - doi.distance
        )

    def __pow__(self, val:float) -> 'HMR_DataOfInterest':
        return HMR_DataOfInterest(
            self.directionX**val,
            self.directionY**val,
            self.distance**val
        )

    def addPoint(self, pt:HMR_Point) -> None:
        if not pt.isValid():
            raise ValueError('Point is not valid.')

        self.points.add(pt)
        self.directionX += pt.direction[0]
        self.directionY += pt.direction[1]
        self.distance += pt.distanceFromPrev

    def removePoint(self, pt:HMR_Point) -> None:
        if not pt.isValid():
            raise ValueError('Point is not valid.')

        if pt in self.points:
            self.points.remove(pt)

        self.directionX -= pt.direction[0]
        self.directionY -= pt.direction[1]
        self.distance -= pt.distanceFromPrev

@dataclass
class HMR_ExpirationPriorityQueueNode():
    point: HMR_Point
    expirationTime: int
    isRemoved: bool

    def __init__(self, point:HMR_Point, expirationTime:int) -> None:
        self.point = point
        self.expirationTime = expirationTime
        self.isRemoved = False

    def __lt__(self, node:'HMR_ExpirationPriorityQueueNode') -> bool:
        return self.expirationTime < node.expirationTime

    def remove(self) -> None:
        self.isRemoved = True

    def hasRemoved(self) -> bool:
        return self.isRemoved

@dataclass
class HMR_CurveFittingResult():
    ref_x: List[float]
    ref_y: List[float]
    res_x: List[float]
    res_y: List[float]
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    isInverted: bool
    coefficients: List[float]
    R2: float
    error: float
    maxWindowSize: int
    step: int
    calculationNumber: int
    fittedX: List[float]
    fittedY: List[float]

    def __init__(
        self,
        refDoi:HMR_DataOfInterest,
        resDoi:HMR_DataOfInterest,
        curveFittingResult:Tuple,
        maxWindowSize:int,
        step:int,
        calculationNumber:int
    ):
        self.getAllPointsAndRanges(refDoi, resDoi)
        (
            self.isInverted,
            self.coefficients,
            self.R2,
            self.error
        ) = curveFittingResult
        self.maxWindowSize = maxWindowSize
        self.step = step
        self.calculationNumber = calculationNumber

    def getAllPointsAndRanges(self, refDoi:HMR_DataOfInterest, resDoi:HMR_DataOfInterest) -> None:
        self.min_x = inf
        self.max_x = -inf
        self.min_y = inf
        self.max_y = -inf
        self.ref_x, self.ref_y = self.getPlotPoints(refDoi.points)
        self.res_x, self.res_y = self.getPlotPoints(resDoi.points)

    def getPlotPoints(self, points:Set[HMR_Point]):
        x = [None]*len(points)
        y = [None]*len(points)

        for i, pt in enumerate(points):
            self.min_x = min(self.min_x, pt.coorX)
            self.max_x = max(self.max_x, pt.coorX)
            self.min_y = min(self.min_y, pt.coorY)
            self.max_y = max(self.max_y, pt.coorY)
            x[i] = pt.coorX
            y[i] = pt.coorY

        return x, y

@dataclass
class HMR_PathResult():
    curveFittings: List[HMR_CurveFittingResult]
    nCalculation: List[int]
    nSteps: List[int]
    R2: List[float]
    R2Mean: float
    R2Std: float
    R2Min: float
    offset: List[float]
    offsetMean: float
    offsetStd: float
    offsetMax: float
    squaredError: List[float]
    currWindowSize: List[int]
    nRefPoints: List[int]
    nResPoints: List[int]
    pathMse:float
    pathSuccessFactor:float | None

    def __init__(self):
        self.curveFittings = []
        self.nCalculation = []
        self.nSteps = []
        self.R2 = []
        self.R2Mean = 0
        self.R2Std = 0
        self.R2Min = 0
        self.offset = []
        self.offsetMean = 0
        self.offsetStd = 0
        self.offsetMax = 0
        self.squaredError = []
        self.currWindowSize = []
        self.nRefPoints = []
        self.nResPoints = []
        self.pathMse = 0.0
        self.pathSuccessFactor = None

@dataclass
class HMR_CaseResult():
    pathResults: List[HMR_PathResult]
    mse: float
    nValidPath: int
    successFactor: float
    averageOffsetAverage: float
    averageOffsetStd: float
    averageOffsetMax: float
    averageR2Average: float
    averageR2Std: float
    averageR2Min: float

    def __init__(self):
        self.pathResults = []
        self.mse = 0.0
        self.nValidPath = 0
        self.successFactor = 0.0
        self.averageOffsetMean = 0.0
        self.averageOffsetStd = 0.0
        self.averageOffsetMax = 0.0
        self.averageR2Mean = 0.0
        self.averageR2Std = 0.0
        self.averageR2Min = 0.0

    def addPathResult(self, pathResult:HMR_PathResult) -> None:
        self.pathResults.append(pathResult)
        self.mse += pathResult.pathMse

        if pathResult.pathSuccessFactor != None:
            self.nValidPath += 1
            self.successFactor += pathResult.pathSuccessFactor
            self.averageOffsetMean += pathResult.offsetMean
            self.averageOffsetStd += pathResult.offsetStd
            self.averageOffsetMax += pathResult.offsetMax
            self.averageR2Mean += pathResult.R2Mean
            self.averageR2Std += pathResult.R2Std
            self.averageR2Min += pathResult.R2Min

    def takeAverages(self) -> None:
        self.successFactor /= self.nValidPath
        self.averageOffsetMean /= self.nValidPath
        self.averageOffsetStd /= self.nValidPath
        self.averageOffsetMax /= self.nValidPath
        self.averageR2Mean /= self.nValidPath
        self.averageR2Std /= self.nValidPath
        self.averageR2Min /= self.nValidPath

    def getAttrFromAllValidPath(self, attr:str) -> List[Any]:
        if not hasattr(self.pathResults[0], attr):
            raise AttributeError(f'Attribute {attr} does not exist.')

        res = []
        for path in self.pathResults:
            if path.pathSuccessFactor != None:
                res.append(path.__getattribute__(attr))

        return res
