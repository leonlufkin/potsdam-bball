import numpy as np
import pandas as pd
from utils import parse_args, mkdir

if __name__ == '__main__':
    args = parse_args()

    shot_chart = pd.read_csv('data/shot_chart_2022.csv')
    names = [head for head in shot_chart.columns if head not in ['Game'] and not head.startswith("Unnamed")]
    players = {}

    for name in names:
        player_shots = shot_chart[name].dropna()
        player_shots = player_shots[player_shots != "AND ONE"].apply(lambda x: x.strip().split(" "))
        player_shots = pd.DataFrame.from_dict(dict(zip(player_shots.index, player_shots.values))).T.reset_index(drop=True).rename(columns={0: 'region', 1: 'type'})
        player_shots['region'] = player_shots['region'].astype(int)
        # FIX THE FOLLOWING LINE TO HANDLE FREE THROWS!
        shot_type = player_shots['type']
        player_shots['fts'] = (shot_type == 'FT').astype(int) + (shot_type == '1FT').astype(int) + (shot_type == '2FT').astype(int)
        player_shots['made'] = (shot_type == 'M').astype(int)
        player_shots['att'] = (shot_type == 'A').astype(int) + player_shots['made']
        player_shots['att with fts'] = player_shots['att'] + player_shots['fts']
        stats = player_shots.groupby('region').sum().reset_index()
        stats['avg with ft'] = round(100 * (stats['made'] + stats['fts']) / stats['att with fts'], 1)
        stats['avg without ft'] = round(100 * stats['made'] / stats['att'], 1)
        players.update({name: stats})

    pdam = pd.concat([stats for player, stats in players.items() if player != "Enemy"], axis=0).groupby('region').sum().reset_index()
    pdam['avg with ft'] = round(100 * (pdam['made'] + pdam['fts']) / pdam['att with fts'], 1)
    pdam['avg without ft'] = round(100 * pdam['made'] / pdam['att'], 1)
    players.update({"Potsdam": pdam})

    writer = pd.ExcelWriter(mkdir('results/') + args.data_file.split('/')[-1].replace('.csv', '.xlsx'), engine='openpyxl')
    for player, stats in players.items():
        stats.to_excel(writer, sheet_name=player, index=False)
    writer.save()