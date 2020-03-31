import json
import argparse
import sys
import os

class ComposedTemplate(object):
    def __init__(self, base_object=None, init_template_paths=None):
        """

        :param base_object:
        :type base_object: dict
        :param init_template_paths:
        :type init_template_paths: list
        :return: None
        """
        if init_template_paths is None:
            init_template_paths = []

        if base_object is None:
            base_object = {}

        self.o = base_object

        for f in init_template_paths:
            self.load_and_merge(f)

    def load_and_merge(self, template_path):
        data = load_template(template_path)
        self.merge(data)

    def merge(self, t):
        self.o = merge_template(self.o, t)

    def override(self, keys, value):
        cur = self.o
        for k in keys[:-1]:
            cur = cur[k]

        if value is not None:
            cur[keys[-1]] = value
        else:
            del cur[keys[-1]]

    def get_final_object(self):
        return self.o


def load_template(path):
    with open(path, 'r') as f:
        r = json.load(f)
    return r


def pop_merge_val(o_dest, o_src, k):
    if k not in o_src or not o_src[k]:
        return

    v = o_src.pop(k)

    if k not in o_dest:
        o_dest[k] = type(v)()

    if type(v) is list:
        o_dest[k].extend(v)
    elif type(v) is dict:
        o_dest[k].update(v)
    else:
        raise RuntimeError("Unknown types to merge! Trying to merge key {} from {} into {}".format(k, o_src, o_dest))


def merge_template(obj, t):
    """

    :param obj:
    :type obj: dict
    :param t:
    :type t: dict
    :return: None
    """

    t = t.copy()
    pop_merge_val(obj, t, 'builders')
    pop_merge_val(obj, t, 'variables')
    pop_merge_val(obj, t, 'provisioners')
    #pop_merge_val(obj, t, 'post-processors')

    assert not t, 'Apparently did not consume all properties, left with {}'.format(t)
    return obj


def base_template_composition_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o',
                        '--overrides',
                        action='append',
                        default=[],
                        help='''expressions to override properties dynamically. 
    Expressions consist of a list of keys to traverse, seperated by '->', to get to the object to modify followed by 
    '=' and the value to store there.If the value is enclosed in eval(..) then it will 
    be evaluated and the result will be used instead of the string itself.

    Ex. 1: variables->ICTF_FRAMEWORK_DIR=eval(os.path.join(os.path.abspath(os.getcwd()), '..', '..'))
    '''
                        )

    parser.add_argument('-t',
                        '--templates',
                        nargs='+',
                        help='list of templates to compose in order to create the final base template')
    return parser


def create_composed_template(templates, overrides=None):
    overrides = overrides or tuple()

    t = ComposedTemplate(init_template_paths=templates)
    for v in overrides:
        keys = [k.strip() for k in v[:v.index('=')].split('->')]
        val = v[v.index('=') + 1:]
        if val.startswith('eval('):
            assert val.endswith(')')
            to_eval = val[5:-1]
            val = eval(to_eval)

        t.override(keys, val)

    return t
