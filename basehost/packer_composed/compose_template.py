from compose_utils import create_composed_template, base_template_composition_argparser
import argparse
import os
import sys
import json

parser = base_template_composition_argparser()
parser.add_argument('dest_path', help='path to store the resulting template in')
parser.add_argument('-f', '--force', help='force overwrite existing files, PROBABLY a bad idea')
args = parser.parse_args()

composed_template = create_composed_template(args.templates, args.overrides)

if args.force or not os.path.isfile(args.dest_path):
    with open(args.dest_path, 'w') as f:
        json.dump(composed_template.get_final_object(), f, indent=2)
