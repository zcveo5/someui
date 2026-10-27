import datetime
import sys
from pathlib import Path

LOG_DIR_NAME = 'someUiLogging'
LOG_DIR = Path(__file__).absolute().parent / LOG_DIR_NAME
DEFAULT_FMT = '[{name} {time}] {msg}'


class Logger:
    def __init__(self, name, f=sys.stdout, fmt=DEFAULT_FMT):
        self.fmt = fmt
        self.name = name
        self.f = f
        self.level = 0

    @classmethod
    def make_from_file(cls, name, fmt=DEFAULT_FMT):
        LOG_DIR.mkdir(exist_ok=True)
        fp = LOG_DIR / f'{name}.log'
        return cls(name, fp.open('w'), fmt)

    def log(self, level, msg):
        if level < self.level:
            return
        self.f.write(self.fmt.format(name=self.name, time=datetime.datetime.now().strftime('%H:%M:%S'), msg=msg) + '\n')
        self.f.flush()

    def debug(self, msg):
        self.log(0, msg)

    def info(self, msg):
        self.log(10, msg)

    def warning(self, msg):
        self.log(20, msg)

    def error(self, msg):
        self.log(30, msg)