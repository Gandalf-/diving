#!/usr/bin/python3

import matplotlib.pyplot as m

from utility import flatten
import detective


print("loading... ", end="", flush=True)
ns, ts, ss = detective.table_builder(False)
print("done")

def scatterer():
    _, ax = m.subplots()
    for i, name in enumerate(ns):
        x = [i for _ in range(len(ss[i]))]
        y = ss[i]
        s = [1 for _ in range(len(ss[i]))]
        ax.scatter(x, y, s=s)

m.hist(flatten(ss), bins=20)
m.show()
