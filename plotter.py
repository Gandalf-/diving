#!/usr/bin/python3

# %%
from apocrypha.client import Client
import matplotlib.pyplot as m
import numpy as np

import taxonomy
import detective
import collection

from utility import flatten, tree_size
from plot_utility import BubbleChart


m.rcParams['figure.dpi'] = 175


def packed_bubble(names, counts, spacing=5):
    ''' plot '''
    chart = BubbleChart(area=counts, bubble_spacing=spacing)
    chart.collapse()

    _, ax = m.subplots(subplot_kw=dict(aspect='equal'))
    prop_cycle = m.rcParams['axes.prop_cycle']
    colors = prop_cycle.by_key()['color'] * 50

    chart.plot(ax, names, colors)
    ax.axis('off')
    ax.relim()
    ax.autoscale_view()
    m.show()


# %%
# similiarity distances between all subjects
print("loading... ", end="", flush=True)
ns, ts, ss, _ = detective.table_builder(False)
print("done")


def scatterer():
    _, ax = m.subplots()
    for i, name in enumerate(ns):
        size = len(ss[i])

        x = [i for _ in range(size)]
        y = ss[i]
        s = [1 for _ in range(size)]

        ax.scatter(x, y, s=s)


m.title('Distances between subjects')
m.xlabel('Distance')
m.ylabel('Occurrences')

m.hist(flatten(ss), bins=20)
m.show()

# %%
# cache prefetch timing
db = Client(host='elm.anardil.net')
choices = db.keys('diving', 'cache-speed')

when = choices[0]
times = db.get('diving', 'cache-speed', when, default=[])
times = [float(t) for t in times]

m.title('Digital Ocean CDN Prefetch Timing')

percentiles = [0.01, 0.1, 1, 25, 50, 75, 99, 99.9, 99.99]
m.bar([str(p) for p in percentiles], np.percentile(times, percentiles))

# m.plot(times)

m.ylabel('Seconds')
m.xlabel('Percentile')
m.grid(True)
m.show()


# %%
# common names bar graph
tree = collection.go()  # common names
sizes = {k: tree_size(v) for k, v in tree.items()}

for k, v in list(sizes.items()):
    if v > 50:
        continue
    sizes.setdefault('other', 0)
    sizes['other'] += v
    del sizes[k]

names, counts = list(zip(*sorted(sizes.items())))
xs = [i for i in range(len(counts))]

m.bar(xs, counts)
m.title('Diving Pictures')
m.ylabel('Pictures')
m.xticks(xs, names, rotation=45, ha='right')
m.show()


# %%
# common names packed bubble chart

m.rcParams.update({'font.size': 6})

tree = collection.go()  # common names
tree = tree['shrimp']
sizes = {k: tree_size(v) for k, v in tree.items()}

filter = 1
for k, v in list(sizes.items()):
    if v > filter:
        continue
    sizes.setdefault('other', 0)
    sizes['other'] += v
    del sizes[k]

sizes = {
    k.title().replace(' ', '\n') + f'\n{v}': 2 * v
    for k, v in sizes.items()
}

names, counts = list(zip(*sizes.items()))
packed_bubble(names, counts, 1)


# %%
# animalia packed bubble chart

m.rcParams.update({'font.size': 7})

tree = taxonomy.gallery_tree()
tree = tree['Animalia']['Chordata']['Actinopterygii']['Perciformes']
sizes = {k: tree_size(v) for k, v in tree.items()}

filter = 5
to_drop = []
other = 0
for k, v in sizes.items():
    if v > filter:
        continue
    other += v
    to_drop.append(k)

if other:
    sizes['other'] = other

sizes = {
    f'{k.title().split(" ")[0]}\n{v}': 2 * v
    for k, v in sizes.items()
    if k not in to_drop
}

names, counts = list(zip(*sizes.items()))
packed_bubble(names, counts, 1)

# %%
