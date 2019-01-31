'''
This code connects your Bot to the engine. Modify at your own risk!
'''

import argparse
import socket

from game import Game, Round, Pot
from actions import *


class Runner(object):
    def __init__(self, bot, socketfile, verbose):
        self.bot = bot
        self.socketfile = socketfile
        self.verbose = verbose
        self.current_game = None
        self.current_round = None
        self.current_cards = None
        self.current_pot = None
        self.move_history = []

    def receive(self):
        while True:
            packet = self.socketfile.readline().strip()

            if not packet:
                if self.verbose:
                    print("Gameover, engine disconnected.")
                break

            if self.verbose:
                print("==> {}".format(packet))

            yield packet


    def send(self, outgoing_string):
        if self.verbose:
            print("<== {}".format(outgoing_string))

        self.socketfile.write("{}\n".format(outgoing_string))
        self.socketfile.flush()


    def run(self):
        for packet in self.receive():
            data = packet.split(' ')
            action = data[0]

            if action == 'NEWGAME':
                self._handle_newgame(data)
            elif action == 'NEWHAND':
                self._handle_newhand(data)
            elif action == 'EXCHANGE':
                self._handle_exchange(data)
            elif action == 'GETACTION':
                action = self._handle_getaction(data)
                self._handle_action(action)
            elif action == 'HANDOVER':
                self._handle_handover(data)
            elif action == 'REQUESTKEYVALUES':
                # Ignore this, since we don't allow it anymore.
                self.send("FINISH")
            else:
                if verbose:
                    print("# Unexpected action: {}".format(action))


    def _handle_newgame(self, data):
        self.__init__(self.bot, self.socketfile, self.verbose)
        name = data[1]
        opponent_name = data[2]
        round_stack = int(data[3])
        big_blind = int(data[4])
        num_hands = int(data[5])
        time_bank = float(data[6])
        self.current_game = Game(name, opponent_name, round_stack, big_blind, num_hands, time_bank)
        self.bot.handle_new_game(self.current_game)


    def _handle_newhand(self, data):
        hand_num = int(data[1])
        big_blind = data[2] == 'false'
        self.current_cards = data[3].split(',')
        bankroll = int(data[4])
        opponent_bankroll = int(data[5])
        self.move_history = []
        self.current_pot = Pot(**{
            'pip': self.current_game.big_blind if big_blind else self.current_game.big_blind/2,
            'bets': 0,
            'opponent_bets': self.current_game.big_blind if not big_blind else self.current_game.big_blind/2,
            'num_exchanges': 0,
            'opponent_num_exchanges': 0
        })
        self.current_round = Round(hand_num, bankroll, opponent_bankroll, big_blind)
        self.bot.handle_new_round(self.current_game, self.current_round)


    def _handle_exchange(self, data):
        self.current_cards = data[2].split(',')


    def _get_legal_moves(self, legal_move_string):
        legal_move_strings = legal_move_string.split(';')
        min_amount = None
        max_amount = None
        legal_moves = set([])
        for move_string in legal_move_strings:
            if move_string.startswith('CHECK'):
                legal_moves.add(CheckAction)
            elif move_string.startswith('CALL'):
                legal_moves.add(CallAction)
            elif move_string.startswith('FOLD'):
                legal_moves.add(FoldAction)
            elif move_string.startswith('EXCHANGE'):
                legal_moves.add(ExchangeAction)
            elif move_string.startswith('RAISE'):
                legal_moves.add(RaiseAction)
            elif move_string.startswith('BET'):
                legal_moves.add(BetAction)

            if move_string.startswith('RAISE') or move_string.startswith('BET'):
                move_info = move_string.split(':')
                min_amount = int(move_info[1])
                max_amount = int(move_info[2])
        return legal_moves, min_amount, max_amount


    def _check_move_validity(self, action, legal_moves, min_amount, max_amount):
        if type(action) not in legal_moves:
            return False

        if isinstance(action, RaiseAction) or isinstance(action, BetAction):
            return min_amount <= action.amount <= max_amount

        return True


    def _cost(self, action):
        if isinstance(action, CheckAction):
            return 0
        elif isinstance(action, CallAction):
            return self.current_pot.opponent_bets - self.current_pot.bets - self.current_pot.pip
        elif isinstance(action, FoldAction):
            return 0
        elif isinstance(action, ExchangeAction):
            return 2**(self.current_pot.num_exchanges + 1)
        elif isinstance(action, RaiseAction):
            return action.amount - self.current_pot.pip
        elif isinstance(action, BetAction):
            return action.amount - self.current_pot.pip


    def _update_pot(self, new_moves, new_pot_total):
        new_pot = self.current_pot._asdict()
        for move in new_moves:
            if move.startswith('EXCHANGE') and move.split(':')[-1] == self.current_game.opponent_name:
                new_pot['opponent_num_exchanges'] += 1
            elif move.startswith('DEAL') or move.startswith('TIE') or move.startswith('WIN'):
                new_pot['bets'] += new_pot['pip']
                new_pot['pip'] = 0

        new_pot['opponent_bets'] = new_pot_total - self.current_pot.total - Pot(**new_pot).opponent_exchanges
        self.current_pot = Pot(**new_pot)


    def _handle_getaction(self, data):
        new_pot_total = int(data[1])
        new_moves = data[5].split(';')
        self._update_pot(new_moves, new_pot_total)
        self.move_history.extend(new_moves)
        board = [] if data[3] == 'None' else data[3].split(',')
        legal_moves, min_amount, max_amount = self._get_legal_moves(data[7])

        time_left = float(data[8])

        action = self.bot.get_action(
            self.current_game,
            self.current_round,
            self.current_pot,
            self.current_cards,
            board,
            legal_moves,
            self._cost,
            self.move_history,
            time_left,
            min_amount=min_amount,
            max_amount=max_amount
        )
        
        if isinstance(action, BetAction) or isinstance(action, RaiseAction):
            action = type(action)(amount=int(action.amount))

        if not self._check_move_validity(action, legal_moves, min_amount, max_amount):
            print("Error: bot returned invalid move. Move: {}. Legal: {}, Min={}, Max={}".format(action, legal_moves, min_amount, max_amount))
            if FoldAction in legal_moves:
                action = FoldAction()
            else:
                action = CheckAction()

        return action


    def _handle_action(self, action):
        new_pot = self.current_pot._asdict()

        if isinstance(action, CheckAction):
            self.send('CHECK')
        elif isinstance(action, FoldAction):
            self.send('FOLD')
        elif isinstance(action, ExchangeAction):
            new_pot['num_exchanges'] += 1
            self.send('EXCHANGE')
        elif isinstance(action, CallAction):
            new_pot['pip'] += self._cost(action)
            self.send('CALL')
        elif isinstance(action, RaiseAction):
            new_pot['pip'] += self._cost(action)
            self.send('RAISE:{}'.format(action.amount))
        elif isinstance(action, BetAction):
            new_pot['pip'] += self._cost(action)
            self.send('BET:{}'.format(action.amount))

        self.current_pot = Pot(**new_pot)


    def _get_result(self, new_moves):
        opponent_cards = None
        for move in new_moves:
            if move.startswith("SHOW") and move.endswith(self.current_game.opponent_name):
                move_info = move.split(":")
                opponent_cards = move_info[1:3]
            elif move.startswith("TIE"):
                return 'tie', opponent_cards
            elif move.startswith("WIN"):
                if move.endswith(self.current_game.name):
                    return 'win', opponent_cards
                else:
                    return 'loss', opponent_cards
        return None, None


    def _handle_handover(self, data):
        bankroll = int(data[1])
        opponent_bankroll = int(data[2])
        board_cards = [] if data[4] == 'None' else data[4].split(',')
        new_moves = data[6].split(';')
        new_pot_total = int(data[7])
        self._update_pot(new_moves, new_pot_total)
        result, opponent_cards = self._get_result(new_moves)
        self.move_history.extend(new_moves)
        self.bot.handle_round_over(
            self.current_game,
            self.current_round,
            self.current_pot,
            self.current_cards,
            opponent_cards,
            board_cards,
            result,
            bankroll,
            opponent_bankroll,
            self.move_history
        )


def create_runner(bot, host, port):
    try:
        sock = socket.create_connection((host, port))
    except socket.error as e:
        print('Error connecting to {}:{}. Aborting.'.format(host, port))
        return None, None

    socketfile = sock.makefile()
    runner = Runner(bot, socketfile, verbose=False)
    
    return runner, sock
