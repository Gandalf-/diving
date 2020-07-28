#!/usr/bin/python3

'''
search through diving pictures to produce a 'taxonomy tree', then convert that
tree into HTML pages for diving.anardil.net
'''

import hashlib
import sys
import os

from multiprocessing import Pool
import inflect

# pylint: disable=too-many-locals

inflect = inflect.engine()

root = "/mnt/zfs/Media/Pictures/Diving"

categories = {
    "fish": (
        "basslet",
        "blue tang",
        "flounder",
        "cero",
        "goby",
        "greenling",
        "grunt",
        "gunnel",
        "grouper",
        "lingcod",
        "midshipman",
        "perch",
        "rock beauty",
        "sculpin",
        "sculpin",
        "sole",
        "spotted drum",
        "tarpon",
        "tomtate",
        "war bonnet",
    ),
    "crab": ("reef spider",),
    "nudibranch": ("sea lemon", "dorid", "dendronotid"),
    "anemone": ("zoanthid",),
    "coral": ("sea pen", "sea whip", "sea rod"),
}


class Image:
    ''' container for a diving picture '''

    def __init__(self, label, directory):
        self.label = label
        label, _ = os.path.splitext(label)

        if " - " in label:
            number, name = label.split(" - ")
        else:
            number = label
            name = ""

        self.name = name
        self.number = number
        self.directory = directory

    def __repr__(self):
        return ", ".join(
            [
                # self.number,
                self.name,
                # self.directory
            ]
        )

    def path(self):
        ''' where this is on the file system
        '''
        return os.path.join(root, self.directory, self.label)

    def fullsize(self):
        ''' URI of full size image '''
        return "https://public.anardil.net/media/diving/{d}/{i}".format(
            d=self.directory, i=self.label,
        )

    def hash(self):
        ''' hash a file the same way indexer does, so we can find it's thumbnail
        '''
        sha1 = hashlib.sha1()

        with open(self.path(), "rb") as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha1.update(data)

        return sha1.hexdigest()

    def normalized(self):
        ''' lower case, remove plurals, split and expand '''
        # simplify name
        name = inflect.singular_noun(self.name.lower())
        name = name or self.name.lower()

        # fix inflect's mistakes
        for tofix in ("octopu", "gras", "fuscu"):
            if tofix in name and tofix + "s" not in name:
                name = name.replace(tofix, tofix + "s")

        if name.endswith("alga"):
            name += "e"

        # split 'rockfish' to 'rock fish'
        for split in ("fish", "coral", "ray"):
            if (
                name != split
                and name.endswith(split)
                and not name.endswith(" " + split)
            ):
                name = name.replace(split, " " + split)

        # categorization
        for category, values in categories.items():
            for value in values:
                if name.endswith(value):
                    name += " " + category

        return name


def flatten(xs):
    ''' [[a]] -> [a] '''
    return [item for sublist in xs for item in sublist]


def listing():
    """ a list of all dive picture folders available """
    return [d for d in os.listdir(root) if not d.startswith(".")]


def delve(directory):
    """ create an Image object for each picture in a directory """
    path = os.path.join(root, directory)
    return [
        Image(o, directory) for o in os.listdir(path) if o.endswith(".jpg")
    ]


def collect():
    """ run delve on all dive picture folders """
    return [delve(d) for d in listing()]


def named():
    ''' all named images from all directories '''
    return flatten([[y for y in z if y.name] for z in collect()])


def expand_names(images):
    """ split out `a and b` into separate elements """
    result = []

    for image in images:
        for split in (" with ", " and "):

            if split not in image.name:
                continue

            left, right = image.name.split(split)

            clone = Image(image.label, image.directory)
            clone.name = left
            image.name = right
            result.append(clone)

        result.append(image)

    return result


def make_tree(images):
    """ make a nested dictionary by words
    """
    out = {}
    for image in images:
        name = image.normalized()
        words = name.split(" ")[::-1]

        sub = out
        for word in words:
            sub.setdefault(word, {})
            sub = sub[word]

        sub.setdefault("data", [])
        sub["data"].append(image)

    return out


def tree_size(tree):
    ''' number of leaves '''
    if not isinstance(tree, dict):
        return len(tree)

    return sum(tree_size(c) for c in tree.values())


def pruner(tree, too_few=5):
    """ remove top level keys with too few elements
    """
    to_remove = []

    for key, value in tree.items():
        if tree_size(value) <= too_few:
            to_remove.append(key)

    for remove in to_remove:
        # print('pruned', remove)
        tree.pop(remove)

    return tree


def compress(tree):
    """ look for sub trees with no 'data' key, which can be squished up a level
    """
    assert isinstance(tree, dict), tree

    for key, value in list(tree.items()):

        if not isinstance(value, dict):
            continue

        if "data" not in value and len(value.keys()) == 1:
            v = tree.pop(key)
            s = list(v.keys())[0]
            new_key = s + " " + key
            tree[new_key] = compress(v[s])
        else:
            tree[key] = compress(value)

    return tree


def data_to_various(tree):
    ''' rebucket data into various
    '''
    assert isinstance(tree, dict), tree

    for key, value in list(tree.items()):
        if key == 'data':

            if len(tree.keys()) == 1:
                # we're alone, don't nest further
                continue

            values = tree.pop('data')
            assert 'various' not in tree
            tree['various'] = {'data': values}

        else:
            tree[key] = data_to_various(value)

    return tree


def go():
    ''' full pipeline '''
    return data_to_various(
        pruner(compress(compress(make_tree(expand_names(named())))))
    )


def tree_print(tree, lineage="", depth=0):
    ''' print the tree to stdout '''

    for key, value in sorted(tree.items()):
        if key == "data":
            print(" " * depth, len(tree["data"]), "direct pictures")
            continue

        child = key + " " + lineage if lineage else key
        print(" " * depth, child)
        tree_print(value, lineage=child, depth=depth + 2)


pinned = {
    "crab": '2020-06-17 Rockaway Beach/005 - Dungeness Crab.jpg',
    "anemone": '2019-11-12 Rockaway Beach/019 - Anemones.jpg',
    'barnacle': '2019-12-30 Metridium/005 - Giant Acorn Barnacle.jpg',
    'diver': '2019-10-31 Klein Bonaire M/017 - Divers.jpg',
    'eel': '2020-07-26 Port Townsend/056 - Juvenile Wolf Eel.jpg',
    'fish': '2020-03-01 Power Lines/017 - Juvenile Yellow Eye Rockfish',
    'nudibranch': '2020-07-09 Rockaway Beach/005 - Alabaster Nudibranch.jpg',
    'lobster': '2020-02-19 Sund Rock South Wall/033 - Squat Lobster.jpg',
}


def find_by_path(tree, needle):
    ''' search the tree for an image with this path
    '''
    if not isinstance(tree, dict):
        for image in tree:
            if needle in image.path():
                return image
    else:
        for child in tree.values():
            found = find_by_path(child, needle)
            if found:
                return found

    return None


def find_representative(tree, lineage=None):
    """ grab one image to represent this tree
    """
    if not lineage:
        lineage = []

    category = ' '.join(lineage)
    if category in pinned:
        found = find_by_path(tree, pinned[category])
        if found:
            return found

    if not isinstance(tree, dict):
        results = tree
    else:
        results = (
            find_representative(values, lineage=[key] + lineage)
            for (key, values) in tree.items()
        )

    results = sorted(results, key=lambda x: x.path(), reverse=True)
    return results[0]


def uncategorize(name):
    ''' remove the special categorization labels added earlier '''
    for category, values in categories.items():
        for value in values:
            if name.endswith(" " + category) and value in name:
                name = name.rstrip(" " + category)

    return name


def html_title(lineage):
    ''' html head and title section
    '''
    title = " ".join(lineage) or "Diving Gallery"
    display = uncategorize(title).title()

    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>{title}</title>
        <link rel="stylesheet" href="/style.css"/>
        <link rel="stylesheet" href="/jquery.fancybox.min.css"/>
      </head>

      <body>
      {scripts}
      <div class="title">
    """.format(
        title=display, scripts=html_scripts
    )

    # create the buttons for each part of our name lineage
    for i, parent in enumerate(lineage):
        link = "/gallery/" + " ".join(lineage[i:]) + ".html"
        link = link.replace(" ", "-")

        last = i == len(lineage) - 1

        html += """
        <a href="{link}">
            <h1 class="{classes}">{title}</h1>
        </a>
        """.format(
            title=parent.title(),
            classes="top" + (" last" if last else ""),
            link=link,
        )

    # only include link to timeline on the top level page
    if not lineage:
        html += """
        <a href="/timeline/index.html">
            <h1 class="top switch">Diving Timeline</h1>
        </a>
        <div class="top" id="buffer"></div>
        """

    # always have a link to the top level of the gallery
    html += """
    <a href="/gallery/index.html">
        <h1 class="top switch">Diving Gallery</h1>
    </a>
    </div>
    """

    return html, title


def html_tree(tree, lineage=None):
    """ html version of display
    """
    if not lineage:
        lineage = []

    html, title = html_title(lineage)
    results = []

    has_subcategories = [1 for key in tree.keys() if key != "data"] != []
    if has_subcategories:
        html += '<div class="grid first">'

    # categories
    for key, value in sorted(tree.items()):
        if key == "data":
            continue

        child = key + " " + " ".join(lineage) if lineage else key
        size = tree_size(value)

        example = find_representative(value, [key] + lineage)
        html += """
        <div class="image">
        <a href="{link}">
            <img src="/imgs/{thumbnail}" alt="">
            <h3>
              <span class="sneaky">{size}</span>
              {subject}
              <span class="count">{size}</span>
            </h3>
        </a>
        </div>
        """.format(
            subject=key.title(),
            link="/gallery/{path}.html".format(path=child.replace(" ", "-")),
            thumbnail=example.hash(),
            size='{}:{}'.format(sum(1 for k in value if k != 'data'), size),
        )

        results.extend(html_tree(value, lineage=[key] + lineage))

    if has_subcategories:
        html += "</div>"

    direct = tree.get("data", [])
    direct = sorted(direct, key=lambda x: x.path(), reverse=True)
    assert not (direct and has_subcategories)

    # direct examples
    if direct:

        seen = set()

        if has_subcategories:
            html += """
            <br>
            <h1>More</h1>
            """
            html += '<div class="grid">'
        else:
            html += '<div class="grid first">'

        for image in direct:
            identifier = tuple([image.name, image.path()])
            if identifier in seen:
                print(identifier)
                continue

            html += """
            <a data-fancybox="gallery" data-caption="{name}" href="{fullsize}">
                <img src="/imgs/{thumbnail}" alt="">
            </a>
            """.format(
                name=image.name,
                fullsize=image.fullsize(),
                thumbnail=image.hash(),
            )

            seen.add(identifier)
        html += "</div>"

    html += """
    </body>
    </html>
    """

    if title == "Diving Gallery":
        title = "index"

    results.append((title, html))

    return results


def pool_writer(args):
    ''' callback for HTML writer pool '''
    title, html = args
    path = "gallery/{name}.html".format(name=title.replace(" ", "-"))

    with open(path, "w+") as f:
        print(html, file=f)


def write_all_html():
    ''' main '''
    pool = Pool()

    print("loading data... ", end="", flush=True)
    tree = go()
    print("done", tree_size(tree), "images loaded")

    print("walking tree... ", end="", flush=True)
    htmls = html_tree(tree)
    print("done", len(htmls), "pages prepared")

    print("writing html... ", end="", flush=True)
    pool.map(pool_writer, htmls)
    print("done")


# resources

html_scripts = """
    <!-- fancybox is excellent, this project is not commercial -->
    <script src="/jquery.min.js"></script>
    <script src="/jquery.fancybox.min.js"></script>
"""


if not sys.flags.interactive and __name__ == "__main__":
    if len(sys.argv) == 2:
        root = sys.argv[1]

    write_all_html()
