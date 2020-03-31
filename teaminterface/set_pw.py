import requests
from passlib.utils import generate_password
import sys
from config import config

def _db_api_post_authenticated(endpoint, args):
    try:
        ret = requests.post(config['DB_API_URL_BASE'] + endpoint, data=args, params={'secret': config['DB_API_SECRET']})
        if ret.status_code == 200:
            result_json = ret.json()
            return result_json
        else:
            raise RuntimeError(ret.text)
    except ValueError:
        return
    except:
        raise

team_id = sys.argv[1]
password = generate_password(16)
print password
reset_args = {}
reset_args['team_id'] = team_id
reset_args['password'] = password
result = _db_api_post_authenticated("/team/changepass", reset_args)
print result
