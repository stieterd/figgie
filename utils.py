# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 17:46:51 2024

@author: 644794ph
"""

import json
import websocket

class TradingBot:
    
    def __init__(self):
        '''Config for the tradingbot'''
        pass
    
    @staticmethod
    def on_trade_event(round_data: dict, round_history: dict) -> dict:
        '''Gets called on each trade event'''
        ## Put your code here ##
        
        return {'Diamonds': ['Sell', 4], 'Hearts': ['Buy', 4], 'Spades': [], 'Clubs':[]}

    @staticmethod
    def data_collection(round_data:dict, round_history: dict) -> bool:
        '''Gets called at the end of each game'''
        ## Put your code here ##
        
        goal_suit = round_data['goal_suit']
        chips_and_hands = round_data['chips_and_hands']
        
        # return true if you want to terminate return false if you want to keep going
        return False

class FiggieGame:
    
    NBOTS = 4
    
    def __init__(self):
        self.header = {
            'Sec-Websocket-Extensions': 'permessage-deflate; client_max_window_bits',
            'Sec-Websocket-Key':'Y22XNEFUuyeyRyIEW77q7A==',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        self.lobby_data = {}
        
        self.wsapp = websocket.WebSocketApp("wss://europe.figgie.com/", header=self.header, on_message=self.on_message)
        self.wsapp.run_forever()

        
    @staticmethod
    def start_game(wsapp):
        wsapp.send(json.dumps(['Start_game']))
        
    @staticmethod
    def start_next_round(wsapp):
        wsapp.send(json.dumps(['Start_next_round']))
    
    @staticmethod
    def set_readyness(wsapp):
        wsapp.send(json.dumps(["Set_readiness",{"is_ready":True}]))

    @staticmethod
    def add_bot(wsapp):
        wsapp.send(json.dumps(["Add_bot"]))
        
    @staticmethod
    def set_display_name(wsapp):
        wsapp.send(json.dumps(["Set_display_name", "lalala"]))
    
    @staticmethod
    def create_lobby(wsapp):
        wsapp.send(json.dumps(["Create_lobby",{"settings":["Standard"]}]))

    @staticmethod
    def add_order(wsapp, direction: str, suit: str, price:int): # direction: Buy or Sell, suit: Diamonds, Clubs, Spades, Hearts
        wsapp.send(json.dumps(["Add_order",{"order":{"suit":[suit],"price":price,"direction":direction,"is_ioc":False}}]))
        
    def on_message(self, wsapp, message):
        
        message = json.loads(message)
        # print(message)
        
        if "Initial_connect" in message[0]:
            self.set_display_name(wsapp)
            self.create_lobby(wsapp)
        
        elif "Lobby" in message[0]:
            self.lobby_data = message[1]
            if self.lobby_data['is_startable'] and len(self.lobby_data['players_and_readiness']) > 1:
                self.start_game(wsapp)
                return
            
            self.set_readyness(wsapp)
            for x in range(self.NBOTS):
                self.add_bot(wsapp)
        
        elif "Live_round_for_player" in message[0]:
            round_data = message[1]['round']
            round_history = message[1]['round_history']
            orders = TradingBot.on_trade_event(round_data, round_history)
            for key, value in orders.items():
                if len(value) == 0:
                    continue
                
                self.add_order(wsapp, value[0], key, value[1])
        
        elif "End_of_round_summary" in message[0]:
            round_data = message[1]['round']
            round_history = message[1]['round_history']
            exit_term = TradingBot.data_collection(round_data, round_history)
            
            if not exit_term:
                self.start_next_round(wsapp)
            
            
if __name__ == "__main__":
    fg = FiggieGame()
    