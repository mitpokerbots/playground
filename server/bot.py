from server.pokerbots_parser.actions import  FoldAction, CallAction, CheckAction, RaiseAction
from server.pokerbots_parser.bot import Bot
import socket
import time
import random
import json

def pot_to_json(pot):
    return {
        'pip': pot.pip,
        'bets': pot.bets,
        'num_exchanges': pot.num_exchanges,
        'exchanges': pot.exchanges,
        'total': pot.total,
        'opponent_bets': pot.opponent_bets,
        'opponent_num_exchanges': pot.opponent_num_exchanges,
        'opponent_exchanges': pot.opponent_exchanges,
        'opponent_total': pot.opponent_total,
        'grand_total': pot.grand_total
    }

def move_history_to_json(move_history):
    history = []
    for move in move_history:
        data = move.split(':')
        d = {
            'type': data[0],
            'player': 'table' if data[0] == 'DEAL' else ('hero' if data[-1] == 'A' else 'bot')
        }
        if data[0] in ['POST', 'BET', 'RAISE']:
            d['amount'] = int(data[1])
        elif data[0] == 'SHOW':
            d['cards'] = data[1:3]
        elif data[0] == 'DEAL':
            d['street'] = data[1]
        history.append(d)
    return history

def legal_moves_to_json(legal_moves, min_amount, max_amount, continue_cost):
    moves = []
    for cls in legal_moves:
        d = {
            'type': cls.__name__[:-6].upper(),
        }
        if cls is RaiseAction:
            d['min'] = min_amount
            d['max'] = max_amount
            d['base_cost'] = 0
        elif cls is CallAction:
            d['base_cost'] = continue_cost
        else:
            d['base_cost'] = 0
        moves.append(d)
    return sorted(moves, key=lambda m: ('min' in m, m['type']))

class Player(Bot):
    def __init__(self, db_game, pubsub):
        self.db_game = db_game
        self.sock = None
        self.done = False
        self.bankroll = 0
        self.opponent_bankroll = 0
        self.pubsub = pubsub
        self.past_moves = []
        self.current_street = 0

    def set_sock(self, sock):
        self.sock = sock

    def force_shutdown(self):
        self.done = True
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def handle_new_game(self, new_game):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        new_game: the pokerbots.Game object.

        Returns:
        Nothing.
        '''
        pass

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        self.bankroll = game_state.bankroll
        self.opponent_bankroll =  -1 * game_state.bankroll
        self.past_moves = []
        self.current_street = 0

        if game_state.round_num > 100:
            return self.force_shutdown()

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''

        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed

        if self.done:
            return

        board_cards = previous_state.deck[:street]  # the board cards
        my_bounty = previous_state.bounties[active]  # your current bounty rank
        my_pip = previous_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        my_stack = previous_state.stacks[active]  # the number of chips you have remaining
        opp_stack = previous_state.stacks[1-active]  # the number of chips your opponent has remaining
        
        my_contribution = 400 - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = 400 - opp_stack  # the number of chips your opponent has contributed to the pot

        # if self.current_street != street:
        #     self.current_street = street
        #     self.past_moves.append('DEAL:' + ('Flop' if street == 3 else ('Turn' if street == 4 else 'River')))
        if not opp_cards and my_delta > 0:
            self.past_moves.append('FOLD:bot')

        pot = {
            'pip': my_pip,
            'bets': my_contribution,
            'bounty_rank': my_bounty,
            'total': my_contribution,
            'opponent_bets': opp_contribution,
            'opponent_total': opp_contribution,
            'grand_total': my_contribution + opp_contribution
        }

        self.db_game.send_message({
            'status': 'round_over',
            'round_num': game_state.round_num,
            'bankroll': self.bankroll,
            'new_bankroll': game_state.bankroll,
            'opponent_bankroll': self.opponent_bankroll,
            'new_opponent_bankroll': -1*game_state.bankroll,
            'pot': pot,
            'cards': my_cards,
            'opponent_cards': opp_cards if opp_cards else ['??', '??'],
            'board_cards': board_cards,
            'result': ('win' if my_delta > 0 else ('loss' if my_delta < 0 else 'tie')),
            'move_history': move_history_to_json(self.past_moves)
        })
        time.sleep(5)

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        if self.done:
            return
        street = round_state.street
        legal_actions = round_state.legal_actions()

        my_pip = round_state.pips[active]
        min_raise, max_raise = round_state.raise_bounds()
        min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
        max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        my_bounty = round_state.bounties[active]  # What is your bounty rank?
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = 400 - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = 400 - opp_stack  # the number of chips your opponent has contributed to the pot

        if continue_cost == 0:
            if (not self.past_moves or (self.past_moves[-1][:6] == 'RAISE:' and self.past_moves[-1][-2:] == ':A')):
                self.past_moves.append('CALL:bot')
            elif (self.past_moves and self.past_moves[-1][:6] == 'CHECK:' and self.past_moves[-1][-2:] == ':A' and not bool(active)):
                self.past_moves.append('CHECK:bot')
        
        if self.current_street != street:
            self.current_street = street
            self.past_moves.append('DEAL:' + ('Flop' if street == 3 else ('Turn' if street == 4 else 'River')))

            if (active and continue_cost == 0):
                self.past_moves.append('CHECK:bot')

        if my_contribution != 1 and continue_cost > 0:
            self.past_moves.append('RAISE:' + str(continue_cost) + ':bot')
        

        pot = {
            'pip': my_pip,
            'bets': my_contribution,
            'total': my_contribution,
            'bounty_rank': my_bounty,
            'opponent_bets': opp_contribution,
            'opponent_total': opp_contribution,
            'grand_total': my_contribution + opp_contribution
        }

        self.db_game.send_message({
            'status': 'get_action',
            'round_num': game_state.round_num,
            'bankroll': game_state.bankroll,
            'opponent_bankroll': -1 * game_state.bankroll,
            'pot': pot,
            'cards': round_state.hands[active],
            'opponent_cards': ['??', '??'],
            'board_cards': board_cards,
            'move_history': move_history_to_json(self.past_moves),
            'legal_moves': legal_moves_to_json(legal_actions, min_raise, max_raise, continue_cost)
        })

        while True:
            message = self.pubsub.get_message(timeout=200)
            if message is None:
                print("None message, therefore timeout")
                return self.force_shutdown()

            if message.get('type') == 'subscribe':
                continue

            print(message)

            if message['data'].decode("utf-8") == 'ping':
                continue

            data = json.loads(message['data'])

            if data['type'] == 'FOLD':
                self.past_moves.append('FOLD:A')
                return FoldAction()
            elif data['type'] == 'CHECK':
                self.past_moves.append('CHECK:A')
                return CheckAction()
            elif data['type'] == 'CALL':
                self.past_moves.append('CALL:A')
                return CallAction()
            elif data['type'] == 'BET':
                self.past_moves.append('RAISE:' + str(data['amount']) + ':A')
                return RaiseAction(amount=data['amount'])
            elif data['type'] == 'RAISE':
                self.past_moves.append('RAISE:' + str(data['amount']) + ':A')
                return RaiseAction(amount=data['amount'])
            else:
                return
