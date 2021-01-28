import warnings


def warn(*args, **kwargs):
    pass


warnings.warn = warn
from framework import Framework

if __name__ == '__main__':
    framework = Framework()
    framework.what_to_start()
