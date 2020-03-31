#!/bin/bash

function gen_pass()
{
    cat /dev/urandom | base64 | head -c $1 | sed 's/[+/]/_/g'
}

mkdir -p secrets/database-api
echo '172.31.64.13:80' > secrets/api_address
gen_pass 25 > secrets/database-api/mysql
gen_pass 25 > secrets/database-api/salt
gen_pass 25 > secrets/database-api/secret
gen_pass 500 > secrets/teamvm_ova_key
