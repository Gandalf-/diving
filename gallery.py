#!/usr/bin/python3

import hashlib
import sys
import os

from multiprocessing import Pool
import inflect

inflect = inflect.engine()


def flatten(xs):
    return [item for sublist in xs for item in sublist]


root = "/mnt/zfs/Media/Pictures/Diving"
fishes = (
    "flounder",
    "blue tang",
    "grunt",
    "goby",
    "gunnel",
    "sculpin",
    "greenling",
    "lingcod",
    "sculpin",
    "tarpon",
    "war bonnet",
)
nudibranchs = ("sea lemon", "dorid")


class Image:
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
        return os.path.join(root, self.directory, self.label)

    def fullsize(self):
        return "https://public.anardil.net/media/diving/{d}/{i}".format(
            d=self.directory, i=self.label,
        )

    def normalized(self):
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
        if (
            name != "fish"
            and name.endswith("fish")
            and not name.endswith(" fish")
        ):
            name = name.replace("fish", " fish")

        # categorization
        for fish in fishes:
            if name.endswith(fish):
                name += " fish"

        for nudi in nudibranchs:
            if name.endswith(nudi):
                name += " nudibranch"

        return name


def listing():
    """ a list of all dive picture folders available """
    return [d for d in os.listdir(root) if not d.startswith(".")]


def delve(directory):
    """ create an Image object for each picture in a directory """
    path = os.path.join(root, directory)
    return [Image(o, directory) for o in os.listdir(path) if o.endswith(".jpg")]


def collect():
    """ run delve on all dive picture folders """
    return [delve(d) for d in listing()]


def named():
    return flatten([[y for y in z if y.name] for z in collect()])


def expand_names(images):
    """ split out `a and b` into separate elements """
    result = []

    for image in images:
        for split in (" with ", " and "):

            if split not in image.name:
                continue

            left, right = image.name.split(split)

            clone = image
            clone.name = left
            image.name = right
            result.append(clone)

        result.append(image)

    return result


def hash(path):
    sha1 = hashlib.sha1()

    with open(path, "rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()


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
        tree.pop(remove)

    return tree


def compress(tree):
    """ look for sub trees with no 'data' key, which can be squished up a level
    """
    if not isinstance(tree, dict):
        return

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


def go():
    return pruner(compress(compress(make_tree(expand_names(named())))))


def display(tree, lineage="", depth=0):

    for key, value in sorted(tree.items()):
        if key == "data":
            print(" " * depth, len(tree["data"]), "direct pictures")
            continue

        child = key + " " + lineage if lineage else key
        print(" " * depth, child)
        display(value, lineage=child, depth=depth + 2)


def find_representative(tree):
    """ grab one image to represent this tree
    """
    if not isinstance(tree, dict):
        results = tree
    else:
        results = (find_representative(child) for child in tree.values())

    results = sorted(results, key=lambda x: x.path(), reverse=True)
    return results[0]


def uncategorize(name):
    for fish in fishes:
        if name.endswith(" fish") and fish in name:
            name = name.rstrip(" fish")

    for nudi in nudibranchs:
        if name.endswith(" nudibranch") and nudi in name:
            name = name.rstrip(" fish")

    return name


def html_tree(tree, lineage=[]):
    """ html version of display
    """
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
    """.format(
        title=display, scripts=html_scripts
    )

    # title
    html += '<div class="title">'

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

    if not lineage:
        html += """
        <a href="/timeline/index.html">
            <h1 class="top switch">Diving Timeline</h1>
        </a>
        <div class="top" id="buffer"></div>
        """

    html += """
    <a href="/gallery/index.html">
        <h1 class="top switch">Diving Gallery</h1>
    </a>
    """

    html += "</div>"

    results = []

    html += '<div class="grid">'
    found_category = False

    # categories
    for key, value in sorted(tree.items()):
        if key == "data":
            continue

        found_category = True
        child = key + " " + " ".join(lineage) if lineage else key

        example = find_representative(value)
        html += """
        <div class="image">
        <a href="{link}">
            <img src="/imgs/{thumbnail}" alt="">
            <h4>{subject}</h4>
        </a>
        </div>
        """.format(
            subject=key.title(),
            link="/gallery/{path}.html".format(path=child.replace(" ", "-")),
            thumbnail=hash(example.path()),
        )

        results.extend(html_tree(value, lineage=[key] + lineage))
    html += "</div>"

    direct = tree.get("data", [])
    direct = sorted(direct, key=lambda x: x.path(), reverse=True)

    # direct examples
    if direct:

        seen = set()

        if found_category:
            html += """
            <br>
            <h1>More</h1>
            """.format(
                title=title
            )

        html += '<div class="grid">'
        for image in direct:
            identifier = tuple([image.name, image.path()])
            if identifier in seen:
                continue

            html += """
            <a data-fancybox="gallery" data-caption="{subject}" href="{fullsize}">
                <img src="/imgs/{thumbnail}" alt="">
            </a>
            """.format(
                subject=image.name,
                fullsize=image.fullsize(),
                thumbnail=hash(image.path()),
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
    title, html = args
    path = "gallery/{name}.html".format(name=title.replace(" ", "-"))

    with open(path, "w+") as f:
        print(html, file=f)


def write_all_html():
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
