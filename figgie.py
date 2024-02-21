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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.animation as animation

from datetime import datetime
import pandas as pd


class TradingBot:
    n_games = 0

    @staticmethod
    def on_trade_event(round_data: dict, round_history: dict) -> dict:
        '''Gets called on each trade event'''
        try:

            current_orders = TradingBot.parse_current_orders(round_data)
            hand = TradingBot.parse_current_hand(round_data)

            result_bids = {'Diamonds': {}, 'Hearts': {},
                           'Spades': {}, 'Clubs': {}}

            # progress in percentages
            game_progress = 1 - TradingBot.event_call_time_left(round_data, round_history) / 240
            turning_point = 0.25

            sell_price = max(15 - game_progress * 12, 5) if game_progress < 0.90 else 2
            buy_price = 3

            if game_progress > turning_point:
                for key in result_bids.keys():
                    result_bids[key]['Sell'] = sell_price

            for key in result_bids.keys():
                cur_buy_price = buy_price
                for order in current_orders['offer']:
                    if order['suit'] == key:
                        if order['price'] <= 6 and order[
                            'display_name'] != FiggieGame.DISPLAY_NAME and game_progress < turning_point:
                            cur_buy_price = order['price']
                            break

                if game_progress < 0.80:
                    if hand[key] < 5:
                        result_bids[key]['Buy'] = cur_buy_price

            # print(history_stats)
            print(current_orders)
            # print(hand)
            print(result_bids)

            # 0 means no actions, so if buy is 0 you are not buying
            return result_bids  # {'Diamonds': {'Buy': 0, 'Sell': 8}, 'Hearts': {'Buy': 4, 'Sell': 8}, 'Spades': {'Buy': 4, 'Sell': 4}, 'Clubs': {'Buy': 4, 'Sell': 0}}

        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in on_trade_event')

    @staticmethod
    def on_data_collection(round_data: dict, round_history: dict) -> bool:
        '''Gets called at the end of each game'''
        ## Put your code here ##
        try:
            goal_suit = round_data['goal_suit'][0]
            TradingBot.n_games += 1

            TradingBot.draw_current_timeline(round_history)

            if not os.path.isdir('figures'):
                os.mkdir('figures')

            plt.savefig(f'figures/{goal_suit}_{TradingBot.n_games}.png')

            # return true if you want to terminate return false if you want to keep going
            return False
        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in data_collection')

    @staticmethod
    def parse_history(round_history):
        history = round_history['game_updates']
        result = {'Diamonds': {'Buy': [], 'Sell': []}, 'Hearts': {'Buy': [], 'Sell': []},
                  'Spades': {'Buy': [], 'Sell': []}, 'Clubs': {'Buy': [], 'Sell': []}}
        for element in history:
            if element[0] != 'Order':
                continue

            result[element[1]['suit'][0]][element[1]['direction']].append(element[1]['metadata']['price'])

        return result

    @staticmethod
    def parse_current_hand(round_data: dict) -> dict:
        try:
            for user in round_data['chips_and_hands']:
                if user['user']['display_name'] == FiggieGame.DISPLAY_NAME:
                    hand = {item[0][0]: item[1] for item in user['hand']}
            return hand

        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in parse_hand')

    @staticmethod
    def parse_current_orders(round_data: dict) -> dict:
        try:
            bid_offer_prices = {"offer": [], "bid": []}

            for item in round_data['markets']:
                bid_info = item[1]["bid"]
                offer_info = item[1]["offer"]

                if bid_info != None:
                    bid_dict = {"suit": item[0][0], "display_name": bid_info["user"]["display_name"],
                                "price": bid_info["price"]}
                    bid_offer_prices["bid"].append(bid_dict)

                if offer_info != None:
                    offer_dict = {"suit": item[0][0], "display_name": offer_info["user"]["display_name"],
                                  "price": offer_info["price"]}
                    bid_offer_prices["offer"].append(offer_dict)

            return bid_offer_prices
        except Exception as e:
            print(traceback.format_exc())
            raise Exception('error in parse_orders')

    @staticmethod
    def parse_historical_orders(round_history: dict) -> pandas.DataFrame:

        orders = pd.DataFrame(round_history['game_updates'], columns=['Type', 'Details'])
        orders = orders[orders['Type'] == "Order"]
        orders['Metadata'] = orders['Details'].apply(lambda x: x['metadata'])
        orders['User'] = orders['Metadata'].apply(lambda x: x['user']['display_name'])
        orders['Price'] = orders['Metadata'].apply(lambda x: x['price'])
        orders['Time'] = pd.to_datetime(orders['Metadata'].apply(lambda x: x['time']))
        orders['Suit'] = orders['Details'].apply(lambda x: x['suit'][0])
        orders['Direction'] = orders['Details'].apply(lambda x: x['direction'])
        orders.drop(columns=['Details', 'Metadata'], inplace=True)

        return orders

    @staticmethod
    def parse_historical_trades(round_history: dict) -> pandas.DataFrame:

        trades = pd.DataFrame(round_history['trades'], columns=['Type', 'Details'])
        trades = trades[trades['Type'] == "Trade"]
        # trades['Metadata'] = trades['Details'].apply(lambda x: x['metadata'])
        trades['Seller'] = trades['Details'].apply(lambda x: x['seller']['display_name'])
        trades['Seller'] = trades['Details'].apply(lambda x: x['buyer']['display_name'])
        trades['Price'] = trades['Details'].apply(lambda x: x['price'])
        trades['Time'] = pd.to_datetime(trades['Details'].apply(lambda x: x['time']))
        trades['Suit'] = trades['Details'].apply(lambda x: x['suit'][0])
        trades['Direction'] = trades['Details'].apply(lambda x: x['direction'])
        trades.drop(columns=['Details'], inplace=True)

        return trades

    @staticmethod
    def event_call_time_left(round_data: dict, round_history: dict):

        if len(round_history['game_updates']) == 0:
            return 240

        if round_history['game_updates'][0][0] == 'Trade':
            result = datetime.strptime(round_data['end_time'].split('.')[0], '%Y-%m-%d %H:%M:%S') - datetime.strptime(
                round_history['game_updates'][0][1]['time'].split('.')[0], '%Y-%m-%d %H:%M:%S')
        else:
            result = datetime.strptime(round_data['end_time'].split('.')[0],
                                       '%Y-%m-%d %H:%M:%S') - datetime.strptime(
                round_history['game_updates'][0][1]['metadata']['time'].split('.')[0], '%Y-%m-%d %H:%M:%S')

        return result.total_seconds()

    @staticmethod
    def draw_current_timeline(round_history):
        colors = ['b-', 'r-']

        orders = TradingBot.parse_historical_orders(round_history)
        trades = TradingBot.parse_historical_trades(round_history)

        plt.clf()

        for pos, suit in enumerate(sorted(orders['Suit'].unique())):
            for idx, direction in enumerate(sorted(orders['Direction'].unique())):
                temp_df = orders[(orders['Direction'] == direction) & (orders['Suit'] == suit)]
                plt.subplot(2, 2, 1 + pos)
                plt.plot(temp_df['Time'], temp_df['Price'], colors[idx], marker=None, label=direction)

            temp_trades = trades[trades['Suit'] == suit]
            plt.subplot(2, 2, 1 + pos)
            plt.plot(temp_trades['Time'], temp_trades['Price'], 'go-')

            plt.title(suit)
            plt.xlabel('Time')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.xticks([orders['Time'].min(), orders['Time'].max()], rotation=45)
            plt.ylim(0, 30)
            plt.ylabel('Price')

        plt.tight_layout()


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
