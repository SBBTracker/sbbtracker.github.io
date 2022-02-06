import datetime
import json
from collections import defaultdict
from statistics import mean

from sbbtracker_datasci import download
from sbbtracker_datasci.utils import load_data

import numpy as numpy

download.download_data()

load_data.load_data()

placements = defaultdict(list)
mythic_placements = defaultdict(list)
mythics = set()

stats = defaultdict(lambda: defaultdict(dict))
num_matches = 0
players = set()

for match in load_data.GLOBAL_DATA.all_data[load_data.GLOBAL_DATA.latest_patch]:
    num_matches += 1
    match_dict = load_data.GLOBAL_DATA.all_data[load_data.GLOBAL_DATA.latest_patch][match]
    player_id = match_dict["player-id"]
    players.add(player_id)
    placement = match_dict["placement"]
    if match_dict["combat-info"]:
        combat = match_dict["combat-info"][0]['combat']
        if player_id in combat:
            hero_name = combat[player_id]['hero-name']
            if hero_name is not None:
                placements[hero_name].append(placement)
                if match_dict["possibly-mythic"]:
                    mythics.add(player_id)
                    mythic_placements[hero_name].append(placement)

total_places = []
total_mythic_places = []
for hero in placements:
    places = placements[hero]
    total_places.extend(places)
    total_mythic_places.extend(mythic_placements[hero])

    total_data = stats["total"][hero]
    mythic_data = stats["mythic"][hero]
    total_data["placement"] = round(mean(places), 2)
    total_data["histogram"] = numpy.histogram(places, bins=8)[0].tolist()
    total_data["matches"] = len(places)
    total_data["win-percent"] = round(total_data["histogram"][0] / len(places) * 100, 2)
    mythic_data["placement"] = round(mean(mythic_placements[hero]), 2)
    mythic_data["histogram"] = numpy.histogram(mythic_placements[hero], bins=8)[0].tolist()
    mythic_data["matches"] = len(mythic_placements[hero])
    mythic_data["win-percent"] = round(mythic_data["histogram"][0] / len(mythic_placements[hero]) * 100, 2)


stats["players"] = len(players)
stats["matches"] = num_matches
stats["last-updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " EST"

with open("docs/stats/placements.json", "w", newline='') as out_file:
    json.dump(stats, out_file)
