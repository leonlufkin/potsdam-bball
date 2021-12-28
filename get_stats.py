import numpy as np
import pandas as pd
from utils import parse_args, mkdir

class PlayerEvent:
    def __init__(self, time, player=None, action=None, home_pts=0, enemy_pts=0):
        self.time = time
        self.player = player
        self.action = action
        self.home_pts = home_pts
        self.enemy_pts = enemy_pts

    def update(self, time=None, player=None, action=None, home_pts=0, enemy_pts=0):
        if time is not None:
            self.time = time
        if player is not None:
            self.player = player
        if action is not None:
            self.action = action
        if home_pts > 0:
            self.home_pts = home_pts
        if enemy_pts > 0:
            self.enemy_pts = enemy_pts
    
    def reset(self):
        self.player = None
        self.action = None
        self.home_pts = 0
        self.enemy_pts = 0

class TeamEvent:
    def __init__(self, names, time) -> None:
        self.names = names
        self.time = time
        self.actions = {name : None for name in names}
        self.home_pts = 0
        self.enemy_pts = 0

    def readline(self, line: str):
        entries = line.split(',')
        self.update_time(entries[0])
        self.update_home_score(entries[1])
        self.update_enemy_score(entries[2])
        for i, player in enumerate(self.names):
            self.update_player(player, entries[3+i])

    def update_time(self, time: str):
        if time != "":
            try:
                self.time = (np.array([float(x) for x in time.strip().split(":")]) * np.array([1, 1/60])).sum()
            except:
                print(time)
                raise ValueError("cannot convert time: {}".format(time.strip()))

    def update_home_score(self, pts: str):
        if pts != "":
            self.home_pts = int(pts)
        else:
            self.home_pts = 0

    def update_enemy_score(self, pts: str):
        if pts != "":
            self.enemy_pts = int(pts)
        else:
            self.enemy_pts = 0

    def update_player(self, player, update: str):
        if update == "":
            self.actions[player] = None
        else:
            self.actions[player] = update.strip().lower()

    def get_player_event(self, name):
        event = PlayerEvent(self.time, player=name, action=self.actions[name], home_pts=self.home_pts, enemy_pts=self.enemy_pts)
        return event


class Player:
    def __init__(self, name):
        self.name = name
        self.reset_time()
        self.reset_points()
        self.reset_actions()

    def reset_time(self):
        self.in_time = 0
        self.out_time = 0
        self.playtime = 0

    def reset_points(self):
        self.plus_minus = 0
        self.made_2p = 0
        self.made_3p = 0
        self.made_fg = 0
        self.made_ft = 0
        self.made_pts = 0
        self.att_2p = 0
        self.att_3p = 0
        self.att_fg = 0
        self.att_ft = 0
        self.att_pts = 0

    def reset_actions(self):
        self.rebounds = 0
        self.assists = 0
        self.steals = 0
        self.blocks = 0
        self.turnovers = 0
        self.on_court = False

    def reset_stats(self):
        self.reset_time()
        self.reset_points()
        self.reset_actions()

    def sub_in(self, time):
        if not self.on_court:
            # print("player wasn't on court, getting subbed in!")
            self.in_time = time
            self.on_court = True
        else:
            raise ValueError("{} is already on the court, cannot sub back in at {:.2f}".format(self.name, time))

    def sub_out(self, time):
        if self.on_court:
            self.out_time = time
            self.on_court = False
            self.update_playtime()
        else:
            raise ValueError("{} is not on the court, cannot sub out at {:.2f}".format(self.name, time))

    def update_playtime(self):
        self.playtime += self.in_time - self.out_time
        self.in_time = 0
        self.out_time = 0

    def home_score(self, pts):
        self.plus_minus += pts

    def enemy_score(self, pts):
        self.plus_minus -= pts

    def scored_2p(self):
        self.made_2p += 1
        self.att_2p += 1
        self.made_fg += 1
        self.att_fg += 1
        self.made_pts += 2
        self.att_pts += 2

    def missed_2p(self):
        self.att_2p += 1
        self.att_fg += 1
        self.att_pts += 2

    def scored_3p(self):
        self.made_3p += 1
        self.att_3p += 1
        self.made_fg += 1
        self.att_fg += 1
        self.made_pts += 3
        self.att_pts += 3

    def missed_3p(self):
        self.att_3p += 1
        self.att_fg += 1
        self.att_pts += 3

    def scored_ft(self):
        self.made_ft += 1
        self.att_ft += 1
        self.made_pts += 1

    def missed_ft(self):
        self.att_ft += 1
        self.att_pts += 1

    def action_taken(self, action: str):
        if action == "2p made":
            self.scored_2p()
        elif action.startswith("2p") and "attempt" in action:
            self.missed_2p()
        elif action == "3p made":
            self.scored_3p()
        elif action.startswith("3p") and "attempt" in action:
            self.missed_3p()
        elif action == "turnover":
            self.turnovers += 1
        elif action == "rebound":
            self.rebounds += 1
        elif action == "steal":
            self.steals += 1
        elif action.startswith("assist"):
            self.assists += 1
        elif action.startswith("block"):
            self.blocks += 1
        else:
            return ValueError("action {} not recognized!".format(action))

    def event_occurred(self, event: PlayerEvent):
        # print("{}: {}".format(event.player, event.action))
        if event.player == self.name:
            if event.action is not None:
                # print("{} has an action!".format(event.player))
                if event.action == "in":
                    # print("{} got subbed in!".format(event.player))
                    self.sub_in(event.time)
                elif event.action == "out":
                    self.sub_out(event.time)
                elif event.action.endswith("ft"):
                    num_fts = int(event.action[0])
                    fts_made = event.home_pts
                    fts_missed = num_fts - event.home_pts
                    for _ in range(fts_made):
                        self.scored_ft()
                    for _ in range(fts_missed):
                        self.missed_ft()
                else:
                    self.action_taken(event.action)
        if self.on_court:
            if event.home_pts > 0:
                self.home_score(event.home_pts)
            if event.enemy_pts > 0:
                self.enemy_score(event.enemy_pts)

    def get_box_stats(self) -> pd.Series:
        stat_names = ['name', 'playtime', 'pts scored', 'att fg', 'made fg', 'att 2p', 'made 2p', 'att 3p', 'made 3p', 'rebounds', 'assists', 'steals', 'blocks', 'att ft', 'made ft', 'turnovers', 'possessions', '+/-']
        stats = [self.name, self.playtime, self.made_pts, self.att_fg, self.made_fg, self.att_2p, self.made_2p, self.att_3p, self.made_3p, self.rebounds, self.assists, self.steals, self.blocks, self.att_ft, self.made_ft, self.turnovers, self.turnovers + self.att_fg, self.plus_minus]
        box_stats = pd.Series(stats, index=stat_names)
        return box_stats
        
class Team:
    def __init__(self, names) -> None:
        self.players = [Player(name) for name in names]
    
    def event_occured(self, event: TeamEvent):
        for player in self.players:
            player.event_occurred(event.get_player_event(player.name))

    def quarter_ended(self):
        for player in self.players:
            if player.on_court:
                player.event_occurred(PlayerEvent(time=0, player=player.name, action="out"))
        
    def get_box_stats(self) -> pd.DataFrame:
        player_stats = [player.get_box_stats() for player in self.players]
        team_stats = pd.DataFrame(player_stats)
        return team_stats

    def reset_team(self):
        for player in self.players:
            player.reset_stats()

if __name__ == '__main__':
    args = parse_args()

    f = open(args.data_file)
    headers = f.readline()
    names = [head for head in headers.strip("\n").split(",") if head.lower() not in ['time', 'potsdam score', 'enemy score', 'game']]

    pdam = Team(names)
    team_event = TeamEvent(names, None)
    stats = {}

    line = f.readline().strip("\n")
    while line:
        if line.strip(",") == "":
            line = f.readline().strip("\n")
        elif line.startswith("Q1"):
            # print(line)
            game = int(line[-1])
            print("game: {:d}".format(game))
            line = f.readline().strip("\n")
        # case when line is just name of opposing school
        elif ":" not in line:
            print(line.strip(","))
            line = f.readline().strip("\n")
        else:
            while line.endswith(str(game)):
                if line.startswith("Q"):
                    pdam.quarter_ended()
                else:
                    team_event.readline(line)
                    pdam.event_occured(team_event)
                line = f.readline().strip("\n")
                # print(line)
            pdam.quarter_ended()
            box_stats = pdam.get_box_stats().sort_values(by=['name'])
            box_stats['game'] = game
            stats.update({game: box_stats})
            pdam.reset_team()
            # print("updated game stats")

    game_stats = pd.concat(stats.values())
    all_game_stats = game_stats.groupby('name').sum().reset_index().drop(columns=['game'])
    per_game_stats = game_stats.groupby('name').mean().drop(columns=['game']).add_suffix(" per game").reset_index()
    stats[0] = all_game_stats.merge(per_game_stats, on='name')

    ft_weight = 0.5 # 0.44
    for game, stat in stats.items():
        # percentage stats
        stat['2p %'] = 100 * stat['made 2p'] / stat['att 2p']
        stat['3p %'] = 100 * stat['made 3p'] / stat['att 3p']
        stat['fg %'] = 100 * stat['made fg'] / stat['att fg']
        stat['ft %'] = 100 * stat['made ft'] / stat['att ft']
        stat['TS %'] = 100 * stat['pts scored']/2/(stat['att fg'] + ft_weight*stat['att ft'])

        # per 32 stats
        stat['+/- per 32'] = 32 * stat['+/-'] / stat['playtime']
        stat['made ft'] = stat['']
        stat['possessions per 32'] = 32 * stat['possessions'] / stat['playtime']
        
        # advanced stats
        stat['PER'] = (stat['made fg']*85.910 + stat['steals']*53.897 + stat['made 3p']*51.757 + stat['made ft']*46.845 + stat['blocks']*39.190 + stat['rebounds']*18.7875 + stat['assists']*34.677 - (stat['att ft']-stat['made ft'])*20.091 - (stat['att fg']-stat['made fg'])*20.091 - stat['turnovers']) / stat['playtime']

        # stats using whole team's data
        stat['usage rate'] = 100 * ((stat['att fg'] + ft_weight*stat['att ft'] + stat['turnovers']) * (stat['playtime'].sum() / 5)) / ((stat['att fg'].sum() + ft_weight*stat['att ft'].sum() + stat['turnovers'].sum()) * stat['playtime'])

    writer = pd.ExcelWriter(mkdir('results/') + args.data_file.split('/')[-1].replace('.csv', '.xlsx'), engine='openpyxl')
    for game, stat in stats.items():
        if game == 0:
            df_name = "season"
        else:
            df_name = "game {:d}".format(game)
        stat.round(decimals=1).to_excel(writer, sheet_name=df_name, index=False)
    writer.save()