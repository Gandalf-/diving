#!/usr/bin/python3

'''
html generation
'''

import enum
import string
from typing import Any, Dict, List, Optional, Tuple, Type

import locations
from util import collection, grammar, taxonomy, translator, uddf
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
from util.static import search_data_path, search_js, stylesheet

Where = enum.Enum('Where', 'Gallery Taxonomy Sites Timeline Detective')
Side = enum.Enum('Side', 'Left Right')


scripts = """
    <!-- fancybox is excellent, this project is not commercial -->
    <link rel="stylesheet" href="/jquery.fancybox.min.css"/>
    <script src="/jquery-3.6.0.min.js"></script>
    <script src="/jquery.fancybox.min.js" defer></script>

    <script>
    function removeFlip(elem) {
        elem.classList.remove('is-flipped');

        // When 'is-flipped' is removed, we add the 'loop' attribute and start the timer to remove it after 5 seconds.
        const clips = elem.querySelectorAll('video.clip');
        clips.forEach(clip => {
            clip.setAttribute('loop', 'true');
            clip.currentTime = 0;
            clip.play();

            setTimeout(() => {
                clip.removeAttribute('loop');
            }, 7000);
        });
    }

    function flip(elem) {
        const label = 'is-flipped';
        if (elem.classList.contains(label)) {
            removeFlip(elem);
        } else {
            elem.classList.add(label);
            setTimeout(() => {
                if (elem.classList.contains(label)) {
                    removeFlip(elem);
                }
            }, 7000);
        }
    }

    document.addEventListener("DOMContentLoaded", function() {
        const clips = document.querySelectorAll('video.clip');
        clips.forEach(clip => {
            setTimeout(() => {
                clip.removeAttribute('loop');
            }, 7000); // 5 seconds
        });
    });
    </script>
"""

blurb = 'Explore high quality scuba diving pictures'


def title(
    lineage: List[str], where: Where, scientific: Dict[str, Any]
) -> Tuple[str, str]:
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
            'subject\'s common names. Such as anemone, fish, '
            'nudibranch, octopus, sponge.'
        )
    elif display.endswith('Taxonomy'):
        desc = (
            f'{blurb} organized into a tree structure by '
            'subject\'s scientific classification. Such as Arthropoda, '
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


def description(title: str, where: Where) -> str:
    if where == Where.Sites:
        words = locations.where_to_words(title)
        last = words[-1]
        suffix = ''

        if is_date(last):
            suffix = f' on {pretty_date(last)}'
            words = words[:-1]
        else:
            suffix = ', organized by dive site and date'

        if len(words) > 1:
            # Swap the context and site
            body = ' '.join(words[1:]) + f', {words[0]}'
        else:
            body = words[0]

        return f'{blurb} from {body}{suffix}.'

    if where == Where.Gallery:
        more = len(title.split(' ')) > 1
        related = ' and related organisms' if more else ''

        title = grammar.plural(title).replace('Various ', '')
        return f'{blurb} of {title}{related}.'

    if where == Where.Taxonomy:
        words = title.split(' ')
        if len(words) > 1 and words[-2].istitle() and words[-1].islower():
            # ... Genus species
            name = ' '.join(words[-2:])
            return f'{blurb} of {name} and related organisms.'

        return f'{blurb} of members of {title}.'

    assert False, (where, title)


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
        metrics.counter('images without gallery link')
        name_html = f'<p class="top elem nolink">{image.name}</p>'

    return name_html


def image_to_site_html(image: Image, where: Where) -> str:
    '''create the html site link, entry, or nothing for this image'''
    if where == Where.Sites:
        return ''

    site_url = _image_to_sites_link(image)
    return f'<a class="top elem sites" href="{site_url}">{image.site()}</a>'


def html_direct_image(image: Image, where: Where, lazy: bool) -> str:
    if image.is_image:
        return _direct_image_html(image, where, lazy)
    else:
        return _direct_video_html(image, where)


# PRIVATE


def _direct_image_html(image: Image, where: Where, lazy: bool) -> str:
    assert image.is_image
    metrics.counter('html direct images')
    name_html = image_to_name_html(image, where)
    site_html = image_to_site_html(image, where)

    lazy_load = 'loading="lazy"' if lazy else ''
    location = image.location()
    fullsize = image.fullsize()
    thumbnail = image.thumbnail()

    return f"""
    <div class="card" onclick="flip(this);">
        <div class="card_face card_face-front">
            <img height=225 width=300 {lazy_load} alt="{image.name}" src="{thumbnail}">
        </div>
        <div class="card_face card_face-back">
            {name_html}
            {site_html}
            <a class="top elem timeline" data-fancybox="gallery" data-caption="{image.name} - {location}" href="{fullsize}">
            Fullsize Image
            </a>
            <p class="top elem">Close</p>
        </div>
    </div>
    """


def _direct_video_html(image: Image, where: Where) -> str:
    assert image.is_video
    metrics.counter('html direct videos')
    name_html = image_to_name_html(image, where)
    site_html = image_to_site_html(image, where)

    image.location()
    fullsize = image.fullsize()
    thumbnail = image.thumbnail()

    allowed = string.ascii_letters + string.digits
    unique = 'video_' + ''.join(c for c in image.identifier() if c in allowed)

    # disableRemotePlayback is to stop Android from suggesting a cast
    # playsinline is get iOS to play the video at all
    # Safari always chooses the first element regardless of support with autoplay

    return f"""
    <div class="card" onclick="flip(this);">
        <div class="card_face card_face-front">
            <video class="clip" disableRemotePlayback preload playsinline muted autoplay loop height=225 width=300>
                <source src="{thumbnail.replace('.webm', '.mp4')}" type="video/mp4">
                Your browser does not support the HTML5 video tag.
            </video>
        </div>
        <div class="card_face card_face-back">
            {name_html}
            {site_html}
            <a class="top elem timeline" data-fancybox href="#{unique}">
            Full Video
            </a>
            <p class="top elem">Close</p>

            <video controls muted preload="none" id="{unique}" style="display:none;">
                <source src="{fullsize}" type="video/webm">
                <source src="{fullsize.replace('.webm', '.mp4')}" type="video/mp4">
                Your browser does not support the HTML5 video tag.
            </video>
        </div>
    </div>
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


class Title:
    '''Produce the HTML and title for a particular group of pages'''

    def __init__(
        self, where: Where, lineage: List[str], scientific: Dict[str, Any]
    ) -> None:
        self.where = where
        self.lineage = lineage
        self.scientific = scientific

    def run(self) -> Tuple[str, str]:
        '''Produce html, path'''
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
                <h1 class="top">{name}</h1>
            </a>
            """

        html += """
            <div class="top buffer"></div>

            <a href="/gallery/">
                <h1 class="top switch gallery">Gallery</h1>
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
    '''html head and title section for taxonomy pages'''

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
                <h1 class="top switch taxonomy">Taxonomy</h1>
            </a>
            <div class="top buffer"></div>
        """

        # create the buttons for each part of our name lineage
        for i, name in enumerate(self.lineage):
            name = taxonomy.simplify(name)
            partial = self.lineage[: i + 1]
            link = f"/taxonomy/{lineage_to_link(partial, side)}"

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
    '''html head and title section for sites pages'''

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
                <h1 class="top switch sites">Sites</h1>
            </a>
            <div class="top buffer"></div>
        """
        dive_info = None
        name = ""

        if self.is_dive():
            date = self.get_date()
            dive_info = uddf.search(date, self.get_hint())
            name = pretty_date(date)

        # create the buttons for each part of our name lineage
        for i, _name in enumerate(self.lineage):
            if is_date(_name):
                continue

            partial = self.lineage[: i + 1]
            link = f"/sites/{lineage_to_link(partial, Side.Right)}"

            html += f"""
            <a href="{link}">
                <h1 class="top">{strip_date(_name)}</h1>
            </a>
            """

        html += f"""\
        <h3 class="tight">{name}</h3>
        """
        if dive_info:
            html += uddf.dive_info_html(dive_info)
        html += """\
        </div>
        """

        return html, path


def switcher_button(where: Where, long: bool = False) -> str:
    '''Get the switcher button for this site'''
    _timeline = '''
        <a href="/timeline/">
            <h1 class="top switch">{}</h1>
        </a>
    '''
    _gallery = '''
        <a href="/gallery/">
            <h1 class="top switch gallery">{}</h1>
        </a>
    '''
    _detective = '''
        <a href="/detective/">
            <h1 class="top switch detective">{}</h1>
        </a>
    '''
    _sites = '''
        <a href="/sites/">
            <h1 class="top switch sites">{}</h1>
        </a>
    '''
    _taxonomy = '''
        <a href="/taxonomy/">
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
                <input type="text" id="search_bar" placeholder="">
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
        path = sanitize_link(self.where.name.lower() + '/index')

        html = head(display, path, self.where)
        html += spacer.join(parts)
        html += self.sub_line()

        html += '''
        </div>
        '''

        return html, path
