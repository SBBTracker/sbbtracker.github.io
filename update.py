import collections
import json
import os
import tarfile
from collections import defaultdict
import datetime
from pathlib import Path
from statistics import mean

import numpy as numpy
import requests

try:
    response = requests.get('https://raw.githubusercontent.com/SBBTracker/SBBTracker/main/assets/template-ids.json')
    ids = json.loads(response.text)
except:
    pass

names_to_id = {ids[template_id]["Name"]: ids[template_id]["Id"] for template_id in ids}

patch_date = datetime.date(2022, 2, 14)
# https://9n2ntsouxb.execute-api.us-east-1.amazonaws.com/prod/api/v1/data/daily-rollup/2022-02-11.tar.gz
rollup_base = "https://9n2ntsouxb.execute-api.us-east-1.amazonaws.com/prod/api/v1/data/daily-rollup/"

data_dir = Path("./data")
if not data_dir.exists():
    os.mkdir(data_dir)


def download_rollups():
    for n in range(1, int((datetime.datetime.utcnow().date() - patch_date).days)):
        rollup_date = (patch_date + datetime.timedelta(n)).strftime("%Y-%m-%d")
        rollup_url = rollup_base + rollup_date + ".tar.gz"
        r = requests.get(rollup_url, stream=True)
        local_filename = data_dir.joinpath(rollup_date + ".tar.gz")
        if not local_filename.exists():
            with open(local_filename, 'wb') as local_file:
                for chunk in r.raw.stream(1024, decode_content=False):
                    if chunk:
                        local_file.write(chunk)
            tar = tarfile.open(local_filename)
            tar.extractall(data_dir)
            tar.close()


def update_dict(input_dict, places):
    input_dict["placement"] = round(mean(places), 2)
    input_dict["histogram"] = numpy.histogram(places, bins=range(1, 10))[0].tolist()
    input_dict["matches"] = len(places)
    input_dict["win-percent"] = round(input_dict["histogram"][0] / len(places) * 100, 2)


nonmythic_placements = defaultdict(list)
mythic_placements = defaultdict(list)
mythics = set()

stats = defaultdict(lambda: defaultdict(dict))
num_matches = 0
nonmythic_players = set()

download_rollups()

for player in os.listdir("data"):
    if os.path.isdir(f"data/{player}"):
        for match in os.listdir(f"data/{player}"):
            with open(f"data/{player}/{match}") as f:
                num_matches += 1
                match_dict = json.load(f)
                player_id = match_dict["player-id"]
                placement = match_dict["placement"]
                build_id = match_dict['build-id'] if 'build-id' in match_dict else ''
                if match_dict["combat-info"]:
                    combat = match_dict["combat-info"][0]
                    if player_id in combat and 'hero' in combat[player_id]:
                        hero_id = combat[player_id]['hero']
                        hero_name = ids[hero_id]['Name']
                        if hero_name is not None:
                            if match_dict["possibly-mythic"]:
                                mythics.add(player_id)
                                mythic_placements[hero_name].append(placement)
                            else:
                                nonmythic_placements[hero_name].append(placement)
                                nonmythic_players.add(player_id)

total_nonmythic_places = []
total_mythic_places = []
for hero in nonmythic_placements:
    total_nonmythic_places.extend(nonmythic_placements[hero])
    total_mythic_places.extend(mythic_placements[hero])

    total_data = stats["total"][hero]
    nonmythic_data = stats["nonmythic"][hero]
    mythic_data = stats["mythic"][hero]

    update_dict(nonmythic_data, nonmythic_placements[hero])
    update_dict(mythic_data, mythic_placements[hero])
    update_dict(total_data, nonmythic_placements[hero] + mythic_placements[hero])

update_dict(stats["nonmythic"]["All Heroes"], total_nonmythic_places)
update_dict(stats["mythic"]["All Heroes"], total_mythic_places)
update_dict(stats["total"]["All Heroes"], total_mythic_places + total_nonmythic_places)
stats["players"] = len(nonmythic_players) + len(mythics)
stats["matches"] = num_matches
stats["last-updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " EST"

with open("./docs/stats/placements.json", "w", newline='') as out_file:
    json.dump(stats, out_file)

with open("./docs/art/names_to_id.json", "w", newline='') as f:
    json.dump(names_to_id, f)
