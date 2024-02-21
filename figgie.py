# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 17:46:51 2024

@author: 644794ph
"""

import json
import random
import sys
import os

import pandas
import websocket
import traceback

from datetime import datetime
import pandas as pd


class TradingBot:
    n_games = 0


    ### KEEP THIS METHOD ###
    ##  insert your own code into it ##
    @staticmethod
    def on_trade_event(round_data: dict, round_history: dict) -> dict:
        '''
        :param round_data: dictionary containing the round data
        :param round_history: dictionary containing all the trades and orders
        :return: return a dictionary containing keys of suits you want to buy/sell: Diamonds, Hearts, Spades, Clubs

        this method gets called on each event of the game, like: new sell order, new buy order, new trade
        keep in mind that if you place a new buy order or sell order, you will trigger this event too

        example of return:
            A dictionary looking like: {'Diamonds': {'Sell': 5, 'Buy': 1}, 'Hearts': {'Buy': 2}}
            if you want to place a Sell order on diamonds for 5 and a buy order on diamonds for 1 and a buy order on hearts for 2
        '''

        try:

            ## Place your code here ##

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in on_trade_event')


    ### KEEP THIS METHOD ###
    ##  insert your own code into it ##
    @staticmethod
    def on_data_collection(round_data: dict, round_history: dict) -> bool:
        '''
        :param round_data: dictionary containing the round data
        :param round_history: dictionary containing all the trades and orders
        :return: return a boolean representing the exit term
            true: another round to start
            false: stop game

        this method gets called on the end of each round, you can use this to collect all the statistics of the
        previously played round
        '''

        try:

            ## place your code here ##

            # return true if you want to terminate return false if you want to keep going
            return False
        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in data_collection')

class FiggieGame:
    NBOTS = 4
    DISPLAY_NAME = "pjotr"
    ROUND_LENGTH_SECONDS = 240  # seconds a round takes

    def __init__(self):
        self.header = {
            'Sec-Websocket-Extensions': 'permessage-deflate; client_max_window_bits',
            'Sec-Websocket-Key': 'B6piFIxKZM3YzCoLy6GFXUM9DKw=',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        self.lobby_data = {}

        self.wsapp = websocket.WebSocketApp("wss://europe.figgie.com/", header=self.header, on_message=self.on_message)
        self.wsapp.run_forever()

        self.last_order = {}

    @staticmethod
    def start_game(wsapp):
        wsapp.send(json.dumps(['Start_game']))

    @staticmethod
    def start_next_round(wsapp):
        wsapp.send(json.dumps(['Start_next_round']))

    @staticmethod
    def set_readyness(wsapp):
        wsapp.send(json.dumps(["Set_readiness", {"is_ready": True}]))

    @staticmethod
    def add_bot(wsapp):
        wsapp.send(json.dumps(["Add_bot"]))

    @staticmethod
    def set_display_name(wsapp):
        wsapp.send(json.dumps(["Set_display_name", FiggieGame.DISPLAY_NAME]))

    @staticmethod
    def create_lobby(wsapp):
        wsapp.send(json.dumps(["Create_lobby", {"settings": ["Standard"]}]))

    @staticmethod
    def join_lobby(wsapp, lobby_id: str):
        wsapp.send(json.dumps(["Join_lobby_as_player", {"id": lobby_id}]))

    @staticmethod
    def add_order(wsapp, direction: str, suit: str,
                  price: int):  # direction: Buy or Sell, suit: Diamonds, Clubs, Spades, Hearts
        wsapp.send(json.dumps(
            ["Add_order",
             {"order": {"suit": [str(suit)], "price": int(price), "direction": str(direction), "is_ioc": False}}]))

    # @staticmethod
    # def cancel_order(wsapp, direction: str, suit: str,
    #                  price: int):  # direction: Buy or Sell, suit: Diamonds, Clubs, Spades, Hearts
    #     wsapp.send(json.dumps(
    #         ["Cancel_order", {"order": {"suit": [suit], "price": price, "direction": direction, "is_ioc": False}}]))

    def on_message(self, wsapp, message):
        message = json.loads(message)

        if "Initial_connect" in message[0].strip():
            self.set_display_name(wsapp)
            print("creating lobby")
            self.create_lobby(wsapp)
            print('lobby created')

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

            try:
                orders = TradingBot.on_trade_event(round_data, round_history)

                for key, value in orders.items():
                    if len(value) == 0:
                        continue
                    suit = key

                    for direction, price in value.items():
                        veto = False
                        for market in round_data['markets']:
                            if price == 0:
                                veto = True
                                break

                            if [suit] != market[0]:
                                continue

                            way = 'bid' if direction == "Buy" else 'offer'
                            if market[1][way] is None:
                                continue

                            if direction == "Sell" and int(market[1][way]['price']) <= int(price):
                                veto = True
                            elif direction == "Buy" and int(market[1][way]['price']) >= int(price):
                                veto = True

                        if not veto:
                            self.add_order(wsapp, direction, suit, price)

                self.last_order = orders

            except Exception as e:
                print(traceback.format_exc())
                sys.exit()

        elif "End_of_round_summary" in message[0]:
            round_data = message[1]['round']
            round_history = message[1]['round_history']
            try:
                exit_term = TradingBot.on_data_collection(round_data, round_history)
            except Exception as e:
                print(traceback.format_exc())
                sys.exit()

            if not exit_term:
                self.start_next_round(wsapp)
            else:
                sys.exit()


if __name__ == "__main__":
    fg = FiggieGame()
