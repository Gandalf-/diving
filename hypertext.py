#!/usr/bin/python3

'''
html generation
'''

import enum
import datetime
from typing import Optional, Tuple, List, Dict, Any, Type

import locations

from util.collection import expand_names, all_valid_names
from util.common import (
    is_date,
    flatten,
    strip_date,
    pretty_date,
    fast_exists,
    titlecase,
    sanitize_link,
)
from util.metrics import metrics
from util.static import stylesheet, search_js, search_data_path
from util.image import categorize, uncategorize, split, Image
from util.translator import translate
from util import taxonomy


Where = enum.Enum('Where', 'Gallery Taxonomy Sites Timeline Detective')
Side = enum.Enum('Side', 'Left Right')


scripts = """
    <!-- fancybox is excellent, this project is not commercial -->
    <link rel="stylesheet" href="/jquery.fancybox.min.css"/>
    <script src="/jquery-3.6.0.min.js" defer></script>
    <script src="/jquery.fancybox.min.js" defer></script>

    <script>
    function flip(elem) {
        const label = 'is-flipped';
        if (elem.classList.contains(label)) {
            elem.classList.remove(label);
        } else {
            const seconds = 10;
            elem.classList.add(label);
            setTimeout(function () {
                if (elem.classList.contains(label)) {
                    elem.classList.remove(label);
                }
            }, 1000 * seconds);
        }
    }
    </script>
"""


def title(
    lineage: List[str], where: Where, scientific: Dict[str, Any]
) -> Tuple[str, str]:
    """html head and title section"""
    if not lineage:
        impl: Type[Title] = TopTitle
    else:
        assert lineage
        impl = {
            Where.Gallery: GalleryTitle,
            Where.Taxonomy: TaxonomyTitle,
            Where.Sites: SitesTitle,
        }[where]

    return impl(where, lineage, scientific).run()


def head(_title: str) -> str:
    """top of the document"""
    if _title.endswith('Gallery'):
        desc = (
            'Scuba diving pictures organized into a tree structure by '
            'subject\'s common names. Such as anemone, fish, '
            'nudibranch, octopus, sponge.'
        )
    elif _title.endswith('Taxonomy'):
        desc = (
            'Scuba diving pictures organized into a tree structure by '
            'subject\'s scientific classification. Such as Arthropoda, '
            'Cnidaria, Mollusca.'
        )
    elif _title.endswith('Sites'):
        sites = locations.site_list()
        desc = f'Scuba diving pictures from {sites} organized into a tree structure by dive site.'

    elif _title.endswith('Timeline'):
        desc = 'Scuba diving pictures organized into a timeline and by location'

    else:
        _title = strip_date(_title)
        desc = f'Scuba diving pictures related to {_title}'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <title>{_title}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name=description content="{desc}">
        <link rel="stylesheet" href="/{stylesheet.path}"/>
      </head>
      <body>
      <div class="wrapper">
      <div class="title">
      """


def lineage_to_link(lineage: List[str], side: Side, key: Optional[str] = None) -> str:
    """get a link to this page"""
    if not lineage:
        assert key
        name = key
    else:
        name = ' '.join(lineage)

        if key and side == Side.Left:
            name = f'{key} {name}'

        if key and side == Side.Right:
            name = f'{name} {key}'

    return sanitize_link(name)


def image_to_name_html(image: Image, where: Where) -> str:
    '''create the html gallery link, entry, or nothing for this image'''
    if where in (Where.Gallery, Where.Taxonomy):
        return ''

    name_url = _image_to_gallery_link(image)
    if name_url:
        name_html = f'<a class="top elem gallery" href="{name_url}">{image.name}</a>'
    else:
        metrics.counter('image without gallery link')
        name_html = f'<p class="top elem nolink">{image.name}</p>'

    return name_html


def image_to_site_html(image: Image, where: Where) -> str:
    '''create the html site link, entry, or nothing for this image'''
    if where == Where.Sites:
        return ''

    site_url = _image_to_sites_link(image)
    return f'<a class="top elem sites" href="{site_url}">{image.site()}</a>'


# PRIVATE


def _image_to_gallery_link(image: Image) -> Optional[str]:
    """get the /gallery link

    there could be mulitple subjects in this image, just take the first for now
    """
    first = next(expand_names([image]))
    name = first.simplified()

    if name not in all_valid_names():
        return None

    page = sanitize_link(first.normalized())
    return f'/gallery/{page}.html'


def _image_to_sites_link(image: Image) -> str:
    """get the /sites/ link"""
    when, where = image.location().split(' ', 1)
    return locations.sites_link(when, where)


class Title:
    '''Produce the HTML and title for a particular group of pages'''

    def __init__(
        self, where: Where, lineage: List[str], scientific: Dict[str, Any]
    ) -> None:
        self.where = where
        self.lineage = lineage
        self.scientific = scientific

    def run(self) -> Tuple[str, str]:
        '''Produce html, title'''
        raise NotImplementedError


class GalleryTitle(Title):
    '''html head and title section for gallery pages'''

    def run(self) -> Tuple[str, str]:
        side = Side.Left

        # check for scientific name for gallery
        slink = sname = taxonomy.gallery_scientific(self.lineage, self.scientific)
        sname = taxonomy.simplify(sname)
        if slink.endswith(' sp.'):
            slink = slink.replace(' sp.', '')

        scientific_common_name = slink.lower().endswith(self.lineage[0].lower())

        if scientific_common_name:
            self.lineage = [slink[-len(self.lineage[0]) :]] + [
                titlecase(e) for e in self.lineage[1:]
            ]
        else:
            self.lineage = [titlecase(e) for e in self.lineage]

        _title = ' '.join(self.lineage)
        display = uncategorize(_title)

        slink = sanitize_link(slink)
        html = head(display)

        # create the buttons for each part of our name lineage
        for i, name in enumerate(self.lineage):
            if i == 0 and scientific_common_name:
                name = f'<em>{name}</em>'

            partial = self.lineage[i:]
            _link = f'/gallery/{lineage_to_link(partial, side)}.html'.lower()

            html += f"""
            <a href="{_link}">
                <h1 class="top">{name}</h1>
            </a>
            """

        html += """
            <div class="top buffer"></div>

            <a href="/gallery/index.html">
                <h1 class="top switch gallery">Gallery</h1>
            </a>
        """

        if slink:
            html += f"""
            <a href="/taxonomy/{slink}.html" class="scientific crosslink">{sname}</a>
            </div>
            """
        else:
            metrics.counter('gallery title without taxonomy link')
            html += f"""
            <p class="scientific">{sname}</p>
            </div>
            """

        return html, _title.lower()


class TaxonomyTitle(Title):
    '''html head and title section for taxonomy pages'''

    def translate_lineage(self) -> str:
        lineage: List[str] = flatten(word.split(' ') for word in self.lineage)[::-1]

        translated = [translate(name) for name in lineage if name != 'sp.']
        if lineage[0].islower():
            size = 2
            last = len(self.lineage[-1].split(' '))
            size = max(size, last)

            translated = translated[:size]

        names = []
        for translation in translated:
            if translation in names:
                continue
            names.append(translation)

        assert names, lineage
        return ' '.join(names)

    def run(self) -> Tuple[str, str]:
        _title = ' '.join(self.lineage)
        side = Side.Right

        html = head(' '.join(self.lineage[-2:]))
        html += """
            <a href="/taxonomy/index.html">
                <h1 class="top switch taxonomy">Taxonomy</h1>
            </a>
            <div class="top buffer"></div>
        """

        # create the buttons for each part of our name lineage
        for i, name in enumerate(self.lineage):
            name = taxonomy.simplify(name)
            partial = self.lineage[: i + 1]
            link = f"/taxonomy/{lineage_to_link(partial, side)}.html"

            html += f"""
            <a href="{link}">
                <h1 class="top">{name}</h1>
            </a>
            """

        # check for common name for taxonomy
        name = ""
        history = ' '.join(self.lineage).split(' ')

        while history and not name:
            name = self.scientific.get(' '.join(history), "")
            history = history[:-1]

        name = titlecase(name)
        link = split(categorize(name.lower()))
        link = sanitize_link(link)
        english = self.translate_lineage()

        if link:
            html += f"""
            <a href="/gallery/{link}.html" class="scientific crosslink">{name}</a>
            <p class="scientific">{english}</p>
            </div>
            """
        else:
            metrics.counter('taxonomy title without gallery link')
            assert not name, name
            html += f"""
            <p class="scientific">{english}</p>
            </div>
            """

        return html, _title


class SitesTitle(Title):
    '''html head and title section for sites pages'''

    def run(self) -> Tuple[str, str]:
        display = _title = ' '.join(self.lineage)
        side = Side.Right

        html = head(display)
        html += """
            <a href="/sites/index.html">
                <h1 class="top switch sites">Sites</h1>
            </a>
            <div class="top buffer"></div>
        """

        # create the buttons for each part of our name lineage
        name = ""
        try:
            last = self.lineage[-1]
            if ' ' in last:
                *parts, last = last.split(' ')
                rest = ' '.join(parts)
            else:
                rest = None

            d = datetime.datetime.strptime(last, '%Y-%m-%d')
            assert d

            name = last
            if rest:
                self.lineage = self.lineage[:-1] + [rest]
        except ValueError:
            pass

        for i, _name in enumerate(self.lineage):
            partial = self.lineage[: i + 1]
            link = f"/sites/{lineage_to_link(partial, side)}.html"

            # it's possible that this is the only date available for this location,
            # in which case we want the name to include the location and trim the
            # lineage one more value
            if not fast_exists(link[1:]):
                name = _name + ' ' + name
                continue

            html += f"""
            <a href="{link}">
                <h1 class="top">{_name}</h1>
            </a>
            """

        if ' ' in name:
            rest, last = name.rsplit(' ', maxsplit=1)
            if is_date(last):
                when = pretty_date(last)
                name = f'{rest} - {when}'
        elif is_date(name):
            name = pretty_date(name)

        # ???
        html += f"""
        <h3 class="tight">{name}</h3>
        </div>
        """

        return html, _title


def switcher_button(where: Where, long: bool = False) -> str:
    '''Get the switcher button for this site'''
    _timeline = '''
        <a href="/timeline/index.html">
            <h1 class="top switch">{}</h1>
        </a>
    '''
    _gallery = '''
        <a href="/gallery/index.html">
            <h1 class="top switch gallery">{}</h1>
        </a>
    '''
    _detective = '''
        <a href="/detective/index.html">
            <h1 class="top switch detective">{}</h1>
        </a>
    '''
    _sites = '''
        <a href="/sites/index.html">
            <h1 class="top switch sites">{}</h1>
        </a>
    '''
    _taxonomy = '''
        <a href="/taxonomy/index.html">
            <h1 class="top switch taxonomy">{}</h1>
        </a>
    '''
    return {
        Where.Timeline: _timeline,
        Where.Gallery: _gallery,
        Where.Detective: _detective,
        Where.Sites: _sites,
        Where.Taxonomy: _taxonomy,
    }[where].format(long_name(where) if long else short_name(where))


def long_name(where: Where) -> str:
    '''Get the full name'''
    return where.name


def short_name(where: Where) -> str:
    '''Get the abbreviated switcher button for this site'''
    return {
        Where.Timeline: '📅',
        Where.Gallery: '📸',
        Where.Detective: '🔍',  # '🕵️',
        Where.Sites: '🌎',
        Where.Taxonomy: '🔬',
    }[where]


class TopTitle(Title):
    '''
    HTML head and title section for top level pages. The most interesting
    part of this is the switcher, which allows us to move between the sites
    '''

    def sub_line(self) -> str:
        if self.where == Where.Timeline:
            return ''

        return f'''
        <div class="search">
            <form class="search_random" action="javascript:;" onsubmit="randomPage()">
                <button type="submit">Random</button>
            </form>
            <form class="search_text" autocomplete="off" action="javascript:;" onsubmit="searcher()">
                <input type="text" id="search_bar" placeholder="Copper Rockfish...">
                <button type="submit">Search</button>
            </form>
        </div>
        <div id="search_results" class="search_results">

        <script src="/{search_data_path}" defer></script>
        <script src="/{search_js.path}" defer></script>
        </div>
        '''

    def run(self) -> Tuple[str, str]:
        _title = titlecase(self.where.name)

        display = uncategorize(_title)
        if self.where == Where.Gallery:
            display = titlecase(display)

        carousel = [
            Where.Timeline,
            Where.Gallery,
            Where.Detective,
            Where.Sites,
            Where.Taxonomy,
        ]

        start = carousel.index(self.where)
        indicies = [start - 2, start - 1, start, start + 1, start + 2]
        indicies = [i % len(carousel) for i in indicies]

        parts = [
            switcher_button(carousel[indicies[0]]),
            switcher_button(carousel[indicies[1]]),
            switcher_button(carousel[indicies[2]], long=True),
            switcher_button(carousel[indicies[3]]),
            switcher_button(carousel[indicies[4]]),
        ]

        spacer = '<div class="top buffer"></div>\n'

        html = head(display)
        html += spacer.join(parts)
        html += self.sub_line()

        html += '''
        </div>
        '''

        return html, _title
