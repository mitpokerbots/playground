from collections import namedtuple

'''
Below are actions that the player is allowed to take.
'''

# Organizer note: ensure these match
# engine/src/pokerbots/engine/player/socketplayer/Parser.java
FoldAction = namedtuple('FoldAction', [])
CallAction = namedtuple('CallAction', [])
CheckAction = namedtuple('CheckAction', [])
ExchangeAction = namedtuple('ExchangeAction', [])
BetAction = namedtuple('BetAction', ['amount'])
RaiseAction = namedtuple('RaiseAction', ['amount'])
