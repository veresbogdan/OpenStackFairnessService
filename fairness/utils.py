from collections import defaultdict


def dsum(*dicts):
    ret = defaultdict(int)
    for d in dicts:
        if type(d) is dict:
            for k, v in d.items():
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
