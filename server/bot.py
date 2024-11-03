from server.pokerbots_parser.actions import  FoldAction, CallAction, CheckAction, RaiseAction, BidAction
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
        elif data[0] == 'EXCHANGE' and data[-1] == 'A':
            d['old'] = data[1].split(',')
            d['new'] = data[2].split(',')
        elif data[0] == 'SHOW':
            d['cards'] = data[1:3]
        elif data[0] == 'DEAL':
            d['street'] = data[1]
        history.append(d)
    return history

def legal_moves_to_json(legal_moves, min_amount, max_amount):
    moves = []
    for cls in legal_moves:
        d = {
            'type': cls.__name__[:-6].upper(),
        }
        if cls is RaiseAction:
            d['min'] = min_amount
            d['max'] = max_amount
            d['base_cost'] = 0
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
        Called when a new round starts. Called Game.num_rounds times.

        Arguments:
        game: the pokerbots.Game object for the new round.
        new_round: the new pokerbots.Round object.

        Returns:
        Nothing.
        '''
        self.bankroll = game_state.bankroll
        self.opponent_bankroll =  -1 * game_state.bankroll
        if game_state.round_num > 100:
            return self.force_shutdown()

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called Game.num_rounds times.

        Arguments:
        game: the pokerbots.Game object.
        round: the pokerbots.Round object.
        pot: the pokerbots.Pot object.
        cards: the cards you held when the round ended.
        opponent_cards: the cards your opponent held when the round ended, or None if they never showed.
        board_cards: the cards on the board when the round ended.
        result: 'win', 'loss' or 'tie'
        new_bankroll: your total bankroll at the end of this round.
        new_opponent_bankroll: your opponent's total bankroll at the end of this round.
        move_history: a list of moves that occurred during this round, earliest moves first.

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


        board_cards = terminal_state.deck[:street]  # the board cards
        opp_pip = terminal_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_pip = terminal_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        my_stack = terminal_state.stacks[active]  # the number of chips you have remaining
        opp_stack = terminal_state.stacks[1-active]  # the number of chips your opponent has remaining
        
        my_contribution = 400 - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = 400 - opp_stack  # the number of chips your opponent has contributed to the pot

        pot = {
            'pip': my_pip,
            'bets': my_contribution,
            'num_exchanges': 0,
            'exchanges': 0,
            'total': my_contribution,
            'opponent_bets': opp_contribution,
            'opponent_num_exchanges': 0,
            'opponent_exchanges': 0,
            'opponent_total': opp_contribution,
            'grand_total': my_contribution + opp_contribution
        }

        self.db_game.send_message({
            'status': 'round_over',
            'round_num': game_state.round_num,
            'bankroll': terminal_state.stacks[active],
            'new_bankroll': game_state.bankroll,
            'opponent_bankroll': terminal_state.stacks[1 - active],
            'new_opponent_bankroll': -1*game_state.bankroll,
            'pot': pot,
            'cards': my_cards,
            'opponent_cards': opp_cards if opp_cards else ['??', '??'],
            'board_cards': board_cards,
            'result': ('win' if my_delta > 0 else ('loss' if my_delta < 0 else 'tie')),
            'move_history': move_history_to_json([])
        })
        time.sleep(5)

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the server needs an action from your bot.

        Arguments:
        game: the pokerbots.Game object.
        round: the pokerbots.Round object.
        pot: the pokerbots.Pot object.
        cards: an array of your cards, in common format.
        board_cards: an array of cards on the board. This list has length 0, 3, 4, or 5.
        legal_moves: a set of the move classes that are legal to make.
        cost_func: a function that takes a move, and returns additional cost of that move. Your returned move will raise your pot.contribution by this amount.
        move_history: a list of moves that have occurred during this round so far, earliest moves first.
        time_left: a float of the number of seconds your bot has remaining in this match (not round).
        min_amount: if BetAction or RaiseAction is valid, the smallest amount you can bet or raise to (i.e. the smallest you can increase your pip).
        max_amount: if BetAction or RaiseAction is valid, the largest amount you can bet or raise to (i.e. the largest you can increase your pip).
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
        my_bid = round_state.bids[active]  # How much you bid previously (available only after auction)
        opp_bid = round_state.bids[1-active]  # How much opponent bid previously (available only after auction)
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = 400 - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = 400 - opp_stack  # the number of chips your opponent has contributed to the pot

        pot = {
            'pip': my_pip,
            'bets': my_contribution,
            'num_exchanges': 0,
            'exchanges': 0,
            'total': my_contribution,
            'opponent_bets': opp_contribution,
            'opponent_num_exchanges': 0,
            'opponent_exchanges': 0,
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
            'board_cards': round_state.deck[:street],
            'move_history': move_history_to_json([]),
            'legal_moves': legal_moves_to_json(legal_actions, min_raise, max_raise)
        })

        while True:
            message = self.pubsub.get_message(timeout=50)
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
                return FoldAction()
            elif data['type'] == 'CHECK':
                return CheckAction()
            elif data['type'] == 'CALL':
                return CallAction()
            elif data['type'] == 'BET':
                return RaiseAction(amount=data['amount'])
            elif data['type'] == 'RAISE':
                return RaiseAction(amount=data['amount'])
            else:
                return
