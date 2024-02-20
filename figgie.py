# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 17:46:51 2024

@author: 644794ph
"""

import json
import sys

import websocket
import traceback


class TradingBot:

    def __init__(self):
        '''Config for the tradingbot'''
        pass

    @staticmethod
    def parse_hand(round_data):
        try:
            for user in round_data['chips_and_hands']:
                if user['user']['display_name'] == FiggieGame.DISPLAY_NAME:
                    hand = {item[0][0]: item[1] for item in user['hand']}
            return hand

        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in parse_hand')

    @staticmethod
    def parse_orders(round_data):
        try:
            bid_offer_prices = {"offer": [], "bid": []}

            for item in round_data['markets']:
                bid_info = item[1]["bid"]
                offer_info = item[1]["offer"]

                if bid_info != None:
                    bid_dict = {"suit": item[0][0], "display_name": bid_info["user"]["display_name"], "price": bid_info["price"]}
                    bid_offer_prices["bid"].append(bid_dict)

                if offer_info != None:
                    offer_dict = {"suit": item[0][0], "display_name": offer_info["user"]["display_name"], "price": offer_info["price"]}
                    bid_offer_prices["offer"].append(offer_dict)

            return bid_offer_prices
        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in parse_orders')

    @staticmethod
    def on_trade_event(round_data: dict, round_history: dict) -> dict:
        '''Gets called on each trade event'''
        try:
            return {'Diamonds': {'Buy': 0, 'Sell': 8}, 'Hearts': {'Buy': 4, 'Sell': 8}, 'Spades': {'Buy': 4, 'Sell': 4}, 'Clubs': {'Buy': 4, 'Sell': 0}}

        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in on_trade_event')

    @staticmethod
    def data_collection(round_data: dict, round_history: dict) -> bool:
        '''Gets called at the end of each game'''
        ## Put your code here ##
        try:

            goal_suit = round_data['goal_suit']
            chips_and_hands = round_data['chips_and_hands']

            # return true if you want to terminate return false if you want to keep going
            return False
        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in data_collection')


class FiggieGame:
    NBOTS = 4
    DISPLAY_NAME = "pjotr"

    def __init__(self):
        self.header = {
            'Sec-Websocket-Extensions': 'permessage-deflate; client_max_window_bits',
            'Sec-Websocket-Key': 'B6piFIxKZM3YzCoLy6GFXUM9DKw=',
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
    def add_order(wsapp, direction: str, suit: str,
                  price: int):  # direction: Buy or Sell, suit: Diamonds, Clubs, Spades, Hearts
        wsapp.send(json.dumps(
            ["Add_order", {"order": {"suit": [suit], "price": price, "direction": direction, "is_ioc": False}}]))

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

                            if direction == "Sell" and market[1][way]['price'] <= price:
                                veto = True
                            elif direction == "Buy" and market[1][way]['price'] >= price:
                                veto = True

                        if not veto:
                            self.add_order(wsapp, direction, suit, price)
            except Exception as e:
                print(traceback.format_exc())
                print(market[1][way]['user'])
                sys.exit()

        elif "End_of_round_summary" in message[0]:
            round_data = message[1]['round']
            round_history = message[1]['round_history']
            try:
                exit_term = TradingBot.data_collection(round_data, round_history)
            except Exception as e:
                print(traceback.format_exc())
                sys.exit()

            if not exit_term:
                self.start_next_round(wsapp)


if __name__ == "__main__":
    fg = FiggieGame()
