from collections import defaultdict

import numpy as np


def dsum(*dicts):
    ret = defaultdict(int)
    for d in dicts:
        if type(d) is dict:
            for k, v in d.items():
                if type(v) is list:
                    # TODO sum up the list?
                    if v is not None:
                        ret[k] = [x + y for x, y in zip(ret[k], v)]
                    else:
                        ret[k] = list()
                else:
                    if v is not None:
                        ret[k] += v
                    else:
                        ret[k] += 0
    return dict(ret)


def dminus(*dicts):
    ret = defaultdict(int)
    for d in dicts:
        if type(d) is dict:
            for k, v in d.items():
                ret[k] -= v
    return dict(ret)
