"""
Poker Bot Template
Students should copy this template and implement their own strategy
"""
from typing import List, Dict, Any
import random

from bot_api import PokerBotAPI, PlayerAction, GameInfoAPI, get_legal_actions
from engine.cards import Card
from engine.poker_game import GameState


class TemplateBot(PokerBotAPI):
    """
    Template bot that demonstrates the basic structure.
    Students should rename this class and implement their own strategy.
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        
        # You can store information between hands here
        self.hands_played = 0
        self.opponent_aggression = {}  # Track opponent behavior
        self.my_wins = 0
        self.my_losses = 0
        
        # Example: track what opponents do in different situations
        self.opponent_fold_rate = {}
        self.opponent_raise_rate = {}
    
    def get_action(self, game_state: GameState, hole_cards: List[Card], 
                   legal_actions: List[PlayerAction], min_bet: int, max_bet: int) -> tuple:
        """
        Decide what action to take.
        
        This is where you implement your poker strategy!
        
        Available information:
        - game_state: Current pot, community cards, player chips, etc.
        - hole_cards: Your two cards
        - legal_actions: What actions you can legally take
        - min_bet/max_bet: Betting limits
        
        You can use the GameInfoAPI helper functions to get more information.
        """
        
        # Example strategy - students should replace this with their own logic
        
        # Get some useful information
        pot_odds = GameInfoAPI.get_pot_odds(game_state.pot, 
                                           GameInfoAPI.calculate_bet_amount(game_state.current_bet, 
                                                                           game_state.player_bets[self.name]))
        
        position_info = GameInfoAPI.get_position_info(game_state, self.name)
        opponents = GameInfoAPI.get_active_opponents(game_state, self.name)
        is_heads_up = GameInfoAPI.is_heads_up(game_state)
        
        # Simple example strategy:
        
        # 1. If we can check, sometimes check
        if PlayerAction.CHECK in legal_actions:
            if random.random() < 0.3:  # 30% chance to check
                return PlayerAction.CHECK, 0
        
        # 2. Evaluate our hand strength (very basic)
        hand_strength = self._evaluate_basic_hand_strength(hole_cards, game_state.community_cards)
        
        # 3. Make decision based on hand strength
        if hand_strength >= 0.8:  # Very strong hand
            if PlayerAction.RAISE in legal_actions:
                raise_amount = min(game_state.current_bet * 2, max_bet)
                return PlayerAction.RAISE, raise_amount
            elif PlayerAction.CALL in legal_actions:
                return PlayerAction.CALL, 0
                
        elif hand_strength >= 0.6:  # Good hand
            if PlayerAction.CALL in legal_actions:
                return PlayerAction.CALL, 0
            elif PlayerAction.CHECK in legal_actions:
                return PlayerAction.CHECK, 0
                
        elif hand_strength >= 0.3:  # Marginal hand
            # Consider pot odds
            if pot_odds > 3.0 and PlayerAction.CALL in legal_actions:
                return PlayerAction.CALL, 0
            elif PlayerAction.CHECK in legal_actions:
                return PlayerAction.CHECK, 0
        
        # Default: fold weak hands
        return PlayerAction.FOLD, 0
    
    def _evaluate_basic_hand_strength(self, hole_cards: List[Card], community_cards: List[Card]) -> float:
        """
        Basic hand strength evaluation (0.0 = weakest, 1.0 = strongest)
        Students should improve this with better poker logic!
        """
        if not hole_cards or len(hole_cards) != 2:
            return 0.0
        
        card1, card2 = hole_cards
        
        # Pocket pairs are strong
        if card1.rank == card2.rank:
            if card1.rank.value >= 10:  # High pocket pairs
                return 0.9
            elif card1.rank.value >= 6:  # Medium pocket pairs
                return 0.7
            else:  # Low pocket pairs
                return 0.5
        
        # High cards
        high_card = max(card1.rank.value, card2.rank.value)
        low_card = min(card1.rank.value, card2.rank.value)
        
        # Suited cards get bonus
        suited_bonus = 0.1 if card1.suit == card2.suit else 0.0
        
        # Connected cards get bonus
        connected_bonus = 0.1 if abs(card1.rank.value - card2.rank.value) == 1 else 0.0
        
        # Basic strength based on high card
        if high_card >= 13:  # King or Ace high
            base_strength = 0.6
        elif high_card >= 10:  # Ten or Jack high
            base_strength = 0.4
        else:
            base_strength = 0.2
        
        # Adjust for low card
        if low_card >= 10:
            base_strength += 0.2
        elif low_card >= 7:
            base_strength += 0.1
        
        return min(1.0, base_strength + suited_bonus + connected_bonus)
    
    def hand_complete(self, game_state: GameState, hand_result: Dict[str, Any]):
        """
        Called when a hand is finished. Learn from the results!
        
        This is where you can update your strategy based on what happened.
        """
        self.hands_played += 1
        
        # Track if we won or lost
        if 'winners' in hand_result and self.name in hand_result['winners']:
            self.my_wins += 1
            self.logger.info(f"Won hand #{self.hands_played}!")
        else:
            self.my_losses += 1
        
        # Update opponent tracking
        if 'showdown_hands' in hand_result:
            for opponent, hand_info in hand_result['showdown_hands'].items():
                if opponent != self.name:
                    # Track what kinds of hands opponents play
                    # Students can expand this tracking
                    pass
        
        # Log some statistics periodically
        if self.hands_played % 10 == 0:
            win_rate = self.my_wins / self.hands_played if self.hands_played > 0 else 0
            self.logger.info(f"After {self.hands_played} hands: {win_rate:.2%} win rate")
    
    def tournament_start(self, players: List[str], starting_chips: int):
        """Called when the tournament starts"""
        super().tournament_start(players, starting_chips)
        
        # Initialize opponent tracking
        for player in players:
            if player != self.name:
                self.opponent_aggression[player] = 0.5  # Start neutral
                self.opponent_fold_rate[player] = 0.5
                self.opponent_raise_rate[player] = 0.2
        
        self.logger.info(f"Tournament starting against {len(players)-1} opponents")
    
    def tournament_end(self, final_standings: List[tuple]):
        """Called when tournament ends"""
        super().tournament_end(final_standings)
        
        # Log final performance
        my_placement = next(place for name, chips, place in final_standings if name == self.name)
        total_players = len(final_standings)
        
        self.logger.info(f"Final placement: {my_placement}/{total_players}")
        if self.hands_played > 0:
            win_rate = self.my_wins / self.hands_played
            self.logger.info(f"Final win rate: {win_rate:.2%} over {self.hands_played} hands")


# TODO for students: Ideas to improve this bot
"""
Ideas for improving your poker bot:

1. Better Hand Evaluation:
   - Implement proper hand rankings with community cards
   - Calculate actual hand strength vs. just hole card strength
   - Consider drawing possibilities (straight/flush draws)

2. Opponent Modeling:
   - Track opponent betting patterns
   - Identify tight vs. loose players
   - Adjust strategy based on opponent type

3. Position Awareness:
   - Play tighter in early position
   - Play more aggressively in late position
   - Use position for bluffing opportunities

4. Pot Odds and Expected Value:
   - Calculate proper pot odds
   - Consider implied odds for drawing hands
   - Make mathematically correct decisions

5. Betting Strategy:
   - Implement proper bet sizing
   - Use continuation betting
   - Know when to bluff and when to fold

6. Tournament Strategy:
   - Adjust play based on chip stack size
   - Consider bubble play and ICM
   - Adapt to changing blind levels

7. Advanced Concepts:
   - Game theory optimal (GTO) play
   - Exploitative play vs. specific opponents
   - Range vs. range thinking
   
Remember: Start simple and gradually add complexity!
"""