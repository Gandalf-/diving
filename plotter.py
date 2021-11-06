#!/usr/bin/python3

# %%
from apocrypha.client import Client
import matplotlib.pyplot as m
import numpy as np

from utility import flatten
import detective


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

m.grid(True)
m.show()

# %%
