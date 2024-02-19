#!/usr/bin/env python
# coding: utf-8

# In[19]:


import websocket
import json
    
header = {
    'Sec-Websocket-Extensions': 'permessage-deflate; client_max_window_bits',
    'Sec-Websocket-Key':'Y22XNEFUuyeyRyIEW77q7A==',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
}


# In[23]:


lobby_data = {}
n_bots = 4

def start_game(wsapp):
    wsapp.send(json.dumps(['Start_game']))

def set_readyness(wsapp):
    wsapp.send(json.dumps(["Set_readiness",{"is_ready":True}]))

def add_bot(wsapp):
    wsapp.send(json.dumps(["Add_bot"]))
    
def set_display_name(wsapp):
    wsapp.send(json.dumps(["Set_display_name", "lalala"]))
    
def create_lobby(wsapp):
    wsapp.send(json.dumps(["Create_lobby",{"settings":["Standard"]}]))

def add_order(wsapp, direction: str, suit: str, price:int): # direction: Buy or Sell, suit: Diamonds, Clubs, Spades, Hearts
    wsapp.send(json.dumps(["Add_order",{"order":{"suit":[suit],"price":price,"direction":direction,"is_ioc":false}}]))
    
def on_message(wsapp, message):
    
    message = json.loads(message)
    print(message)
    
    if "Initial_connect" in message[0]:
        set_display_name(wsapp)
        create_lobby(wsapp)
    
#     if "Main_menu_lobbies" in message[0]:
#         set_display_name(wsapp)
    
    elif "Lobby" in message[0]:
        lobby_data = message[1]
        if lobby_data['is_startable'] and len(lobby_data['players_and_readiness']) > 1:
            start_game(wsapp)
            return
        
        set_readyness(wsapp)
        for x in range(n_bots):
            add_bot(wsapp)
    
    elif "Live_round_for_player" in message[0]:
        round_data = message[1]['round']
        round_history = message[1]['round_history']
        



# In[24]:


wsapp = websocket.WebSocketApp("wss://europe.figgie.com/", header=header, on_message=on_message)

wsapp.run_forever()


# In[ ]:




