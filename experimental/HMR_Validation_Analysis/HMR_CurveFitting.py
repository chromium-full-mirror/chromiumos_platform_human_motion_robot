from HMR_Data                       import HMR_Point
from HMR_DataAnalysisUtility        import clip
from HMR_EvaluationConfig           import (POLYFIT_MAX_DEGREE, R2_THRESHOLD, ROUNDING_NUMBER_OF_DIGITS)
from typing                         import (Set, Tuple, List)
from abc                            import (ABC, abstractmethod)
from scipy.interpolate              import (splrep, splev)
from numpy.polynomial.polynomial    import (Polynomial, polyval)
from math                           import (sqrt, inf)
from sklearn.metrics                import r2_score


class HMR_CurveFittingBase(ABC):
    @abstractmethod
    def getCurveParam(self, refPointSet) -> None:
        pass

    @abstractmethod
    def evaluate(self, x:float) -> float:
        pass

    def getError(self, refPointSet:Set[Tuple[float, float]], resPointSet:Set[Tuple[float, float]]) -> float:
        if len(resPointSet) == 0:
            return 0

        # Calculate mean squared error
        self.getCurveParam(refPointSet)
        err = 0
        for (x, y) in resPointSet:
            err += (y - self.evaluate(x))**2

        return err/len(resPointSet)

class HMR_SplineCurveFitting(HMR_CurveFittingBase):
    def __init__(self) -> None:
        self.splineInfo = None

    def getCurveParam(self, refPointSet:Set[Tuple[float, float]]) -> None:
        self.__init__()
        n = len(refPointSet)
        xData = [0]*n
        yData = [0]*n
        for i, (x, y) in enumerate(refPointSet):
            xData[i] = x
            yData[i] = y

        self.splineInfo = splrep(xData, yData, k = clip(n - 1, 1, 3), s = n - sqrt(2*n))

    def evaluate(self, x:float) -> float:
        return splev(x, self.splineInfo)

class HMR_NewtonPolynomialCurveFitting(HMR_CurveFittingBase):
    def __init__(self) -> None:
        self.xData = None
        self.coef = None

    def getCurveParam(self, refPointSet:Set[Tuple[float, float]]) -> None:
        self.__init__()
        n = len(refPointSet)
        coef = [[0]*n for _ in range(n)]
        self.xData = [0]*n

        # First column is y coordinate
        for (x, y) in refPointSet:
            self.xData[i] = x
            coef[i][0] = y

        # Calculate divided difference table
        for j in range(1, n):
            for i in range(n - j):
                coef[i][j] = (coef[i + 1][j - 1] - coef[i][j - 1]) / (self.xData[i + j] - self.xData[i])
        self.coef = coef[0]

    def evaluate(self, x:float) -> float:
        # Evaluate newton polynomial at x
        n = len(self.xData) - 1
        y = self.coef[n]
        for k in range(1, n + 1):
            y = self.coef[n - k] + (x - self.xData[n - k])*y
        return y

class HMR_LeastSquareRegressionCurveFitting(HMR_CurveFittingBase):
    # Linear regression over a set of points
    def __init__(self) -> None:
        self.model:Polynomial = None
        self.coef = []
        self.err = 0.0
        self.R2 = 0.0
        self.isInverted = False

    def isSuccess(self):
        return self.R2 >= R2_THRESHOLD

    @staticmethod
    def roundedPolyVal(X:List[float], coef:List[float]) -> List[float]:
        yHat = polyval(X, coef)
        for i, y in enumerate(yHat):
            yHat[i] = round(y, ROUNDING_NUMBER_OF_DIGITS)
        return yHat

    def getCurveParam(self, refPointSet:Set[HMR_Point]) -> None:
        X = [0]*len(refPointSet)
        Y = [0]*len(refPointSet)

        min_x = inf
        max_x = -inf
        min_y = inf
        max_y = -inf

        for i, point in enumerate(refPointSet):
            X[i] = point.coorX
            Y[i] = point.coorY
            min_x = min(min_x, X[i])
            max_x = max(max_x, X[i])
            min_y = min(min_y, Y[i])
            max_y = max(max_y, Y[i])

        self.isInverted = False if (max_x - min_x >= max_y - min_y) else True

        if self.isInverted:
            X, Y = Y, X

        deg = 1
        while (deg <= POLYFIT_MAX_DEGREE):
            self.model = Polynomial.fit(X, Y, deg)
            self.coef = self.model.convert().coef
            self.R2 = r2_score(Y, HMR_LeastSquareRegressionCurveFitting.roundedPolyVal(X, self.coef))
            if self.R2 >= R2_THRESHOLD:
                break
            deg += 1

    def evaluate(self, point:HMR_Point) -> float:
        res = 0
        for k, c in enumerate(self.coef):
            if self.isInverted:
                res += c*point.coorY**k
            else:
                res += c*point.coorX**k
        return res

    def getError(self, refPointSet:Set[HMR_Point], resPointSet:Set[HMR_Point]) -> float:
        if len(resPointSet) == 0:
            return 0

        # Calculate mean squared error
        self.__init__()
        self.getCurveParam(refPointSet)

        self.err = 0.0
        for point in resPointSet:
            if self.isInverted:
                self.err += (point.coorX - self.evaluate(point))**2
            else:
                self.err += (point.coorY - self.evaluate(point))**2

        return self.err

    def getCurveFittingResult(self) -> Tuple:
        return (self.isInverted, self.coef, self.R2, self.err)
