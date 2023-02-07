
from readerwriterlock import rwlock
from collections import defaultdict
from copy import deepcopy

class DataBus:
    def __init__(self, busname= "unnamed") -> None:
        self.message = defaultdict(set)
        self.lock = rwlock.RWLockWriteD()
    
    def read_data(self) -> dict:
        with self.lock.gen_rlock():
            message = deepcopy(self.message)
        return message

    def write_data(self, message) -> None:
        with self.lock.gen_wlock():
            self.message = message