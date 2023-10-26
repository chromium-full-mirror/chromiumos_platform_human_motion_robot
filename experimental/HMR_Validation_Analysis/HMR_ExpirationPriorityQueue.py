from HMR_Data       import (HMR_Point, HMR_ExpirationPriorityQueueNode)
from typing         import (Dict, Tuple)
from queue          import PriorityQueue
from collections    import defaultdict


class HMR_ExpirationPriorityQueue():
    def __init__(
        self,
        minPriorityQueue:PriorityQueue[
            Tuple[
                int, # expirationTime
                HMR_ExpirationPriorityQueueNode
            ]
        ] = PriorityQueue(),
        pointToNodeMapping:Dict[
            HMR_Point,
            HMR_ExpirationPriorityQueueNode
        ] = defaultdict()
    ) -> None:
        self.minPriorityQueue = minPriorityQueue
        self.pointToNodeMapping = pointToNodeMapping

    def peek(self) -> Tuple[int, HMR_ExpirationPriorityQueueNode]:
        if self.isEmpty():
            return None, None
        return self.minPriorityQueue.queue[0]

    def addToPQueue(self, point:HMR_Point, expirationTime:int) -> None:
        if self.isInPQueue(point):
            return

        self.pointToNodeMapping[point] = HMR_ExpirationPriorityQueueNode(point, expirationTime)
        self.minPriorityQueue.put((expirationTime, self.pointToNodeMapping[point]))

    def popFromPQueue(self) -> HMR_ExpirationPriorityQueueNode:
        _, node = self.minPriorityQueue.get()
        del self.pointToNodeMapping[node.point]
        return node

    def isEmpty(self) -> bool:
        return True if (len(self.pointToNodeMapping) == 0 and\
        self.minPriorityQueue.empty()) else False

    def isInPQueue(self, point:HMR_Point) -> bool:
        return True if point in self.pointToNodeMapping else False

    def isOnTop(self, point:HMR_Point) -> bool:
        _, topNode = self.peek()
        return True if point == topNode.point else False

    def markRemoved(self, point:HMR_Point) -> None:
        if (self.isInPQueue(point) and\
            not self.pointToNodeMapping[point].hasRemoved()):
            self.pointToNodeMapping[point].remove()

    def removeMarkedPointsFromPQueue(self) -> None:
        # remove all the points marked isRemoved = True
        while not self.isEmpty():
            _, node = self.peek()
            if not node.hasRemoved():
                break
            self.popFromPQueue()

    def peekExpiredPointsFromPQueue(self, step:int) -> HMR_Point:
        # yield all the points that is not removed
        # but has a expiration time < current step
        while not self.isEmpty():
            expirationTime, node = self.peek()
            if expirationTime <= step and not node.hasRemoved():
                yield node.point
            else:
                break
