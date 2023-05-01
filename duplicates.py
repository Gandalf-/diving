#!/usr/bin/env python3

'''
There are a number of directories that all have files named in the pattern
<number> - <name>.<ext>.  This script will find all the duplicates by
considering the number only.
'''

import os
import re
import sys
from collections import defaultdict


def main() -> None:
    '''Find the duplicates, convert this to a verify check later'''
    if len(sys.argv) != 2:
        print("Usage: duplicates.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print("Not a directory: {}".format(directory))
        sys.exit(1)

    pattern = re.compile(r"(\d+) - (.*)\..*")

    duplicates = defaultdict(list)
    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            number = match.group(1)
            name = match.group(2)
            duplicates[number].append(name)

    for number, names in duplicates.items():
        if len(names) > 1:
            print("{}: {}".format(number, ", ".join(names)))


if __name__ == '__main__':
    main()
