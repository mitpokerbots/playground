from server.pokerbots_parser import  Bot, FoldAction, CallAction, CheckAction, ExchangeAction, BetAction, RaiseAction
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

def legal_moves_to_json(legal_moves, cost_func, min_amount, max_amount):
    moves = []
    for cls in legal_moves:
        d = {
            'type': cls.__name__[:-6].upper(),
        }
        if cls is BetAction or cls is RaiseAction:
            d['min'] = min_amount
            d['max'] = max_amount
            d['base_cost'] = cost_func(cls(min_amount))
        else:
            d['base_cost'] = cost_func(cls())
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

    def handle_new_round(self, game, new_round):
        '''
        Called when a new round starts. Called Game.num_rounds times.

        Arguments:
        game: the pokerbots.Game object for the new round.
        new_round: the new pokerbots.Round object.

        Returns:
        Nothing.
        '''
        self.bankroll = new_round.bankroll
        self.opponent_bankroll = new_round.opponent_bankroll
        if new_round.hand_num > 3:
            return self.force_shutdown()

    def handle_round_over(self, game, round, pot, cards, opponent_cards, board_cards, result, new_bankroll, new_opponent_bankroll, move_history):
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
        if self.done:
            return

        self.db_game.send_message({
            'status': 'round_over',
            'round_num': round.hand_num,
            'bankroll': round.bankroll,
            'new_bankroll': new_bankroll,
            'opponent_bankroll': round.opponent_bankroll,
            'new_opponent_bankroll': new_opponent_bankroll,
            'pot': pot_to_json(pot),
            'cards': cards,
            'opponent_cards': opponent_cards if opponent_cards is not None else ['??', '??'],
            'board_cards': board_cards,
            'result': result,
            'move_history': move_history_to_json(move_history)
        })
        time.sleep(8)

    def get_action(self, game, round, pot, cards, board_cards, legal_moves, cost_func, move_history, time_left, min_amount=None, max_amount=None):
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

        self.db_game.send_message({
            'status': 'get_action',
            'round_num': round.hand_num,
            'bankroll': round.bankroll,
            'opponent_bankroll': round.opponent_bankroll,
            'pot': pot_to_json(pot),
            'cards': cards,
            'opponent_cards': ['??', '??'],
            'board_cards': board_cards,
            'move_history': move_history_to_json(move_history),
            'legal_moves': legal_moves_to_json(legal_moves, cost_func, min_amount, max_amount)
        })

        while True:
            message = self.pubsub.get_message(timeout=50)
            if message is None:
                print "None message, therefore timeout"
                return self.force_shutdown()

            if message.get('type') == 'subscribe':
                continue

            if message['data'] == 'ping':
                continue

            print message
            data = json.loads(message['data'])

            if data['type'] == 'FOLD':
                return FoldAction()
            elif data['type'] == 'CHECK':
                return CheckAction()
            elif data['type'] == 'CALL':
                return CallAction()
            elif data['type'] == 'EXCHANGE':
                return ExchangeAction()
            elif data['type'] == 'BET':
                return BetAction(amount=data['amount'])
            elif data['type'] == 'RAISE':
                return RaiseAction(amount=data['amount'])
            else:
                return
