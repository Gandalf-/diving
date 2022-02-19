#!/usr/bin/python3

'''
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
'''

# pylint: disable=too-few-public-methods

import base64
import operator
from datetime import datetime
from collections import Counter

import wikipedia
from apocrypha.client import Client

import taxonomy

db_root = (
    'diving',
    'wikipedia',
)
database = Client()
wikipedia.set_rate_limiting(True)


class bcolors:
    ''' terminal colors '''

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def fetch(subject: str, suggest=True):
    ''' get summary from wikipedia
    '''
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
        value = {
            # utf8 -> bytes -> b64 -> ascii
            'summary': base64.b64encode(page.summary.encode()).decode(),
            'url': page.url,
            'time': now,
        }
        name = page.url.split('/')[-1]
        name = name.replace('_', ' ')
        name = name.lower()
        subject = subject.lower()

        if 'list of ' in name:
            print(name, 'is a list')
            database.append(*db_root, 'invalid', value=subject.lower())
            return

        if subject + ' ' in name or ' ' + subject in name:
            print(name, 'is more specific than', subject)
            database.append(*db_root, 'invalid', value=subject.lower())
            return

        if ' ' in subject and name in subject and name != subject:
            print(name, 'is less specific than', subject)
            database.append(*db_root, 'invalid', value=subject.lower())
            return

        if name != subject:
            # metacarcinus magister -> dungeness crab, just save the later
            print(
                f'{bcolors.WARNING}mapping {subject} to {name}{bcolors.ENDC}'
            )
            database.set(*db_root, 'maps', subject, value=name)

        print('saved', name)
        database.set(*db_root, 'valid', name, value=value)


def lookup(subject: str, update=True, again=True) -> dict:
    ''' get the subject from the database
    '''
    key = subject.lower()
    if key in database.get(*db_root, 'invalid', default=[], cast=list):
        # no page for this name at all
        return {}

    mapped_key = database.get(*db_root, 'maps', key)
    if mapped_key:
        # metacarcinus magister -> dungeness crab
        key = mapped_key

    out = database.get(*db_root, 'valid', key)
    if not out and not update:
        # didn't find it, don't ask wikipedia
        return {}

    if not out and again:
        # didn't find it, do ask wikipedia
        fetch(subject)
        return lookup(subject, update, False)

    out['summary'] = cleanup(base64.b64decode(out['summary']).decode())
    out['subject'] = subject
    return out


def reference(entry: dict, style='apa') -> str:
    ''' reference info
    '''
    url = entry['url']
    url = f'<a href="{url}">{url}</a>'

    now = datetime.fromtimestamp(entry['time'])
    mla_date = now.strftime('%d %B %Y')
    apa_date = now.strftime('%B, %d %Y')

    subject = entry['subject']

    mla = f'"{subject}." Wikipedia, Wikimedia Foundation, {mla_date}, {url}.'
    apa = f'{subject}. Retrieved {apa_date}, from {url}.'

    # https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content
    out = {'mla': mla, 'apa': apa}.get(style)
    return out


def cleanup(text: str) -> str:
    ''' remove artifacts from simplification the wikipedia package does
    '''
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


def paragraphs(text: str, count: int) -> [str]:
    ''' take count number of paragraphs
    '''
    return text.split('\n')[:count]


def lineage_to_names(lineage):
    ''' lineage list to names to look up
    '''
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


def html(name: str) -> (str, str):
    ''' html fit for use by gallery.py
    '''
    reasonable_number_of_characters = 400

    entry = lookup(name, False)
    if not entry:
        return '', ''

    pgs = paragraphs(entry['summary'], 3)
    text = ''

    for paragraph in pgs:
        m = paragraph.encode('ascii', 'xmlcharrefreplace').decode('ascii')
        text += f'<p>{m}</p>'
        if len(text) > reasonable_number_of_characters:
            break

    ref = reference(entry)

    return (
        f'''<div class="info">
    {text}
    <p class="ref">{ref}</p>
    </div>''',
        entry['url'],
    )


def missing_list():
    ''' what subjects are we missing?
    '''
    names = set(taxonomy.mapping().values())
    out = []

    complete = set()
    complete.update(database.keys(*db_root, 'valid'))
    complete.update(database.keys(*db_root, 'maps'))
    complete.update(database.get(*db_root, 'invalid', default=[], cast=list))

    for name in names:
        parts = [p for p in name.split(' ') if p != 'sp']
        if parts[-1].islower():
            # species
            parts[-1] = parts[-2] + ' ' + parts[-1]

        for part in parts:
            if part.lower() in complete:
                continue
            out.append(part)

    # sorted by frequency
    elems = sorted(
        Counter(out).items(), key=operator.itemgetter(1), reverse=True
    )
    return [e for (e, _) in elems]


def check() -> bool:
    ''' should we stop?
    '''
    print('? ', end='')
    i = input()
    if i and i in 'nN':
        return True
    return False


def updater(*missings):
    ''' interactive update

    attempts to do as much as possible automatically. unclear cases will stop
    and ask for confirmation. the ordering is by number of instances available
    in the pictures. ie a missing item with 50 pictures will be fetched before
    another with 5

    so you can run this as long as your interest holds, get the largest impact
    for your time, and continue later
    '''
    if not missings:
        missings = missing_list()

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
        i = input()
        if i and i in 'nid':
            database.append(*db_root, 'invalid', value=missing.lower())

            key = missing
            mapped = database.get(*db_root, 'maps', missing.lower())
            if mapped:
                database.delete(*db_root, 'maps', missing.lower())
                key = mapped
            database.delete(*db_root, 'valid', key)
            print('removed')


def link(subject, title):
    ''' manually link a subject name (taxonomy) to a page
    '''
    subject = subject.lower()
    title = title.lower()
    fetch(title, False)

    if subject != title:
        print('linking', subject, 'to', title)
        database.set(*db_root, 'maps', subject, value=title)

    database.remove(*db_root, 'invalid', value=subject)
