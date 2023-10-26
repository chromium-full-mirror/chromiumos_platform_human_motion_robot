from HMR_Data                   import (HMR_Point, HMR_TestCase)
from typing                     import (Tuple, Dict, Callable, Set)
from math                       import (sqrt, copysign, acos, log, log2, pi)
from collections                import Counter


def l2CoorNorm(p1:HMR_Point, p2:HMR_Point) -> float:
    res = sqrt((p1.coorX - p2.coorX)**2 + (p1.coorY - p2.coorY)**2)
    return res

def sign(val:float) -> float:
    return copysign(1, val)

def rotateAnti90About(origin:HMR_Point) -> Tuple[float]:
    # Exapnsion of R*(p2 - p1) + p1
    # R = 2D anti 90 degree rotation matrix
    # direction = p2 - p1
    return (-origin.direction[1] + origin.coorX, origin.direction[0] + origin.coorY)

def crossProduct(lineStart:HMR_Point, lineEnd:HMR_Point, pt:HMR_Point) -> float:
    # if return 0, pt is colinear with the line
    # if return > 0, pt is on the left side
    # (or above the line if the line is horizontal)
    # if return < 0, pt is on the right side
    # (or below the line if the line is horizontal)
    return (lineEnd.coorX - lineStart.coorX)*(pt.coorY - lineStart.coorY)\
        - (lineEnd.coorY - lineStart.coorY)*(pt.coorX - lineStart.coorX)

def vectorNorm(vec:Tuple[float]) -> float:
    result = 0
    for v in vec:
        result += v**2
    return sqrt(result)

def dotProduct(vec1:Tuple[float], vec2:Tuple[float]) -> float:
    if len(vec1) != len(vec2):
        raise ValueError('Dimension is not the same.')

    result = 0
    for (v1, v2) in zip(vec1, vec2):
        result += v1*v2
    return result

def clip(value:float, min_value:float, max_value:float) -> float:
    if min_value > max_value:
        raise ValueError(f'min value: {min_value} > max value {max_value}')
    return max(min(value, max_value), min_value)

def cosineSimilarity(vec1:Tuple[float], vec2:Tuple[float]) -> float:
    # cos(theta) = Dot(vec(A), vec(B))/(||vec(A)||*||vec(B)||)
    dotProd = dotProduct(vec1, vec2)
    if dotProd == 0:
        return 0

    v1Norm = vectorNorm(vec1)
    v2Norm = vectorNorm(vec2)
    return clip(dotProd/(v1Norm*v2Norm), -1.0, 1.0)

def angularSimilarity(vec1:Tuple[float], vec2:Tuple[float]) -> float:
    # 1 - acos(cosine Similarity) / pi
    cosSim = cosineSimilarity(vec1, vec2)
    return 1 - acos(cosSim)/pi

def cubicSimilarity(vec1:Tuple[float], vec2:Tuple[float]) -> float:
    # 0.5 + 0.25x + 0.25x^3
    cosSim = cosineSimilarity(vec1, vec2)
    return 0.5 + 0.25*cosSim + 0.25*cosSim**3

def angleBetweenTwoVectors(vec1:Tuple[float], vec2:Tuple[float]) -> float:
    cosSim = cosineSimilarity(vec1, vec2)
    return acos(cosSim)

def getFreqDistribution(testCase:HMR_TestCase, attr:str) -> Dict[int, float]:
    fDist = Counter()
    for path in testCase.paths:
        curr = path.getStart()
        while curr != path.points_tail:
            if not hasattr(curr, attr):
                raise ValueError('No such attribute.')

            fDist[int(getattr(curr, attr))] += 1
            curr = curr.next
    return fDist

def getProbDistribution(fDist:Dict[int, float], size:int) -> Dict[int, float]:
    pDist = fDist
    for x, freq in pDist.items():
        pDist[x] = freq/size
    return pDist

def KLDivergence(refTestCase:HMR_TestCase, resTestCase:HMR_TestCase, attr:str) -> float:
    refFDist = getFreqDistribution(refTestCase, attr)
    resFDist = getFreqDistribution(resTestCase, attr)
    refPDist = getProbDistribution(refFDist, refTestCase.length)
    resPDist = getProbDistribution(resFDist, resTestCase.length)
    return _KLDivergence(resPDist, refPDist)

def _KLDivergence(pDist1:Dict[int, float], pDist2:Dict[int, float], logFunc:Callable = log) -> float:
    res = 0
    maxVal = max(max(pDist1.keys()), max(pDist2.keys()))
    # KL(P||Q) = SUM(p(x)log(p(x)/q(x))
    # TODO: How to handle the case where pmf exists in P but not Q
    for x in range(maxVal + 1):
        if pDist1[x] != 0 and pDist2[x] != 0:
            res += pDist1[x]*logFunc(pDist1[x]/pDist2[x])
    return res

def JSDivergence(refTestCase:HMR_TestCase, resTestCase:HMR_TestCase, attr:str) -> float:
    refFDist = getFreqDistribution(refTestCase, attr)
    resFDist = getFreqDistribution(resTestCase, attr)
    mixFDist = refFDist + resFDist
    refPDist = getProbDistribution(refFDist, refTestCase.length)
    resPDist = getProbDistribution(resFDist, resTestCase.length)
    mixPDist = getProbDistribution(mixFDist, refTestCase.length + resTestCase.length)
    return _JSDivergence(refPDist, resPDist, mixPDist)

def _JSDivergence(pDist1:Dict[int, float], pDist2:Dict[int, float], mixPDist:Dict[int, float]) -> float:
    return 0.5*(_KLDivergence(pDist1, mixPDist, log2) + _KLDivergence(pDist2, mixPDist, log2))

def getCenterOfMass(pointSet:Set[HMR_Point]) -> Tuple[float]:
    X_com = 0
    Y_com = 0
    for pt in pointSet:
        X_com += pt.coorX
        Y_com += pt.coorY
    return (X_com/len(pointSet), Y_com/len(pointSet))

def getOffset(refPointSet:Set[HMR_Point], resPointSet:Set[HMR_Point]) -> float:
    refX_com, refY_com = getCenterOfMass(refPointSet)
    resX_com, resY_com = getCenterOfMass(resPointSet)
    return sqrt((refX_com - resX_com)**2 + (refY_com - resY_com)**2)
