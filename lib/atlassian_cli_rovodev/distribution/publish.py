"""Package and publish executable binary for the host platform."""

import json

from .common import make_portable

if __name__ == "__main__":
    result = make_portable(True)
    if isinstance(result, Exception):
        raise result
    else:
        print("\nExecutable binary created succesfully!")
        print()
        print("\tFolder: ", result.portable_path)
        print("\tArchive: ", result.portable_path + ".zip")
        print()
        print(json.dumps(result._asdict()))
