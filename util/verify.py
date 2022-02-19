#!/usr/bin/python3

'''
Check for broken links, misspelled names, and more
'''

import os
import re


def advisory_checks():
    ''' informational '''
    try:
        required_checks()
    except AssertionError as e:
        print(e)


def required_checks():
    ''' must pass '''
    _important_files_exist()
    _link_check()


# PRIVATE


def _important_files_exist():
    ''' basic sanity '''
    required = ['index.html', 'style.css', 'favicon.ico']
    required += [
        f'{site}/index.html'
        for site in ['sites', 'detective', 'taxonomy', 'timeline', 'gallery']
    ]
    required += [
        'gallery/nudibranch.html',
        'gallery/giant-pacific-octopus.html',
        'taxonomy/Animalia.html',
        'taxonomy/Animalia-Mollusca-Gastropoda-Nudibranchia.html',
        'sites/Bonaire.html',
        'sites/Washington-Sund-Rock.html',
        'detective/data.js',
        'detective/game.js',
        'timeline/2021-12-16-Fort-Worden.html',
        'timeline/2020-09-04-Metridium.html',
    ]
    for fpath in required:
        assert os.path.exists(fpath), f'required file {fpath} does not exist'


def _link_check():
    """check the html directory for broken links by extracting all the
    internal links from the written files and looking for those as paths
    """
    for path, link in _find_links():
        if not os.path.exists(link):
            print('broken', link, 'in', path)


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


if __name__ == '__main__':
    required_checks()
