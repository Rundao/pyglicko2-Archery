import datetime
import json
import math
import binascii, hashlib
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os

from glicko2 import Glicko2

def ymd2mjd(time):
    '''
    Convert datetime to Modified Julian Date
    '''
    return time.toordinal() - 678576

def mjd2ymd(mjd):
    '''
    Convert Modified Julian Date to datetime
    '''
    t_ymd = datetime.datetime.fromordinal(mjd + 678576)
    return t_ymd.year, t_ymd.month, t_ymd.day

# def get_time_input():
#     '''
#     Get competition time from user

#     Returns:
#         datetime: competition time
#     '''
#     Flag = 'n'
#     while Flag == 'n':
#         t_comp_str = input("Enter competition time like 2023-03-06: ")
#         t_comp = datetime.datetime.strptime(t_comp_str, "%Y-%m-%d")
#         Flag = input("Is the time {}-{}-{} correct? (y/n): ".format(t_comp.year, t_comp.month, t_comp.day))
#     return t_comp

def add_new_env(env_name='ArcheryTeam', path='./Data/'):
    '''
    Add new environment

    Args:
        env_name (str, optional): group name. Defaults to 'ArcheryTeam'.
        path (str, optional): path to data folder. Defaults to './Data/'.
    '''
    path = path + env_name + '/'
    # create folder
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.exists(path+'Score/'):
        os.makedirs(path+'Score/')
    # create unHashMap.json
    with open(path+'unHashMap.json', 'w') as f:
        json.dump({}, f, ensure_ascii=False, indent=4)
    # create DataAbstract.json
    with open(path+'DataAbstract.json', 'w') as f:
        json.dump({}, f, ensure_ascii=False, indent=4)
    # create MatchLog.csv
    with open(path+'MatchLog.csv', 'w') as f:
        f.write('t_comp_mjd,Rank1,Name1,JoinYear1,Rank2,...\n')
    return

class DataSolver:
    def __init__(self, env_name='ArcheryTeam', data_path='/Data/', c=18) -> None:
        '''
        Init

        Args:
            env_name (str, optional): group name. Defaults to 'ArcheryTeam'.
            data_path (str, optional): path to data folder. Defaults to '/Data/'.
            c (int, optional): RD_new = min(sqrt(RD^2 + c^2 * delta_t), 350). Defaults to 18.
        '''
        abs_path = os.path.dirname(os.path.abspath(__file__))
        self.__path = abs_path + data_path + env_name + '/'
        self.__path_score = self.__path + 'Score/'
        self.__Glicko2 = Glicko2(tau=0.5)
        self.__c2 = c*c # phi_new = min(sqrt(phi^2 + c^2 * delta_t), 350)
        with open(self.__path+'unHashMap.json', 'r', encoding='utf-8') as f:
            self.__unHashMap = json.load(f)   # name -> id(s)
        with open(self.__path+'DataAbstract.json', 'r', encoding='utf-8') as f:
            self.__player_data = json.load(f) # id -> data
        
        self.__t_today_mjd = ymd2mjd(datetime.datetime.now())
        self.__t_comp_mjd = ymd2mjd(datetime.datetime.now())
        return
    
    def set_t_comp_input(self):
        '''
        Set competition time
        '''
        str_in = input("Enter competition time like 2023-03-06: ")
        t_comp = datetime.datetime.strptime(str_in, "%Y-%m-%d")
        self.__t_comp_mjd = ymd2mjd(t_comp)
        return
    
    def __player2hash(self, name, joinYear):
        '''
        Convert player name to hash

        Args:
            name (str): player name
            joinYear (str): join year, like '22s' for 2022 spring

        Returns:
            str: md5 hash of name and joinYear
        '''
        return hashlib.md5(''.join([name, joinYear]).encode('utf-8')
                           ).hexdigest()
    
    def __player2hex(self, name):
        '''
        Convert player name to hex

        Args:
            name (str): player name

        Returns:
            str: hex of name
        '''
        return name.encode('utf-8').hex()
    
    def add_new_player(self, player, joinYear):
        '''
        Add new player

        Args:
            player (str): player name
            joinYear (str): join year, like '22s' for 2022 spring
        '''
        player_hex = self.__player2hex(player)
        player_id = self.__player2hash(player, joinYear)
        # check if player exists
        if player_id in self.__player_data:
            print("Player {} already exists.".format(player))
            return
        # add player
        if player_hex not in self.__unHashMap:
            self.__unHashMap[player_hex] = []
        player_data = {}
        player_data['Name'] = player
        player_data['JoinYear'] = joinYear
        player_data['LastActive_MJD'] = self.__t_comp_mjd
        player_data['Rating'] = 1500
        player_data['RD'] = 350
        player_data['sigma'] = 0.06
        # update unHashMap and player_data
        self.__unHashMap[player_hex].append(player_id)
        self.__player_data[player_id] = player_data
        # save to file
        with open(self.__path+'unHashMap.json', 'w') as f:
            json.dump(self.__unHashMap, f, indent=4)
        with open(self.__path+'DataAbstract.json', 'w') as f:
            json.dump(self.__player_data, f, ensure_ascii=False, indent=4)
        with open(self.__path_score+player_id+'.csv', 'w') as f:
            f.write('t_comp_mjd,Rating,RatingDeviation,Volatility\n')
            f.write('{},{},{},{}\n'.format(
                self.__t_comp_mjd, player_data['Rating'],
                player_data['RD'], player_data['sigma']))
        return player_id, player_data

    
    def __load_player(self, player, id=None):
        '''
        Load player data. 
        Update score if exists, 
        else create new player, add to unHashMap and player_data

        Args:
            player (str): player name
            id (str, optional): player id if known. Defaults to None.
        '''
        # get player id if player is in the data
        Flag_unHashMap_updated = True
        player_hex = self.__player2hex(player)
        if player_hex in self.__unHashMap:
            # 排除重名的情况，找到对应的id(md5 hash)
            if (id == None) & (len(self.__unHashMap[player_hex]) > 1):
                print("Player {} has more than one id.".format(player))
                for id in self.__unHashMap[player_hex]:
                    name = self.__player_data[id]['Name']
                    join_year = self.__player_data[id]['JoinYear']
                    Flag = input("Is {}(Join in {}) the player you want? (y/n): ".format(name, join_year))
                    if Flag == 'y':
                        Flag_unHashMap_updated = False
                        break
            else:
                if id == None:
                    id = self.__unHashMap[player_hex][0]
                Flag_unHashMap_updated = False
        # create or update player data dict
        if Flag_unHashMap_updated:  # add new player
            join_year = input("Enter {}'s join year and season (24s/23f): ".format(player))
            id, player_data = self.add_new_player(player, join_year)
        else:
            player_data = self.__player_data[id]
            delta_t = self.__t_comp_mjd - player_data['LastActive_MJD']
            delta_t = delta_t if delta_t > 0 else 0
            player_data['RD'] = min(350,
                math.sqrt(math.pow(player_data['RD'], 2) + self.__c2 * delta_t))
            player_data['LastActive_MJD'] = self.__t_comp_mjd
        
        return id, player_data
    
    def __update_player_by_match(self, match_result:list):
        '''
        Update player data by match result

        Args:
            match_result (list): [[rank, id, player_score], ...]
                where:  player_score = self.__Glicko2.create_rating(
                            mu = Rating,
                            phi = RD,
                            sigma = sigma
                        )
                is updated by t_comp_mjd
        '''
        match_result_new = []
        for i in range(len(match_result)):
            rank, id, player_score = match_result[i]
            opponent_list = []
            for j in range(len(match_result)):
                if i == j:
                    continue
                rank_, id_, player_score_ = match_result[j]
                if rank > rank_:
                    winORlose = 0
                elif rank < rank_:
                    winORlose = 1
                else:
                    winORlose = 0.5
                opponent_list.append([winORlose, player_score_])
            match_result_new.append([id, player_score, 
                    self.__Glicko2.rate(player_score, opponent_list)])
        
        for id, player_score, player_score_new in match_result_new:
            self.__player_data[id]['Rating'] = player_score_new.mu
            self.__player_data[id]['RD'] = player_score_new.phi
            self.__player_data[id]['sigma'] = player_score_new.sigma
            self.__player_data[id]['LastActive_MJD'] = self.__t_comp_mjd
            # write player score history
            with open(self.__path_score+id+'.csv', 'a') as f:
                f.write('{},{},{},{}\n'.format(
                    self.__t_comp_mjd, player_score_new.mu,
                    player_score_new.phi, player_score_new.sigma))
        with open(self.__path+'DataAbstract.json', 'w', encoding='utf-8') as f:
            json.dump(self.__player_data, f, ensure_ascii=False, indent=4)


    def add_match_file(self):
        '''
        Add match result from file
        '''
        # input match result
        root = tk.Tk()
        root.withdraw()
        file_comp = filedialog.askopenfilename()
        df_comp = pd.read_excel(file_comp)
        t_comp_timestamp = df_comp.loc[0, '时间']
        self.__t_comp_mjd = ymd2mjd(
            datetime.datetime.fromtimestamp(t_comp_timestamp.timestamp()))
        match_range = []
        for i in range(len(df_comp)):
            rank, player_str = int(df_comp.loc[i, '排名']), df_comp.loc[i, '姓名']
            print("Rank: {}, Name: {}, ".format(rank, player_str))
            match_range.append([rank, player_str])
        print("Match on {}.".format(mjd2ymd(self.__t_comp_mjd)))
        if input("Is the match result above correct? (y/n): ") != 'y':
            print("Match result input cancelled, please check the file.")
            return
        match_result = []
        for i in range(len(match_range)):
            rank, player_str = match_range[i]
            id, player_data = self.__load_player(player_str)
            player_score = self.__Glicko2.create_rating(
                mu = player_data['Rating'],
                phi = player_data['RD'],
                sigma = player_data['sigma']
            )
            match_result.append([rank, id, player_score])

        # write match log
        with open(self.__path+'MatchLog.csv', 'a', encoding='utf-8') as f:
            str_write = ''
            str_write += str(self.__t_comp_mjd)
            for i in range(len(match_range)):
                rank, player_str = match_range[i]
                id = match_result[i][1]
                str_write += ',' + str(rank)
                str_write += ',' + player_str
                str_write += ',' + self.__player_data[id]['JoinYear']
            str_write += '\n'
            f.write(str_write)
        
        # update player data
        self.__update_player_by_match(match_result)
        print("Match result added.")
        return
    
    def regenerate_from_match_log(self):
        '''
        Regenerate player data and score history from match log
        '''
        # initial DataAbstract and ScoreHistory
        for file in os.listdir(self.__path_score):
            if file.endswith('.csv'):
                with open(self.__path_score+file, 'w') as f:
                    f.write('t_comp_mjd,Rating,RatingDeviation,Volatility\n')
        with open(self.__path+'DataAbstract.json', 'r', encoding='utf-8') as f:
            self.__player_data = json.load(f)
        for id in self.__player_data:
            self.__player_data[id]['Rating'] = 1500
            self.__player_data[id]['RD'] = 350
            self.__player_data[id]['sigma'] = 0.06
            self.__player_data[id]['LastActive_MJD'] = 60000

        # read match log 
        with open(self.__path+'MatchLog.csv', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i in range(1, len(lines)):
                line = lines[i][:-1].split(',')
                self.__t_comp_mjd = int(line[0])
                n_player = len(line)//3
                # load player data and update RD
                match_result = []
                for j in range(n_player):
                    rank = int(line[3*j+1])
                    player_str = line[3*j+2]
                    join_year = line[3*j+3]
                    id = self.__player2hash(player_str, join_year)
                    id, player_data = self.__load_player(player_str, id)
                    player_score = self.__Glicko2.create_rating(
                        mu = player_data['Rating'],
                        phi = player_data['RD'],
                        sigma = player_data['sigma']
                    )
                    match_result.append([rank, id, player_score])
                self.__update_player_by_match(match_result)
        print("Player data regenerated.")
        return
    
    # TODO: 加一个预测胜率的函数
    def predict_win_rate(self, player1, player2=Glicko2().create_rating()):
        '''
        Predict win rate of player1 against player2

        Args:
            player1 (Rating class): Rating paras of player1
            player2 (Rating class, optional): Rating paras of player2. Defaults to Glicko2.create_rating().

        Returns:
            float: Predicted win rate of player1
        '''
        return 0.5
    
    def export_score(self, active_only=True, active_days=180):
        '''
        Export player score to excel file

        Args:
            active_only (bool, optional): Export recent active or all players. 
                Defaults to True.
            active_days (int, optional): Active judgement days. Defaults to 180.
        '''
        # input export file name
        root = tk.Tk()
        root.withdraw()
        file_name = filedialog.asksaveasfilename(
            initialfile='ScoreExport-{:04d}{:02d}{:02d}.xlsx'.format(
                *mjd2ymd(self.__t_comp_mjd)))
        if file_name == '':
            print("Export cancelled.")
            return
        # export player score
        df_score = pd.DataFrame(columns=['Name', 'JoinYear', 'SinceLastActive', 
                                         'R95Lower', 'R95Upper', 'Rating',
                                         'RatingDeviation', 'Volatility'])
        for id in self.__player_data:
            player_data = self.__player_data[id]
            delta_t = self.__t_comp_mjd - player_data['LastActive_MJD']
            delta_t = delta_t if delta_t > 0 else 0
            if active_only:
                if delta_t > active_days:
                    continue
            RD_update = min(350, 
                math.sqrt(math.pow(player_data['RD'], 2) + self.__c2 * delta_t))
            df_score = df_score.append({
                'Name': player_data['Name'],
                'JoinYear': player_data['JoinYear'],
                'SinceLastActive': self.__t_comp_mjd - player_data['LastActive_MJD'],
                'Rating': player_data['Rating'],
                'RatingDeviation': RD_update,
                'Volatility': player_data['sigma'],
                'R95Lower': player_data['Rating'] - 2*RD_update,
                'R95Upper': player_data['Rating'] + 2*RD_update
            }, ignore_index=True)
        df_score = df_score.sort_values(by=['R95Lower'], ascending=False)
        df_score.to_excel(file_name, index=False)
        print("Score exported to {} on {:4d}-{:02d}-{:02d}".format(
            file_name, *mjd2ymd(self.__t_comp_mjd)))
        return