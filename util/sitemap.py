import os

from typing import Iterable

from bs4 import BeautifulSoup

web_root = 'https://diving.anardil.net'

main_header = '''
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
'''

main_footer = '''
</urlset>
'''


def html_pages() -> Iterable[str]:
    sections = ('taxonomy', 'gallery', 'sites')

    for section in sections:
        for fname in os.listdir(section):
            if not fname.endswith('.html'):
                continue

            yield f'{section}/{fname}'


def image_xml(content: str, fpath: str) -> Iterable[str]:
    soup = BeautifulSoup(content, 'html.parser')
    for i, img in enumerate(soup.find_all('img')):
        src = img.get('src')

        yield '<image:image>'
        yield f'<image:loc>{web_root}{src}</image:loc>'
        yield '</image:image>'

    assert i < 1000, f'too many images in {fpath}'


def process_page(fpath: str) -> Iterable[str]:
    yield '<url>'
    yield f'<loc>{web_root}/{fpath}</loc>'

    with open(fpath) as fd:
        yield from image_xml(fd.read(), fpath)

    yield '</url>'


def sitemap() -> Iterable[str]:
    yield main_header.strip('\n')

    for i, page in enumerate(html_pages()):
        if i % 100 == 0:
            print('.', end='', flush=True)
        yield from process_page(page)
    print()

    yield main_footer.strip('\n')


def main() -> None:
    with open('sitemap.xml', 'w') as fd:
        for line in sitemap():
            fd.write(line)
            fd.write('\n')


if __name__ == '__main__':
    main()
