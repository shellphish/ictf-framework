import itertools


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


def flatten(an_iterable):
    return itertools.chain(*an_iterable)


def flatten_deep(iterable):
    iterable = iter(iterable)

    while 1:
        try:
            item = iterable.next()
        except StopIteration:
            break

        try:
            data = iter(item)
            iterable = itertools.chain(data, iterable)
        except:
            yield item
