#!/usr/bin/python3

'''
Check for broken links, misspelled names, and more
'''

import os
import re


def link_check():
    """check the html directory for broken links by extracting all the
    internal links from the written files and looking for those as paths
    """
    for path, link in _find_links():
        if not os.path.exists(link):
            print('broken', link, 'in', path)


# PRIVATE


def _find_links():
    """check the html directory for internal links"""

    def extract_from(fd):
        """get links from a file"""
        for line in fd:
            if 'href' not in line:
                continue

            for link in re.findall(r'href=\"(.+?)\"', line):
                if link.startswith('http'):
                    continue

                link = link[1:]
                yield path, link

    for directory in ('taxonomy', 'gallery', 'sites'):
        for filename in os.listdir(directory):
            if not filename.endswith(".html"):
                continue

            path = os.path.join(directory, filename)
            with open(path) as fd:
                yield from extract_from(fd)
