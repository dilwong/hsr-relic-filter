#!/usr/bin/env python
# coding: utf-8

import requests
from bs4 import BeautifulSoup
import re
import time
from itertools import chain
import difflib
import pandas as pd
from collections import defaultdict
from typing import List, Dict


elemental_boosts = [
    'Physical DMG Boost',
    'Fire DMG Boost',
    'Ice DMG Boost',
    'Wind DMG Boost',
    'Lightning DMG Boost',
    'Quantum DMG Boost',
    'Imaginary DMG Boost'
]

relic_pieces_to_possible_main_stats = {
    'Head': ['HP'],
    'Hands': ['ATK'],
    'Body': ['HP%', 'ATK%', 'DEF%', 'Effect Hit Rate', 'Outgoing Healing Boost', 'CRIT Rate', 'CRIT DMG'],
    'Feet': ['HP%', 'ATK%', 'DEF%', 'SPD'],
    'Planar Sphere': ['HP%', 'ATK%', 'DEF%', 'Physical DMG Boost', *elemental_boosts],
    'Link Rope': ['HP%', 'ATK%', 'DEF%', 'Break Effect', 'Energy Regeneration Rate']
}

all_possible_main_stats = set(chain.from_iterable(relic_pieces_to_possible_main_stats.values()))

all_possible_substats = set([
    'HP', 'ATK', 'DEF',
    'HP%', 'ATK%', 'DEF%',
    'Break Effect', 'Effect Hit Rate', 'Effect Res',
    'CRIT Rate', 'CRIT DMG',
    'SPD'
])
unwanted_flat_substats = set(['HP', 'ATK', 'DEF'])


# characters_url = 'https://www.prydwen.gg/star-rail/characters'
characters_url = 'https://www.prydwen.gg/star-rail/tier-list'
character_soup = BeautifulSoup(requests.get(characters_url).text, 'html.parser')

all_links = [a_tag for a_tag in character_soup.find_all('a')]
character_link_regex = re.compile(r'^/star-rail/characters/(.*)$')
character_matches = [(a_tag, character_link_regex.match(a_tag.get('href'))) for a_tag in all_links]
characters_to_tags = {match_.group(1): a_tag for a_tag, match_ in character_matches if match_ is not None}
characters = sorted(characters_to_tags)


characters_to_soups = dict()
for character in characters:
    print(f'Getting page for {character}')
    try:
        time.sleep(2)
        url = f'https://www.prydwen.gg/star-rail/characters/{character}'
        response = requests.get(url)
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
        characters_to_soups[character] = soup
    except Exception:
        print(f'\tFailed to get page for {character}')


def get_proper_name_of_main_stat(name: str):
    if name.lower() == 'anything':
        return 'Anything'
    main_stat_candidates = {main_stat for main_stat in all_possible_main_stats if main_stat not in ['HP', 'ATK']}
    try:
        name = difflib.get_close_matches(name, main_stat_candidates, n=1, cutoff=0.01)[0]
    except IndexError:
        return ''
    return name

def process_relic_main_stats(relic_stat_lists):
    relic_main_stats_dict = dict()
    for relic in relic_stat_lists:
        relic_main_stats_dict[relic[0]] = [name for name in [get_proper_name_of_main_stat(main_stat) for main_stat in relic[1:]] if name != '']
    return relic_main_stats_dict

def remove_prefix(text: str, prefix: str):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def check_if_substat_in_substat_desc(substat: str, substat_desc: str) -> bool:
    substat_desc = substat_desc.upper()
    alt_names = {
        'HP': 'HP%',
        'DEF': 'DEF%',
        'ATK': 'ATK%',
        'SPEED': 'SPD',
        'EFF RES': 'EFFECT RES',
        'EHR': 'EFFECT HIT RATE',
        'BREAK EFF': 'BREAK EFFECT'
    }
    for key, value in alt_names.items():
        substat_desc = substat_desc.replace(key, value)
    return substat.upper() in substat_desc

def merge_dictionaries(dicts: List[Dict[str, List]]) -> Dict[str, List]:
    merged_dict = defaultdict(set)

    for d in dicts:
        for key, value in d.items():
            merged_dict[key].update(value)

    return {key: sorted(values) for key, values in merged_dict.items()}


characters_to_relics = dict()
characters_to_main_stats = dict()
characters_to_substats = dict()
characters_to_urls = dict()
characters_to_imgs = dict()
characters_to_substat_desc = dict()

for character in characters_to_soups:

    soup = characters_to_soups[character]
    for script in soup(["script", "style"]):
        script.decompose()

    if "build information aren't available yet. They will be added when the character is released." in soup.get_text():
        continue

    character_name = soup.select('div.character-top strong')[0].get_text()

    all_relics = set(img_tag.get('alt', '') for build_relics_div in soup.find_all('div', class_='build-relics') for img_tag in build_relics_div.find_all('img'))
    all_relics.discard('')
    characters_to_relics[character_name] = all_relics

    main_stat_dicts = []
    for main_stat_info in soup.select('div.main-stats'):
        main_stat_dicts.append(process_relic_main_stats([main_stat_tag.find_all(string=True) for main_stat_tag in main_stat_info.select('div.box')]))
    characters_to_main_stats[character_name] = merge_dictionaries(main_stat_dicts)

    best_relic_substats = '\n'.join(
        [remove_prefix(o.text, 'Substats:')
         for o in soup.select('div.tab-inside')[2].select('div.build-stats div.sub-stats')
         if o.text.lower().startswith('substats:')
        ]
    )
    characters_to_substat_desc[character_name] = best_relic_substats
    characters_to_substats[character_name] = [substat for substat in all_possible_substats.difference(unwanted_flat_substats) if check_if_substat_in_substat_desc(substat, best_relic_substats)]

    characters_to_urls[character_name] = f'/star-rail/characters/{character}'
    characters_to_imgs[character_name] = characters_to_tags[character].select('img')[2].get('src')


def flatten_dictionary_to_tuples(d, parent_keys=None):
    if parent_keys is None:
        parent_keys = []
    items = []
    for key, value in d.items():
        current_keys = parent_keys + [key]
        if isinstance(value, dict):
            items.extend(flatten_dictionary_to_tuples(value, current_keys))
        elif isinstance(value, (list, set)):
            for element in value:
                items.append(current_keys + [element])
        else:
            items.append(current_keys + [value])
    return items


(
    pd.DataFrame(flatten_dictionary_to_tuples(characters_to_relics), columns=['Character', 'Relic Set'])
    .sort_values(by=['Character', 'Relic Set'])
    .to_csv('./tables/characters_to_relics.csv', index=False)
)


pd.DataFrame(flatten_dictionary_to_tuples(characters_to_main_stats), columns=['Character', 'Relic Piece', 'Main Stat']).to_csv('./tables/characters_to_main_stats.csv', index=False)


(
    pd.DataFrame(flatten_dictionary_to_tuples(characters_to_substats), columns=['Character', 'Substat'])
    .sort_values(by=['Character', 'Substat'])
    .to_csv('./tables/characters_to_substats.csv', index=False)
)


pd.DataFrame(flatten_dictionary_to_tuples(characters_to_urls), columns=['Character', 'URL']).to_csv('./tables/characters_to_urls.csv', index=False)


pd.DataFrame(flatten_dictionary_to_tuples(characters_to_imgs), columns=['Character', 'IMG']).to_csv('./tables/characters_to_imgs.csv', index=False)


relics_url = 'https://www.prydwen.gg/star-rail/guides/relic-sets'
relic_soup = BeautifulSoup(requests.get(relics_url).text, 'html.parser')


relics_to_imgs = {
    relic_box_tag.select('h4')[0].text: relic_box_tag.select('div.hsr-relic-image img')[2].get('src')
    for relic_box_tag in relic_soup.select('div.hsr-relic-box')
}
relics_to_desc = {
    relic_box_tag.select('h4')[0].text: '\n'.join([desc_tag.get_text().strip() for desc_tag in relic_box_tag.select('div.hsr-set-description')[0].select('div')])
    for relic_box_tag in relic_soup.select('div.hsr-relic-box')
}


pd.DataFrame(flatten_dictionary_to_tuples(relics_to_imgs), columns=['Relic Set', 'IMG']).to_csv('./tables/relics_to_imgs.csv', index=False)


pd.DataFrame(flatten_dictionary_to_tuples(relics_to_desc), columns=['Relic Set', 'DESCRIPTION']).to_csv('./tables/relics_to_desc.csv', index=False)


pd.DataFrame(flatten_dictionary_to_tuples(relic_pieces_to_possible_main_stats), columns=['Relic Piece', 'Main Stat']).to_csv('./tables/piece_to_main_stat.csv', index=False)


pd.DataFrame(flatten_dictionary_to_tuples(characters_to_substat_desc), columns=['Character', 'Substat INFO']).to_csv('./tables/characters_to_substat_desc.csv', index=False)

