import datetime
import json
from collections import defaultdict
from statistics import mean

from sbbtracker_datasci import download
from sbbtracker_datasci.utils import load_data

import numpy as numpy


def update_dict(input_dict, places):
    input_dict["placement"] = round(mean(places), 2)
    input_dict["histogram"] = numpy.histogram(places, bins=8)[0].tolist()
    input_dict["matches"] = len(places)
    input_dict["win-percent"] = round(input_dict["histogram"][0] / len(places) * 100, 2)


download.download_data()

load_data.load_data()

nonmythic_placements = defaultdict(list)
mythic_placements = defaultdict(list)
mythics = set()

stats = defaultdict(lambda: defaultdict(dict))
num_matches = 0
nonmythic_players = set()

for match in load_data.GLOBAL_DATA.all_data[load_data.GLOBAL_DATA.latest_patch]:
    num_matches += 1
    match_dict = load_data.GLOBAL_DATA.all_data[load_data.GLOBAL_DATA.latest_patch][match]
    player_id = match_dict["player-id"]
    placement = match_dict["placement"]
    if match_dict["combat-info"]:
        combat = match_dict["combat-info"][0]['combat']
        if player_id in combat and 'hero-name' in combat[player_id]:
            hero_name = combat[player_id]['hero-name']
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

with open("docs/stats/placements.json", "w", newline='') as out_file:
    json.dump(stats, out_file)
