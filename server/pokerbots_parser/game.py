from collections import namedtuple

'''
The Game class represents a single match between two bots.

name: your bot's name on the engine
opponent_name: the opponent's bot's name on the engine
round_stack: the number of chips you have available at the start of every hand
big_blind: the size of the big blind
num_rounds: the number of hands that will be played during this match
time_bank: the total amount of seconds your bot has to play this game.
'''
Game = namedtuple('Game', ['name', 'opponent_name', 'round_stack', 'big_blind', 'num_hands', 'time_bank'])


'''
The Round class represents a single round of the game above

hand_num: the round #. Ranges from 1 to Game.num_rounds
bankroll: the total amount you've gained or lost from the beginning of the game to the start of this round
opponent_bankroll: the total amount your opponent has gained or lost. Usually the negative of the above
big_blind: True if you had the big blind, False otherwise.
'''
Round = namedtuple('Round', ['hand_num', 'bankroll', 'opponent_bankroll', 'big_blind'])


'''
The Pot class represents the amount of money in the pot

pip: the amount you have added to the pot via betting during this betting round
bets: the amount you have added to the pot via betting during previous rounds
exchanges: the amount you have added to the pot via exchanges
num_exchanges: the number of times you have exchanged
total: the total amount you have added to the pot
opponent_bets: the total amount your opponent has added to the pot via betting
opponent_exchanges: the total amount your opponent has added to the pot via exchanges
opponent_num_exchanges: the number of times your opponent has exchanged
opponent_total: the total amount your opponent has added to the pot
grand_total: the total size of the pot
'''
class Pot(namedtuple('_Pot', ['pip', 'bets', 'num_exchanges', 'opponent_bets', 'opponent_num_exchanges'])):
    @property
    def exchanges(self):
        return 2**(self.num_exchanges + 1) - 2

    @property
    def total(self):
        return self.pip + self.bets + self.exchanges

    @property
    def opponent_exchanges(self):
        return 2**(self.opponent_num_exchanges + 1) - 2

    @property
    def opponent_total(self):
        return self.opponent_bets + self.opponent_exchanges

    @property
    def grand_total(self):
        return self.total + self.opponent_total

    def __repr__(self):
        return (
            'Pot(pip={} bets={} exchanges={} num_exchanges={} total={} ' +
            'opponent_bets={} opponent_exchanges={} opponent_num_exchanges={} opponent_total={} ' +
            'grand_total={})'
        ).format(
            self.pip, self.bets, self.exchanges, self.num_exchanges, self.total,
            self.opponent_bets, self.opponent_exchanges, self.opponent_num_exchanges, self.opponent_total,
            self.grand_total
        )
