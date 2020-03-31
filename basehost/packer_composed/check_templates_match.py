from compose_utils import create_composed_template, base_template_composition_argparser
import argparse
import os
import sys
import json
import six

parser = base_template_composition_argparser()
parser.add_argument('template_to_check', help='path to store the resulting template in')
args = parser.parse_args()

composed_template = create_composed_template(args.templates, args.overrides)

with open(args.template_to_check, 'r') as f:
    to_check = json.load(f)


def walk_objects(o1, o2, path=()):
    if o1 == o2:
        return True

    if type(o1) in six.string_types and type(o2) in six.string_types:
        if o1 == o2:
            return True
        print("Difference @ {}:\t {} and {} differ in value\n".format(path, o1, o2))
        return False

    if type(o1) != type(o2):
        import ipdb; ipdb.set_trace()
        print("Difference @ {}:\t {} and {} differ in type: {} vs {}\n".format(path, o1, o2, type(o1), type(o2)))
        return False

    if type(o1) == dict:
        ks1 = set(o1.keys())
        ks2 = set(o2.keys())
        if ks1 != ks2:
            print("Difference @ {}:\t dicts don't share the same keys: {} vs {}, difference {}\n".format(path, ks1, ks2, ks1.symmetric_difference(ks2)))
            return False

        same = True
        for k in ks1:
            same = same & walk_objects(o1[k], o2[k], path + (k,))

        return same

    elif type(o1) == list:
        if len(o1) != len(o2):
            print("Difference @ {}:\t difference in list length: {} vs {}\n".format(path, len(o1), len(o2)))
            return False

        same = True
        for i in range(len(o1)):
            same = same & walk_objects(o1[i], o2[i], path + (i,))
        return same

    else:
        print("Difference @ {}:\t Objects should match but don't: {} vs {}\n".format(path, o1, o2))
        return False


o = composed_template.get_final_object()
#import ipdb; ipdb.set_trace()
matched = walk_objects(to_check, o)
sys.exit(0 if matched else 1)

