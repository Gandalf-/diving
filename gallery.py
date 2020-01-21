#!/usr/bin/python3

import hashlib
import os
import inflect

inflect = inflect.engine()

def flatten(xs):
    return [item for sublist in xs for item in sublist]

root = '/mnt/zfs/Media/Pictures/Diving'

class Image:
    def __init__(self, label, directory):
        self.label = label
        label, _ = os.path.splitext(label)

        if ' - ' in label:
            number, name = label.split(' - ')
        else:
            number = label
            name = ''

        self.name = name
        self.number = number
        self.directory = directory

    def __repr__(self):
        return ', '.join([
            # self.number,
            self.name,
            # self.directory
        ])

    def path(self):
        return os.path.join(
            root, self.directory,
            self.label)

    def fullsize(self):
        return 'https://public.anardil.net/media/diving/{d}/{i}'.format(
                d=self.directory,
                i=self.label,
            )

    def normalized(self):
        # simplify name
        name = inflect.singular_noun(self.name.lower())

        name = name or self.name.lower()

        # fix inflect's mistakes
        if name.endswith('octopu') or name.endswith('gras'):
            name += 's'

        if name.endswith('alga'):
            name += 'e'

        return name

def listing():
    return [
        d for d in os.listdir(root)
        if not d.startswith('.')
    ]

def delve(directory):
    path = os.path.join(root, directory)
    return [
        Image(o, directory)
        for o in os.listdir(path)
        if o.endswith('.jpg')
    ]

def collect():
    return [
        delve(d) for d in listing()
    ]

def named():
    return flatten([
        [y for y in z if y.name]
        for z in collect()
    ])

def expand_names(images):
    result = []

    for image in images:

        if ' and ' in image.name:
            left, right = image.name.split(' and ')

            clone = image
            clone.name = left
            image.name = right
            result.append(clone)

        result.append(image)

    return result

def group(images):

    groups = {}

    # first pass, full names
    for image in images:
        groups.setdefault(image.normalized(), [])
        groups[image.normalized()].append(image)

    # second pass, sub names
    # deep anenomes -> anenomes, deep anenomes
    for image in images:
        words = image.normalized().split(' ')[::-1]
        base = words[0]
        for word in words[1:]:
            if base in groups:
                groups[base].append(image)

            base = ' '.join([word, base])

    return groups

def run():
    return group(expand_names(named()))

def hash(path):
    sha1 = hashlib.sha1()

    with open(path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()

def summary():
    from pprint import pprint as p
    d = run()
    p({k: len(v) for k,v in d.items()})

def write_html(name, images):
    ''' it's assumed that all these images are of the same thing '''

    html = '''
    <!DOCTYPE html>
    <html>
      <head>
        <title>{title}</title>
      </head>
      {style}
      <body>
      {scripts}
    '''.format(
        title=name.title(),
        style=html_style,
        scripts=html_scripts
    )

    for image in images:
        html += '''
        <div class="image">
          <a data-fancybox="gallery" data-caption="{subject}" href="{fullsize}">
            <img src="/imgs/{thumbnail}" alt="">
          </a>
        </div>
        '''.format(
            subject=image.name,
            fullsize=image.fullsize(),
            thumbnail=hash(image.path())
        )

    html += '''
    </body>
    </html>
    '''

    name = '-'.join(name.split(' '))

    with open('html/' + name + '.html', 'w+') as f:
        print(html, file=f)

def write_all_html():
    data = run()
    too_few = 4

    for name, images in data.items():
        if len(images) < too_few:
            continue

        print(name)
        write_html(name, images)

# resources

html_scripts = '''
    <!-- fancybox is excellent, this project is not commercial -->
    <script src="/jquery.min.js"></script>
    <link rel="stylesheet" href="/jquery.fancybox.min.css"/>
    <script src="/jquery.fancybox.min.js"></script>
'''

html_style = '''
  <style>

.image {
  display: inline-block;
  padding: 2px;
  margin:  auto;
  width:   '$column_width_percent'%;
}

img {
  width: 100%;
}

.row::after {
  content: "";
  clear:   both;
  display: table;
}

body {
  background-color: black;
  text-align:       center;
}

figcaption, h1, h4 {
  color: white;
}

.sidebar {
  height: 100%;
  width: 0;
  position: fixed;
  z-index: 1;
  top: 0;
  left: 0;
  background-color: #111;
  overflow-x: hidden;
  transition: 0.5s;
  padding-top: 60px;
}

.sidebar a {
  padding: 8px 8px 8px 32px;
  text-decoration: none;
  font-size: 25px;
  color: #818181;
  display: block;
  transition: 0.3s;
}

.sidebar a:hover {
  color: #f1f1f1;
}

.sidebar .closebtn {
  position: absolute;
  top: 0;
  right: 25px;
  font-size: 36px;
  margin-left: 50px;
}

.openbtn {
  float: right;
  position: fixed;
  right: 25px;
  font-size: 20px;
  cursor: pointer;
  background-color: #111;
  color: white;
  padding: 10px 15px;
  border: none;
}

.openbtn:hover {
  background-color: #444;
}
  </style>
    '''
