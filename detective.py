#!/usr/bin/python3

"""
identification game
"""

import os
import shutil
from typing import Iterable, List, Optional, Tuple

from util import collection, static, taxonomy
from util.common import titlecase
from util.image import Image, categorize, split, unqualify
from util.metrics import metrics
from util.resource import VersionedResource
from util.similarity import similarity
from util.static import source_root, stylesheet


def get_hashes(images: List[Image]) -> Iterable[str]:
    """cache in a database"""
    for image in images:
        yield image.hashed()


ThumbsTable = List[List[str]]
SimiliarityTable = List[List[int]]
DifficultyTable = List[int]


def table_builder(
    images: List[Image],
) -> Tuple[List[str], ThumbsTable, SimiliarityTable, DifficultyTable]:
    """Build the tables."""
    images = reversed(images)
    all_names, images = _filter_images(images)

    hashes = list(get_hashes(images))
    names = sorted(list(set(all_names)))
    thumbs: ThumbsTable = [[] for _ in names]

    for i, name in enumerate(all_names):
        where = names.index(name)
        if len(thumbs[where]) < 20:
            thumbs[where].append(hashes[i])

    similarity = _similarity_table(names)
    names = [titlecase(n) for n in names]
    diffs = _difficulties(names)

    return names, thumbs, similarity, diffs


def writer() -> None:
    """Write out all the game artifacts"""
    _write_data_js(collection.named(), 'main')

    shutil.copy(
        os.path.join(source_root, 'web', 'game.js'),
        'detective/game.js',
    )

    game = VersionedResource('detective/game.js', 'detective')
    data = VersionedResource('detective/main.js', 'detective')

    with open('detective/index.html', 'w+') as fd:
        html = _html_builder(stylesheet.path, game.path, data.path)
        print(html, file=fd, end='')


# PRIVATE


def _write_data_js(images: List[Image], name: str) -> None:
    """write out the tables to a file"""
    ns, ts, ss, ds = table_builder(images)

    # This saves 100KB of data, ~20% of the total
    ts = str(ts).replace(' ', '')
    ss = str(ss).replace(' ', '')
    ds = str(ds).replace(' ', '')

    with open(f'detective/{name}.js', 'w+') as fd:
        print(f'var {name}_names =', ns, file=fd)
        print(f'var {name}_thumbs =', ts, file=fd)
        print(f'var {name}_similarities =', ss, file=fd)
        print(f'var {name}_difficulties =', ds, file=fd)


def _difficulties(names: List[str]) -> DifficultyTable:
    """get difficulty overrides"""
    lookup = {
        'very easy': 0,
        'easy': 0,
        'moderate': 2,
        'hard': 3,
        'very hard': 4,
    }

    mapping = {}
    for key, values in static.difficulty.items():
        for value in values:
            mapping[value] = lookup[key]

    out = []
    for name in names:
        name = name.lower()
        name = split(categorize(name)).split(' ')[-1]
        out.append(mapping.get(name, 0))
    return out


def _filter_images(images: Iterable[Image]) -> Tuple[List[str], List[Image]]:
    """strip out images that are poor fits for the game
    - multiple subjects
    - vague, like "sponge"
    - no taxonomy, suggesting things like "dive site"
    """
    knowns = set(taxonomy.load_known(exact_only=True))
    all_names = []
    new_images = []

    for image in images:
        # skip old pictures until cleaned up
        if image.directory.startswith('2019-09'):
            continue
        if image.directory.startswith('2017'):
            continue

        # skip bonaire until cleaned up
        if 'Bonaire' in image.directory:
            continue

        # no videos, not sure how that would make sense
        if image.is_video:
            continue

        # take the first subject when there are multiple
        for part in (' with ', ' and '):
            if part in image.name:
                left, _ = image.name.split(part)
                image.name = left

        # no qualified subjects: fish eggs, juvenile rock fish
        simple = image.singular().lower()
        if unqualify(simple) != simple:
            metrics.counter('detective qualified')
            continue

        if simple not in knowns:
            metrics.counter('detective no taxonomy')
            continue

        metrics.counter('detective included')
        all_names.append(simple)
        new_images.append(image)

    return all_names, new_images


def _similarity_table(names: List[str]) -> SimiliarityTable:
    """how alike is every name pair"""
    tree = taxonomy.mapping()
    table: SimiliarityTable = [[] for _ in names]

    for i, name in enumerate(names):
        for j, other in enumerate(names):
            if i == j:
                table[i].append(0)
                continue

            if j > i:
                # should already be done
                continue

            score = similarity(tree[name], tree[other])
            table[i].append(int(score * 100))

    return table


def _html_builder(css: str, game: str, data: str) -> str:
    """Insert dynamic content into the HTML template"""
    desc = 'Scuba diving picture identification game, identify a picture or choose the image for a name'
    return f"""
<!DOCTYPE html>
<html>
    <head>
        <title>Diving Detective</title>
        <link rel="canonical" href="https://diving.anardil.net/detective/" />
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description"
              content="{desc}">
        <link rel="stylesheet" href="/{css}" />
        <link rel="stylesheet" href="/jquery.fancybox.min.css" />
        <script src="/{data}"></script>
        <script src="/{game}"></script>
        <style>
body {{
    max-width: 1080px;
    margin-left: auto;
    margin-right: auto;
    float: none !important;
}}
        </style>
    </head>

    <body>
        <div class="wrapper">
            <div class="title">
                <a href="/timeline/">
                    <h1 class="top switch timeline">📅</h1>
                </a>
                <div class="top buffer"></div>
                <a href="/gallery/">
                    <h1 class="top switch gallery">📸</h1>
                </a>
                <div class="top buffer"></div>
                <a href="/detective/">
                    <h1 class="top switch detective">Detective</h1>
                </a>
                <div class="top buffer"></div>
                <a href="/sites/">
                    <h1 class="top switch sites">🌎</h1>
                </a>
                <div class="top buffer"></div>
                <a href="/taxonomy/">
                    <h1 class="top switch taxonomy">🔬</h1>
                </a>
                <p class="scientific"></p>
            </div>
            <div id="control">
                <select id="game" onchange="choose_game();">
                    <option value="names">Names</option>
                    <option value="images">Images</option>
                </select>
                <div class="scoring">
                    <h3 id="score"></h3>
                    <h3 id="points"></h3>
                </div>
                <select id="difficulty" onchange="choose_game();">
                    <option value=0>Very Easy</option>
                    <option value=1 selected>Easy</option>
                    <option value=2>Moderate</option>
                    <option value=3>Hard</option>
                    <option value=4>Very Hard</option>
                </select>
            </div>

            <div id="correct_outer">
                <h2 id="correct"></h2>
            </div>

            <div class="grid" id="options">
                <div class="choice" id="option0"> </div>
                <div class="choice" id="option1"> </div>
                <div class="choice" id="option2"> </div>
                <div class="choice" id="option3"> </div>
                <div class="choice" id="option4"> </div>
                <div class="choice" id="option5"> </div>
                <div class="choice" id="option6"> </div>
                <div class="choice" id="option7"> </div>

                <div class="top switch skip" onclick="choose_game();">
                    <h4>Skip</h4>
                </div>
            </div>
        </div>

        <script>
            choose_game();
        </script>
    </body>
</html>
"""
