#!/usr/bin/python3

"""
collect information on subjects from wikipedia

we query based on scientific names, but many wikipedia articles are for common
names. a mapping is kept to translate between the two

articles are fuzzy matched on wikipedia's side and might be complete nonsense,
more specific than we asked (genus + species when asking for genus), less
specific (genus when asking for genus + species).

rejected mappings are added to an invalid list in the database that you (the
user) could reconsider at a later time or manually fix with link()

since the content of the article may contain non-ascii characters (greek
letters, etc), the data is base64 encoded before inserted into the database
"""

import base64
import copy
import operator
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import wikipedia

from diving.util import taxonomy
from diving.util.database import database
from diving.util.metrics import metrics

db_root = (
    'diving',
    'wikipedia',
)
wikipedia.set_rate_limiting(True)


class bcolors:
    """terminal colors"""

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def _is_valid_page_name(page_name: str, subject: str) -> tuple[bool, str]:
    """Check if page name is valid. Returns (is_valid, reason)."""
    if 'list of ' in page_name:
        return False, 'is a list'
    if subject + ' ' in page_name or ' ' + subject in page_name:
        return False, 'is more specific than ' + subject
    if ' ' in subject and page_name in subject and page_name != subject:
        return False, 'is less specific than ' + subject
    return True, ''


def _save_page(page: Any, subject: str, timestamp: float) -> None:
    """Process and save a Wikipedia page to the database."""
    name = page.url.split('/')[-1].replace('_', ' ').lower()
    valid, reason = _is_valid_page_name(name, subject)

    if not valid:
        print(name, reason)
        database.append(*db_root, 'invalid', value=subject)
        return

    if name != subject:
        print(f'{bcolors.WARNING}mapping {subject} to {name}{bcolors.ENDC}')
        database.set(*db_root, 'maps', subject, value=name)

    value = {
        'summary': base64.b64encode(page.summary.encode()).decode(),
        'url': page.url,
        'time': timestamp,
    }
    print('saved', name)
    database.set(*db_root, 'valid', name, value=value)


def fetch(subject: str, suggest: bool = True) -> None:
    """get summary from wikipedia"""
    now = datetime.now().timestamp()
    try:
        print('fetching', subject)
        page = wikipedia.page(subject, auto_suggest=suggest)
    except wikipedia.exceptions.PageError:
        print(subject, 'not found')
        database.append(*db_root, 'invalid', value=subject.lower())
    except wikipedia.exceptions.DisambiguationError:
        print(subject, 'ambiguous')
        database.append(*db_root, 'invalid', value=subject.lower())
    else:
        _save_page(page, subject.lower(), now)


def lookup(subject: str, update: bool = True, again: bool = True) -> Dict[str, str]:
    """get the subject from the database"""
    key = subject.lower()

    if is_invalid_subject(key):
        # no page for this name at all
        return {}

    mapped_key = get_mapped_subject(key)
    if mapped_key:
        # metacarcinus magister -> dungeness crab
        key = mapped_key

    out = get_valid_subject(key)
    if not out and not update:
        # didn't find it, don't ask wikipedia
        return {}

    if not out and again:
        # didn't find it, do ask wikipedia
        fetch(subject)
        return lookup(subject, update, False)

    assert out
    out['summary'] = cleanup(base64.b64decode(out['summary']).decode())
    out['subject'] = subject
    return out


def reference(entry: Dict[str, Any], style: str = 'apa') -> str:
    """reference info"""
    url = entry['url']
    uri = url.replace('https://', '')
    url = f'<a href="{url}">{uri}</a>'

    now = datetime.fromtimestamp(entry['time'])
    mla_date = now.strftime('%d %B %Y')
    apa_date = now.strftime('%B, %d %Y')

    subject = entry['subject']

    mla = f'"{subject}." Wikipedia, Wikimedia Foundation, {mla_date}, {url}.'
    apa = f'{subject}. Retrieved {apa_date}, from {url}.'

    # https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content
    out = {'mla': mla, 'apa': apa}[style]
    return out


def cleanup(text: str) -> str:
    """remove artifacts from simplification the wikipedia package does"""
    return (
        text.replace(' ()', '')
        .replace('(, ', '(')
        .replace(' )', ')')
        .replace('  ', ' ')
        .replace(' ,', ',')
        .replace('.', '. ')
        .replace('.  ', '. ')
        .replace(' .', '.')
    )


def paragraphs(text: str, count: int) -> List[str]:
    """take count number of paragraphs"""
    return text.split('\n')[:count]


def lineage_to_names(lineage: List[str]) -> List[str]:
    """lineage list to names to look up"""
    if not lineage:
        return []

    parts = lineage[-1].split(' ')
    if parts[-1].islower():
        if len(parts) == 1 and len(lineage) > 1:
            # species
            parents = lineage[-2].split(' ')
            parts = [parents[-1] + ' ' + lineage[-1]]

        elif len(parts) > 1:
            # genus species
            parts[-2] = parts[-2] + ' ' + parts[-1]
            parts = parts[:-1]

    return parts


def html(name: str) -> Tuple[str, str]:
    """html fit for use by gallery.py"""
    reasonable_number_of_characters = 400

    entry = lookup(name, False)
    if not entry:
        metrics.counter('names without wikipedia information')
        return '', ''

    pgs = paragraphs(entry['summary'], 3)
    text = ''

    for paragraph in pgs:
        m = paragraph.encode('ascii', 'xmlcharrefreplace').decode('ascii')
        if not m:
            continue

        text += f'<p>{m}</p>'
        if len(text) > reasonable_number_of_characters:
            break

    ref = reference(entry)

    return (
        f"""<div class="info">
    {text}
    <p class="ref">{ref}</p>
    </div>""",
        entry['url'],
    )


def missing_list() -> List[str]:
    """what subjects are we missing?"""
    names = set(taxonomy.mapping().values())
    out = []

    complete = set()
    complete.update(database.keys(*db_root, 'valid'))
    complete.update(database.keys(*db_root, 'maps'))
    complete.update(database.get(*db_root, 'invalid'))

    for name in names:
        parts = [p for p in name.split(' ') if p not in ('sp', 'sp.')]
        if parts[-1].islower():
            # species
            parts[-1] = parts[-2] + ' ' + parts[-1]

        for part in parts:
            if part.lower() in complete:
                continue
            out.append(part)

    # sorted by frequency
    elems = sorted(Counter(out).items(), key=operator.itemgetter(1), reverse=True)
    return [e for (e, _) in elems]


def check() -> bool:
    """should we stop?"""
    print('? ', end='')
    i = input()
    if i and i in 'nN':
        return True
    return False


def updater(*targets: str) -> None:
    """interactive update

    attempts to do as much as possible automatically. unclear cases will stop
    and ask for confirmation. the ordering is by number of instances available
    in the pictures. ie a missing item with 50 pictures will be fetched before
    another with 5

    so you can run this as long as your interest holds, get the largest impact
    for your time, and continue later
    """
    if not targets:
        missings = missing_list()
    else:
        missings = list(targets)

    for i, missing in enumerate(missings):
        print(bcolors.OKCYAN, len(missings) - i, missing, bcolors.ENDC)
        entry = lookup(missing)
        if not entry:
            continue

        if missing.lower() not in database.keys(*db_root, 'maps'):
            print('not mapped, continuing')
            continue

        if missing.lower() in entry['summary'].lower():
            print('mapped, but contains the subject')
            continue

        print(paragraphs(entry['summary'], 1)[0])
        print('? ', end='')
        keep = input()
        if keep and keep in 'nid':
            database.append(*db_root, 'invalid', value=missing.lower())

            key = missing
            mapped = database.get(*db_root, 'maps', missing.lower())
            if mapped:
                database.delete(*db_root, 'maps', missing.lower())
                key = mapped
            database.delete(*db_root, 'valid', key)
            print('removed')


def link(subject: str, title: str) -> None:
    """manually link a subject name (taxonomy) to a page"""
    subject = subject.lower()
    title = title.lower()
    fetch(title, False)

    if subject != title:
        print('linking', subject, 'to', title)
        database.set(*db_root, 'maps', subject, value=title)

    database.remove(*db_root, 'invalid', value=subject)


def get_valid_subject(subject: str) -> Dict[str, Any]:
    """get the entry for this valid subject"""
    value = database.get('diving', 'wikipedia', 'valid', subject)
    return copy.deepcopy(value)


def get_mapped_subject(key: str) -> Optional[str]:
    return database.get('diving', 'wikipedia', 'maps', key)


def is_invalid_subject(key: str) -> bool:
    values = database.get('diving', 'wikipedia', 'invalid')
    return key in values
