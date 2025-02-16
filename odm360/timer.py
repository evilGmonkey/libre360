import time
from threading import Event, Thread


class RepeatedTimer:
    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval, function, start_time=None, name=None, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        if start_time is None:
            self.start = time.time()
        else:
            self.start = start_time
        self.event = Event()
        self.thread = Thread(target=self._target, name=name)
        self.thread.start()

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()
        raise Exception("Thread stopped")
