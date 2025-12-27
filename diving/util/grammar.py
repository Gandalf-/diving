from typing import cast

import inflect

_inflect = inflect.engine()


def singular(noun: str) -> str:
    """return singular version"""

    singular = _inflect.singular_noun(noun.lower())
    noun = cast(str, singular) if singular else noun.lower()

    # fix inflect's mistakes
    for tofix in ('octopu', 'gras', 'fuscu', 'dori'):
        if tofix + 's' in noun:
            continue
        if noun.endswith(tofix) or tofix + ' ' in noun:
            noun = noun.replace(tofix, tofix + 's')

    if noun.endswith('alga'):
        noun += 'e'

    if noun.endswith('greenlin'):
        noun += 'g'

    return noun


def plural(noun: str) -> str:
    """return plural version"""

    ignore = ('algae', 'eelgrass', 'octopus')
    lower = noun.lower()
    if any(lower.endswith(x) for x in ignore):
        return noun

    single_s = ('nudibranch',)
    if any(lower.endswith(x) for x in single_s):
        return noun + 's'

    noun = _inflect.plural_noun(noun)
    return noun
