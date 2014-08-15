import MySQLdb
import MySQLdb.cursors

import base64
import sys
import json
from settings import *

import reset_db

def main():

    service_dir = sys.argv[1]


    my_user = MYSQL_DATABASE_USER
    my_db = MYSQL_DATABASE_DB


    db = MySQLdb.connect(user=my_user, passwd=MYSQL_DATABASE_PASSWORD, db=my_db, cursorclass=MySQLdb.cursors.DictCursor)

    c = db.cursor()


    with open(service_dir + 'info.json', 'r') as service_info:
        info = json.load(service_info)
        
        service_id = info['id']

        c.execute("""update scripts set latest_script = 0 where is_ours = 1 and service_id = %s""",
                  (service_id,))

        reset_db.create_script(service_id, 'getflag', service_dir + info['getflag'], c, db)
        reset_db.create_script(service_id, 'setflag', service_dir + info['setflag'], c, db)
        for benign in info['benign']:
            reset_db.create_script(service_id, 'benign', service_dir  + benign, c, db)
        for exploit in info['exploit']:
            reset_db.create_script(service_id, 'exploit', service_dir + exploit, c, db)


    db.commit()

if __name__ == "__main__":
    print main()
