from requests import post
from config import config
import sys

meta_qs = "metadata_questions"

endpoint = "/teams/metadata/labels/add"
with open(meta_qs,"r") as f:
    qs = f.read().splitlines()

for q in qs:
    if not q.strip():
        continue
    label, description = q.split("\t")
    resp = post(config['DB_API_URL_BASE'] + endpoint, data={'label': label, 'description':description}, params={'secret': config['DB_API_SECRET']})
    print resp.content
