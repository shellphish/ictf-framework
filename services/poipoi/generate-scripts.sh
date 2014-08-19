#!/bin/bash

# generate scripts
cp script-templates/benign.py scripts/benign.py
sed -i -e "/XXXSHAREDXXX/r script-templates/shared.py" -e "//d" scripts/benign.py
cp script-templates/getflag.py scripts/getflag.py
sed -i -e "/XXXSHAREDXXX/r script-templates/shared.py" -e "//d" scripts/getflag.py
cp script-templates/setflag.py scripts/setflag.py
sed -i -e "/XXXSHAREDXXX/r script-templates/shared.py" -e "//d" scripts/setflag.py
cp script-templates/exploit.py scripts/exploit.py
sed -i -e "/XXXSHAREDXXX/r script-templates/shared.py" -e "//d" scripts/exploit.py
