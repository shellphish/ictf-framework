import base64
import os
import requests
import sys
import yaml
import json

# THIS PATH ARE RELATIVE TO WHERE TERRAFORM WILL BE LAUNCHED BECAUSE
# THEY ARE USED IN THE PROVISIONING SECTION.
PROV_FOLDER = os.path.dirname(os.path.abspath(__file__))
SECRETS_FOLDER = os.path.join(PROV_FOLDER, '../../secrets/')
VM_PROVISIONED_NAME = "database"


def register_service(db_api_url_base, db_secret, service_name, service_info):
    payload = b''
    EncodedPayload = base64.b64encode(payload).decode("utf-8")
    data = {"team_id":     0, "name": service_name, "payload": EncodedPayload,
            "upload_type": "service", "is_bundle": "1"}

    result = requests.post(db_api_url_base + "/upload/new", data=data, params={'secret': db_secret})

    response = result.json()

    if response['result'] == 'success':
        # print("successfully uploaded bundle")
        upload_id = response['upload_id']

        # then, register it as a service

        data = {"name":                service_name, "upload_id": upload_id, "description": service_info['description'],
                "authors":             service_info['authors'],
                "flag_id_description": service_info['flag_id_description'],
                "state":               service_info['state']}
        result = requests.post(db_api_url_base + "/service/new", data=data, params={'secret': db_secret})
        response = result.json()

        if response['result'] == 'success':
            # print("successfully registered example service")
            service_id = response["id"]

            scripts_path = os.path.join(service_info['path'], 'scripts')

            for script in os.listdir(scripts_path):
                if os.path.isfile(os.path.join(scripts_path, script)):

                    script_type = os.path.basename(script)

                    if script_type in {'setflag', 'getflag', 'benign', 'exploit'}:
                        print (f"Uploading script {filename} [{script_type}]")
                        data = {"upload_id": upload_id, "filename": script, "type": script_type,
                                "state":     service_info['state'], "service_id": service_id}
                        result = requests.post(db_api_url_base + "/script/new", data=data, params={'secret': db_secret})
                        assert result.status_code == 200
                    else:
                        print("Unknown script type " + str(script_type) + " skipping " + script)

            return {"success": True, "service_id": service_id, "service_name": service_name}

    elif response['result'] == 'update succeeded':
        print("UPLOAD ALREADY COMPLETED, SCRIPTS UPDATED IN DB".format())
        return {"success": False, "service_name": service_name}
    else:
        print("UNEXPECTED return result, {}".format(response['result']))
        return {"success": False, "service_name": service_name}


def create_service(db_api_url_base, db_secret, service_path, service_state):
    # extract the service_info from the info.yaml file inside the service_path
    print(service_path)
    service_yaml = os.path.abspath(os.path.join(service_path, './info.yaml'))
    if not os.path.isfile(service_yaml):
        raise Exception("Could not find service file for %s, tried %s. Skipping." % (service_path, service_yaml))
    service_info = yaml.load(open(service_yaml, 'r'))

    # Check that the service path matches the name in info.yaml

    service_name = os.path.basename(service_path)
    if service_name == "":
        service_name = os.path.basename(service_path[:-1])
    if service_name != service_info['service_name']:
        print(
            '{} ({})!= {} - Path of service doesn\'t match the name listed in info.yaml... Please change info.yaml manually and verify tgz is updated appropriately. '.
            format(service_name, service_path, service_info['service_name']))
        exit("100")
        # service_info['service_name'] = service_name
        # with open(service_yaml, 'w') as fout:
        #     yaml.dump(service_info, fout)

    # Copy over the state and path to the teams_info file (other components expect them to be there)
    service_info['state'] = service_state
    service_info['path'] = service_path
    return register_service(db_api_url_base, db_secret, service_info['service_name'], service_info)


'''
 Creating all services specified in the game_info.yml
'''


def create_all_services(db_api_url_base, db_secret, services_info, services_folder_path):
    processed = dict()
    for service in services_info:
        service_name = service['name']
        service_path = os.path.join(services_folder_path, service_name)
        service_state = service['state']

        if service_path not in processed:
            if service_state != 'enabled':
                print("Service " + service_path + "is not enabled, skipping")
                continue

        create_service(db_api_url_base, db_secret, service_path, service_state)
        processed[service_path] = True


if __name__ == "__main__":
    game_config = json.load(open(sys.argv[2], 'r'))

    db_api = sys.argv[1]  # passed by terraform
    database_api_secret_path = SECRETS_FOLDER + "database-api/secret"

    if not os.path.isfile(database_api_secret_path):
        raise Exception("Missing database secrets!")

    with open(database_api_secret_path, "r") as f:
        database_api_secret = f.read().rstrip()

    create_all_services('http://{}'.format(db_api), database_api_secret, game_config['services'], game_config["service_metadata"]['host_dir'])
