from time import time


class Timer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        
    def start(self):
        self.start_time = time()
        
    def stop(self):
        self.end_time = time()
        
    @property
    def elapsed(self) -> float:
        if self.start_time is None or self.end_time is None:
            raise ValueError("Timer has not been started and stopped properly.")
        return self.end_time - self.start_time
    
    def reset(self):
        self.start_time = None
        self.end_time = None