from time import sleep
from threading import Thread

__all__ = ['RateLimiterThread']

class RateLimiterThread(Thread):
    def __init__(self, requests_per_sec, event):
        super().__init__()
        self.sleep_duration = 1 / requests_per_sec
        self.event = event
    
    def run(self):
        while True:
            try:
                self.event.wait()
                sleep(self.sleep_duration)
                self.event.clear()
            except EOFError:
                return