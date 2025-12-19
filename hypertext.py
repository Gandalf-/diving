#!/usr/bin/python3

"""
html generation
"""

import enum
import html as html_module
import string
from typing import Any, Dict, List, Optional, Tuple, Type

import locations
from util import collection, grammar, log, taxonomy, translator
from util.common import (
    flatten,
    is_date,
    pretty_date,
    sanitize_link,
    strip_date,
    titlecase,
)
from util.image import Image, categorize, split, uncategorize
from util.metrics import metrics
from util.static import search_data_path, search_js, stylesheet, video_js

Where = enum.Enum('Where', 'Gallery Taxonomy Sites Timeline Detective')
Side = enum.Enum('Side', 'Left Right')


scripts = (
    """
    <!-- fancybox is excellent, this project is not commercial -->
    <link rel="stylesheet" href="/jquery.fancybox.min.css"/>
    <script src="/jquery-3.6.0.min.js" defer></script>
    <script src="/jquery.fancybox.min.js" defer></script>
    <script>
    // Cross-page prefetch tracking using sessionStorage
    const STORAGE_KEY = 'diving_prefetched_urls';
    const prefetchedUrls = new Set(JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]'));

    function prefetchPage(url) {
        if (prefetchedUrls.has(url)) return;
        prefetchedUrls.add(url);

        // Persist to sessionStorage for cross-page tracking
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...prefetchedUrls]));

        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
    }

    document.addEventListener('DOMContentLoaded', function() {
        const path = window.location.pathname;

        // Only prefetch on gallery, taxonomy, and sites pages
        if (path.startsWith('/gallery') || path.startsWith('/taxonomy') || path.startsWith('/sites')) {
            // Select all internal links in title navigation and image grid
            const links = document.querySelectorAll('.title a[href^="/"], .image a[href^="/"]');

            links.forEach(link => {
                // Small delay to not block page rendering
                setTimeout(() => {
                    prefetchPage(link.href);
                }, 100);
            });

            console.log(`Prefetching ${links.length} pages (${prefetchedUrls.size} total tracked)`);
        }

        // Fancybox: enable HTML in captions
        if (typeof $.fancybox !== 'undefined') {
            $.fancybox.defaults.caption = function(instance, item) {
                return item.opts.$orig ? item.opts.$orig.attr('data-caption') : '';
            };
        }

        // Autofocus search on desktop only (avoid keyboard popup on mobile)
        const searchBar = document.getElementById('search-bar');
        if (searchBar && window.innerWidth > 768) {
            searchBar.focus();
        }
    });
    </script>
"""
    + f"""
    <script src="/{video_js.path}" defer></script>
"""
)

blurb = 'Explore high quality scuba diving pictures'


def title(lineage: List[str], where: Where, scientific: Dict[str, Any]) -> Tuple[str, str]:
    """html head and target path"""
    if not lineage:
        impl: Type[Title] = TopTitle
    else:
        assert lineage
        impl = {
            Where.Gallery: GalleryTitle,
            Where.Taxonomy: TaxonomyTitle,
            Where.Sites: SitesTitle,
        }[where]

    html, path = impl(where, lineage, scientific).run()
    return html, path + '.html'


def head(display: str, path: str, where: Where) -> str:
    """top of the document"""
    if display.endswith('Gallery'):
        desc = (
            f'{blurb} organized into a tree structure by '
            "subject's common names. Such as anemone, fish, "
            'nudibranch, octopus, sponge.'
        )
    elif display.endswith('Taxonomy'):
        desc = (
            f'{blurb} organized into a tree structure by '
            "subject's scientific classification. Such as Arthropoda, "
            'Cnidaria, Mollusca.'
        )
    elif display.endswith('Sites'):
        sites = locations.site_list()
        desc = f'{blurb} from {sites} organized into a tree structure by dive site.'

    elif display.endswith('Timeline'):
        desc = f'{blurb} organized into a timeline by location'

    else:
        desc = description(display, where)

    assert '.html' not in path, path
    path = path.replace('index', '')
    canonical = f'https://diving.anardil.net/{path}'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <title>{display}</title>
        <link rel="canonical" href="{canonical}"/>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name=description content="{desc}">
        <link rel="stylesheet" href="/{stylesheet.path}"/>
      </head>
      <body>
      <div class="wrapper">
      <div class="title">
      """


def _description_sites(title: str) -> str:
    words = locations.where_to_words(title)
    last = words[-1]

    if is_date(last):
        suffix = f' on {pretty_date(last)}'
        words = words[:-1]
    else:
        suffix = ', organized by dive site and date'

    body = ' '.join(words[1:]) + f', {words[0]}' if len(words) > 1 else words[0]
    return f'{blurb} from {body}{suffix}.'


def _description_gallery(title: str) -> str:
    more = len(title.split(' ')) > 1
    related = ' and related organisms' if more else ''
    title = grammar.plural(title).replace('Various ', '')
    return f'{blurb} of {title}{related}.'


def _description_taxonomy(title: str) -> str:
    words = title.split(' ')
    if len(words) > 1 and words[-2].istitle() and words[-1].islower():
        name = ' '.join(words[-2:])
        return f'{blurb} of {name} and related organisms.'
    return f'{blurb} of members of {title}.'


_DESCRIPTION_DISPATCH = {
    Where.Sites: _description_sites,
    Where.Gallery: _description_gallery,
    Where.Taxonomy: _description_taxonomy,
}


def description(title: str, where: Where) -> str:
    handler = _DESCRIPTION_DISPATCH.get(where)
    assert handler, (where, title)
    return handler(title)


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


def html_direct_image(image: Image, where: Where, lazy: bool) -> str:
    if image.is_image:
        return _direct_image_html(image, where, lazy)
    else:
        return _direct_video_html(image, where)


# PRIVATE


def _direct_image_html(image: Image, where: Where, lazy: bool) -> str:
    assert image.is_image
    metrics.counter('html direct images')

    lazy_load = 'loading="lazy"' if lazy else ''
    fullsize = image.fullsize()
    thumbnail = image.thumbnail()
    caption = html_module.escape(_caption_html(image, where), quote=True)

    return f"""
    <a class="thumb" data-fancybox="gallery" data-caption="{caption}" href="{fullsize}">
        <img class="zoom" height=225 width=300 {lazy_load} alt="{image.name}" src="{thumbnail}">
    </a>
    """


def _direct_video_html(image: Image, where: Where) -> str:
    assert image.is_video
    metrics.counter('html direct videos')

    fullsize = image.fullsize()
    thumbnail = image.thumbnail()
    caption = html_module.escape(_caption_html(image, where), quote=True)

    allowed = string.ascii_letters + string.digits
    unique = 'video_' + ''.join(c for c in image.identifier() if c in allowed)

    # disableRemotePlayback is to stop Android from suggesting a cast
    # playsinline is get iOS to play the video at all

    return f"""
    <a class="thumb" aria-label="{image.name} video" data-fancybox="gallery" data-caption="{caption}" href="#{unique}">
        <video class="video" height=225 width=300
          disableRemotePlayback preload playsinline muted loop>
            <source src="{thumbnail}" type="video/mp4">
        </video>
    </a>
    <video controls muted preload="none" id="{unique}" style="display:none;">
        <source src="{fullsize}" type="video/mp4">
    </video>
    """


def _image_to_gallery_link(image: Image) -> Optional[str]:
    """get the /gallery link

    there could be mulitple subjects in this image, just take the first for now
    """
    first = next(collection.expand_names([image]))
    name = first.simplified()

    if name not in collection.all_valid_names():
        return None

    page = sanitize_link(first.normalized())
    return f'/gallery/{page}'


def _image_to_sites_link(image: Image) -> str:
    """get the /sites/ link"""
    when, where = image.location().split(' ', 1)
    return locations.sites_link(when, where)


def _caption_html(image: Image, where: Where) -> str:
    """Generate HTML caption for Fancybox with clickable links."""
    parts = []

    # Name - always show as gallery link (green) if available
    gallery_url = _image_to_gallery_link(image)
    if gallery_url:
        escaped_name = html_module.escape(image.name)
        parts.append(f'<a class="caption-gallery" href="{gallery_url}">{escaped_name}</a>')
    else:
        parts.append(f'<span class="caption-name">{html_module.escape(image.name)}</span>')

    # Location - always show as site link (orange)
    site_url = _image_to_sites_link(image)
    escaped_site = html_module.escape(image.site())
    parts.append(f'<a class="caption-site" href="{site_url}">{escaped_site}</a>')

    # Date - always show, use pretty_date (grey, non-clickable)
    location = image.location()
    date = location.split(' ', 1)[0]
    parts.append(f'<span class="caption-date">{pretty_date(date)}</span>')

    return ' '.join(parts)


class Title:
    """Produce the HTML and title for a particular group of pages"""

    def __init__(self, where: Where, lineage: List[str], scientific: Dict[str, Any]) -> None:
        self.where = where
        self.lineage = lineage
        self.scientific = scientific

    def run(self) -> Tuple[str, str]:
        """Produce html, path"""
        raise NotImplementedError


class GalleryTitle(Title):
    """html head and title section for gallery pages"""

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
        path = sanitize_link(f'gallery/{_title.lower()}')
        html = head(display, path, Where.Gallery)

        # create the buttons for each part of our name lineage
        for i, name in enumerate(self.lineage):
            if i == 0 and scientific_common_name:
                name = f'<em>{name}</em>'

            partial = self.lineage[i:]
            _link = f'/gallery/{lineage_to_link(partial, side)}'.lower()

            html += f"""
            <a href="{_link}">
                <h1 class="nav-pill">{name}</h1>
            </a>
            """

        html += """
            <div class="nav-pill spacer"></div>

            <a href="/gallery/">
                <h1 class="nav-pill active gallery">Gallery</h1>
            </a>
        """

        if slink:
            html += f"""
            <a href="/taxonomy/{slink}" class="scientific crosslink">{sname}</a>
            </div>
            """
        else:
            metrics.counter('titles in gallery without taxonomy link')
            html += f"""
            <p class="scientific">{sname}</p>
            </div>
            """

        return html, path


class TaxonomyTitle(Title):
    """html head and title section for taxonomy pages"""

    def translate_lineage(self) -> str:
        lineage: List[str] = flatten(word.split(' ') for word in self.lineage)[::-1]

        translated = [translator.translate(name) for name in lineage if name != 'sp.']
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
        path = sanitize_link(f'taxonomy/{_title}')

        html = head(' '.join(self.lineage[-2:]), path, Where.Taxonomy)
        html += """
            <a href="/taxonomy/">
                <h1 class="nav-pill active taxonomy">Taxonomy</h1>
            </a>
            <div class="nav-pill spacer"></div>
        """

        # create the buttons for each part of our name lineage
        for i, name in enumerate(self.lineage):
            name = taxonomy.simplify(name)
            partial = self.lineage[: i + 1]
            link = f'/taxonomy/{lineage_to_link(partial, side)}'

            html += f"""
            <a href="{link}">
                <h1 class="nav-pill">{name}</h1>
            </a>
            """

        # check for common name for taxonomy
        name = ''
        history = ' '.join(self.lineage).split(' ')

        while history and not name:
            name = self.scientific.get(' '.join(history), '')
            history = history[:-1]

        name = titlecase(name)
        link = split(categorize(name.lower()))
        link = sanitize_link(link)
        english = self.translate_lineage()

        if link:
            html += f"""
            <a href="/gallery/{link}" class="scientific crosslink">{name}</a>
            <p class="scientific">{english}</p>
            </div>
            """
        else:
            metrics.counter('titles in taxonomy without gallery link')
            assert not name, name
            html += f"""
            <p class="scientific">{english}</p>
            </div>
            """

        return html, path


class SitesTitle(Title):
    """html head and title section for sites pages"""

    def is_dive(self) -> bool:
        *_, last = ' '.join(self.lineage).split(' ')
        return is_date(last)

    def get_date(self) -> str:
        *_, last = ' '.join(self.lineage).split(' ')
        assert is_date(last), last
        return last

    def get_hint(self) -> str:
        last = self.lineage[-1]
        if ' ' in last:
            *parts, _ = last.split(' ')
            return ' '.join(parts)

        return self.lineage[-2]

    def run(self) -> Tuple[str, str]:
        _title = ' '.join(self.lineage)
        path = sanitize_link(f'sites/{_title}')

        html = head(_title, path, Where.Sites)
        html += """
            <a href="/sites/">
                <h1 class="nav-pill active sites">Sites</h1>
            </a>
            <div class="nav-pill spacer"></div>
        """
        dive_info = None
        site_info = None
        name = ''

        if self.is_dive():
            date = self.get_date()
            dive_info = log.search(date, self.get_hint())
            name = pretty_date(date)
        else:
            years = locations.find_year_range(self.lineage)
            site_info = f'<p class="center">{years}</p>'

        # create the buttons for each part of our name lineage
        for i, _name in enumerate(self.lineage):
            if is_date(_name):
                continue

            partial = self.lineage[: i + 1]
            link = f'/sites/{lineage_to_link(partial, Side.Right)}'

            html += f"""
            <a href="{link}">
                <h1 class="nav-pill">{strip_date(_name)}</h1>
            </a>
            """

        html += f"""\
        <h3 class="center">{name}</h3>
        """
        if dive_info:
            html += log.dive_info_html(dive_info)
        if site_info:
            html += site_info
        html += """\
        </div>
        """

        return html, path


def switcher_button(where: Where, long: bool = False) -> str:
    """Get the switcher button for this site"""
    _timeline = """
        <a href="/timeline/">
            <h1 class="nav-pill active">{}</h1>
        </a>
    """
    _gallery = """
        <a href="/gallery/">
            <h1 class="nav-pill active gallery">{}</h1>
        </a>
    """
    _detective = """
        <a href="/detective/">
            <h1 class="nav-pill active detective">{}</h1>
        </a>
    """
    _sites = """
        <a href="/sites/">
            <h1 class="nav-pill active sites">{}</h1>
        </a>
    """
    _taxonomy = """
        <a href="/taxonomy/">
            <h1 class="nav-pill active taxonomy">{}</h1>
        </a>
    """
    return {
        Where.Timeline: _timeline,
        Where.Gallery: _gallery,
        Where.Detective: _detective,
        Where.Sites: _sites,
        Where.Taxonomy: _taxonomy,
    }[where].format(long_name(where) if long else short_name(where))


def long_name(where: Where) -> str:
    """Get the full name"""
    return where.name


def short_name(where: Where) -> str:
    """Get the abbreviated switcher button for this site"""
    return {
        Where.Timeline: '📅',
        Where.Gallery: '📸',
        Where.Detective: '🔍',  # '🕵️',
        Where.Sites: '🌎',
        Where.Taxonomy: '🔬',
    }[where]


class TopTitle(Title):
    """
    HTML head and title section for top level pages. The most interesting
    part of this is the switcher, which allows us to move between the sites
    """

    def sub_line(self) -> str:
        if self.where == Where.Timeline:
            return ''

        return f"""
        <div class="search">
            <form class="search-random" action="javascript:;" onsubmit="randomPage()">
                <button type="submit">Random</button>
            </form>
            <form class="search-text" autocomplete="off" action="javascript:;" onsubmit="searcher()">
                <input type="text" id="search-bar" placeholder="">
                <button type="submit">Search</button>
            </form>
        </div>
        <div id="search-results" class="search-results">

        <script src="/{search_data_path}" defer></script>
        <script src="/{search_js.path}" defer></script>
        </div>
        """

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

        spacer = '<div class="nav-pill spacer"></div>\n'
        path = sanitize_link(self.where.name.lower() + '/index')

        html = head(display, path, self.where)
        html += spacer.join(parts)
        html += self.sub_line()

        html += """
        </div>
        """

        return html, path
