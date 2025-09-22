"""
Texas Hold'em Poker Game Engine
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .cards import Card, Deck, HandEvaluator


class PlayerAction(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check"
    ALL_IN = "all_in"


@dataclass
class GameState:
    """Current state of the poker game visible to players"""
    pot: int
    community_cards: List[Card]
    current_bet: int
    player_chips: Dict[str, int]
    player_bets: Dict[str, int]
    active_players: List[str]
    current_player: str
    round_name: str  # preflop, flop, turn, river
    min_bet: int
    big_blind: int
    small_blind: int


@dataclass
class PlayerHand:
    """A player's hole cards"""
    cards: List[Card]
    
    def __str__(self) -> str:
        return f"[{', '.join(str(card) for card in self.cards)}]"


class PokerGame:
    """Manages a single hand of Texas Hold'em poker"""
    
    def __init__(self, players: List[str], starting_chips: int = 1000, 
                 small_blind: int = 10, big_blind: int = 20):
        self.players = players.copy()
        self.starting_chips = starting_chips
        self.small_blind = small_blind
        self.big_blind = big_blind
        
        # Game state
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.player_hands: Dict[str, PlayerHand] = {}
        self.player_chips: Dict[str, int] = {player: starting_chips for player in players}
        self.player_bets: Dict[str, int] = {player: 0 for player in players}
        self.active_players: List[str] = players.copy()
        self.folded_players: List[str] = []
        
        # Betting state
        self.pot = 0
        self.current_bet = 0
        self.current_player_index = 0
        self.dealer_button = 0
        self.round_name = "preflop"
        self.betting_round_complete = False
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def start_hand(self):
        """Start a new hand of poker"""
        self.reset_hand()
        self.deal_hole_cards()
        self.post_blinds()
        self.current_player_index = self.get_first_player_index()
        
        self.logger.info(f"Starting new hand. Dealer: {self.players[self.dealer_button]}")
        self.logger.info(f"Community cards: {self.community_cards}")
    
    def reset_hand(self):
        """Reset for a new hand"""
        self.deck = Deck()
        self.deck.shuffle()
        self.community_cards = []
        self.player_hands = {}
        self.player_bets = {player: 0 for player in self.active_players}
        self.folded_players = []
        self.pot = 0
        self.current_bet = self.big_blind
        self.round_name = "preflop"
        self.betting_round_complete = False
    
    def deal_hole_cards(self):
        """Deal 2 cards to each active player"""
        for player in self.active_players:
            cards = [self.deck.deal_card() for _ in range(2)]
            self.player_hands[player] = PlayerHand(cards)
            self.logger.info(f"{player} dealt: {self.player_hands[player]}")
    
    def post_blinds(self):
        """Post small and big blinds"""
        if len(self.active_players) < 2:
            return
        
        small_blind_player = self.active_players[(self.dealer_button + 1) % len(self.active_players)]
        big_blind_player = self.active_players[(self.dealer_button + 2) % len(self.active_players)]
        
        # Post small blind
        small_blind_amount = min(self.small_blind, self.player_chips[small_blind_player])
        self.player_bets[small_blind_player] = small_blind_amount
        self.player_chips[small_blind_player] -= small_blind_amount
        self.pot += small_blind_amount
        
        # Post big blind
        big_blind_amount = min(self.big_blind, self.player_chips[big_blind_player])
        self.player_bets[big_blind_player] = big_blind_amount
        self.player_chips[big_blind_player] -= big_blind_amount
        self.pot += big_blind_amount
        
        self.logger.info(f"{small_blind_player} posts small blind: {small_blind_amount}")
        self.logger.info(f"{big_blind_player} posts big blind: {big_blind_amount}")
    
    def get_first_player_index(self) -> int:
        """Get the index of the first player to act"""
        if len(self.active_players) == 2:
            return self.dealer_button
        else:
            return (self.dealer_button + 3) % len(self.active_players)
    
    def get_current_player(self) -> str:
        """Get the current player to act"""
        if not self.active_players:
            return ""
        return self.active_players[self.current_player_index % len(self.active_players)]
    
    def get_game_state(self) -> GameState:
        """Get the current game state visible to players"""
        return GameState(
            pot=self.pot,
            community_cards=self.community_cards.copy(),
            current_bet=self.current_bet,
            player_chips=self.player_chips.copy(),
            player_bets=self.player_bets.copy(),
            active_players=self.active_players.copy(),
            current_player=self.get_current_player(),
            round_name=self.round_name,
            min_bet=self.big_blind,
            big_blind=self.big_blind,
            small_blind=self.small_blind
        )
    
    def get_player_hand(self, player: str) -> Optional[PlayerHand]:
        """Get a player's hole cards"""
        return self.player_hands.get(player)
    
    def is_valid_action(self, player: str, action: PlayerAction, amount: int = 0) -> bool:
        """Check if a player action is valid"""
        if player not in self.active_players or player in self.folded_players:
            return False
        
        if player != self.get_current_player():
            return False
        
        player_bet = self.player_bets[player]
        to_call = self.current_bet - player_bet
        available_chips = self.player_chips[player]
        
        if action == PlayerAction.FOLD:
            return True
        elif action == PlayerAction.CHECK:
            return to_call == 0
        elif action == PlayerAction.CALL:
            return to_call > 0 and available_chips >= to_call
        elif action == PlayerAction.RAISE:
            min_raise = self.current_bet + self.big_blind
            return amount >= min_raise and available_chips >= (amount - player_bet)
        elif action == PlayerAction.ALL_IN:
            return available_chips > 0
        
        return False
    
    def process_action(self, player: str, action: PlayerAction, amount: int = 0) -> bool:
        """Process a player's action"""
        if not self.is_valid_action(player, action, amount):
            self.logger.warning(f"Invalid action by {player}: {action.value} {amount}")
            return False
        
        player_bet = self.player_bets[player]
        to_call = self.current_bet - player_bet
        
        if action == PlayerAction.FOLD:
            self.folded_players.append(player)
            self.active_players.remove(player)
            self.logger.info(f"{player} folds")
        
        elif action == PlayerAction.CHECK:
            self.logger.info(f"{player} checks")
        
        elif action == PlayerAction.CALL:
            call_amount = min(to_call, self.player_chips[player])
            self.player_bets[player] += call_amount
            self.player_chips[player] -= call_amount
            self.pot += call_amount
            self.logger.info(f"{player} calls {call_amount}")
        
        elif action == PlayerAction.RAISE:
            raise_amount = min(amount - player_bet, self.player_chips[player])
            self.player_bets[player] += raise_amount
            self.player_chips[player] -= raise_amount
            self.pot += raise_amount
            self.current_bet = self.player_bets[player]
            self.logger.info(f"{player} raises to {self.current_bet}")
        
        elif action == PlayerAction.ALL_IN:
            all_in_amount = self.player_chips[player]
            self.player_bets[player] += all_in_amount
            self.player_chips[player] = 0
            self.pot += all_in_amount
            if self.player_bets[player] > self.current_bet:
                self.current_bet = self.player_bets[player]
            self.logger.info(f"{player} goes all-in for {all_in_amount}")
        
        self.advance_to_next_player()
        return True
    
    def advance_to_next_player(self):
        """Move to the next player"""
        self.current_player_index = (self.current_player_index + 1) % len(self.active_players)
    
    def is_betting_round_complete(self) -> bool:
        """Check if the current betting round is complete"""
        if len(self.active_players) <= 1:
            return True
        
        # Check if all players have acted and bets are equal
        max_bet = max(self.player_bets[player] for player in self.active_players)
        for player in self.active_players:
            if self.player_bets[player] < max_bet and self.player_chips[player] > 0:
                return False
        
        return True
    
    def advance_to_next_round(self):
        """Advance to the next betting round"""
        if self.round_name == "preflop":
            self.deal_flop()
            self.round_name = "flop"
        elif self.round_name == "flop":
            self.deal_turn()
            self.round_name = "turn"
        elif self.round_name == "turn":
            self.deal_river()
            self.round_name = "river"
        elif self.round_name == "river":
            self.round_name = "showdown"
        
        # Reset betting for new round
        self.current_bet = 0
        for player in self.active_players:
            self.player_bets[player] = 0
        self.current_player_index = (self.dealer_button + 1) % len(self.active_players)
    
    def deal_flop(self):
        """Deal the flop (3 community cards)"""
        self.deck.deal_card()  # Burn card
        for _ in range(3):
            self.community_cards.append(self.deck.deal_card())
        self.logger.info(f"Flop: {self.community_cards[-3:]}")
    
    def deal_turn(self):
        """Deal the turn (4th community card)"""
        self.deck.deal_card()  # Burn card
        self.community_cards.append(self.deck.deal_card())
        self.logger.info(f"Turn: {self.community_cards[-1]}")
    
    def deal_river(self):
        """Deal the river (5th community card)"""
        self.deck.deal_card()  # Burn card
        self.community_cards.append(self.deck.deal_card())
        self.logger.info(f"River: {self.community_cards[-1]}")
    
    def is_hand_complete(self) -> bool:
        """Check if the hand is complete"""
        return len(self.active_players) <= 1 or self.round_name == "showdown"
    
    def determine_winners(self) -> List[Tuple[str, int]]:
        """Determine winners and their winnings"""
        if len(self.active_players) == 1:
            winner = self.active_players[0]
            return [(winner, self.pot)]
        
        # Evaluate all hands
        player_hands = []
        for player in self.active_players:
            hand_cards = self.player_hands[player].cards + self.community_cards
            best_hand = self.get_best_5_card_hand(hand_cards)
            player_hands.append((player, best_hand))
        
        # Sort by hand strength
        player_hands.sort(key=lambda x: self.evaluate_hand_strength(x[1]), reverse=True)
        
        # Determine winners (handle ties)
        winners = [player_hands[0]]
        best_strength = self.evaluate_hand_strength(player_hands[0][1])
        
        for player, hand in player_hands[1:]:
            hand_strength = self.evaluate_hand_strength(hand)
            if hand_strength == best_strength:
                winners.append((player, hand))
            else:
                break
        
        # Split pot among winners
        winnings_per_player = self.pot // len(winners)
        return [(player, winnings_per_player) for player, _ in winners]
    
    def get_best_5_card_hand(self, seven_cards: List[Card]) -> List[Card]:
        """Get the best 5-card hand from 7 available cards"""
        from itertools import combinations
        
        best_hand = None
        best_strength = -1
        
        for five_cards in combinations(seven_cards, 5):
            hand_list = list(five_cards)
            strength = self.evaluate_hand_strength(hand_list)
            if strength > best_strength:
                best_strength = strength
                best_hand = hand_list
        
        return best_hand
    
    def evaluate_hand_strength(self, hand: List[Card]) -> int:
        """Evaluate hand strength for comparison"""
        hand_type, tiebreakers = HandEvaluator.evaluate_hand(hand)
        strength = HandEvaluator.HAND_RANKINGS[hand_type] * 10000000
        
        # Add tiebreakers
        for i, tiebreaker in enumerate(tiebreakers):
            strength += tiebreaker * (100 ** (4 - i))
        
        return strength