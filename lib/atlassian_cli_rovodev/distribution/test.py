"""Test packaging of the executable binary."""

from .common import make_portable

if __name__ == "__main__":
    result = make_portable(False)
    if isinstance(result, Exception):
        raise result
    else:
        print("\nExecutable binary packaged and tested. No problem found!")
