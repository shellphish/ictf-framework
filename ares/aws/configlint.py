from pathlib import Path
import json
import yaml
import jsonschema

PATH = Path.cwd()

def fail_check(msg):
    print(msg)
    exit(1)

def unique(s):
    s2 = list(s)
    return len(s2) == len(set(s2))

def require_unique(s, key):
    if not unique(s):
        fail_check('Key \'{}\' is not unique'.format(key))

def lint(contents, schema):
    jsonschema.validate(contents, schema)

    if contents['game_info']['num_routers'] != 20:
        fail_check("20 router instances is hardcoded, instead you have {}".format(contents['game_info']['num_routers']))
    teams = contents['teams']

    def unique_across_teams(k):
        require_unique((t[k] for t in teams), k)

    unique_across_teams('name')
    unique_across_teams('id')
    unique_across_teams('flag_token')
    unique_across_teams('email')

    team_ids = list(sorted(t['id'] for t in teams))
    if team_ids != list(range(1, len(teams)+1)):
        fail_check('Team ids are not correctly numbered.')

    host_dir = Path(contents['service_metadata']['host_dir']).expanduser()
    if not (host_dir.exists() and host_dir.is_dir()):
        fail_check('Host directory \'{}\' does not exist.'.format(host_dir))

    for service in contents['services']:
        d = host_dir / service['name']
        yamlp = d / 'info.yaml'
        if not (d.exists() and d.is_dir() and yamlp.exists() and yamlp.is_file()):
            fail_check("Service Host Directory \'{}\' does not follow the layout of a services repo.".format(host_dir))

if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser(description='Lint the game config before starting up the game.')
    p.add_argument('config', metavar='config', type=Path, help='game config to lint')
    p.add_argument('-s', '--schema', default=(PATH / 'config_schema.yml'), type=Path, help='schema path')

    args = p.parse_args()

    with args.schema.open('r') as f:
        schema = yaml.load(f, Loader=yaml.SafeLoader)

    with args.config.open('r') as f:
        config = json.load(f)

    lint(config, schema)
    print('ALL GOOD!')
