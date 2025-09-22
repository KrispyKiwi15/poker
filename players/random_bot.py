"""
Random Bot - Makes random legal decisions
This is a simple example bot for testing the tournament system
"""
from typing import List, Dict, Any
import random

from bot_api import PokerBotAPI, PlayerAction
from engine.cards import Card
from engine.poker_game import GameState


class RandomBot(PokerBotAPI):
    """
    A simple bot that makes random legal decisions.
    Useful for testing the tournament system.
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self.hands_played = 0
    
    def get_action(self, game_state: GameState, hole_cards: List[Card], 
                   legal_actions: List[PlayerAction], min_bet: int, max_bet: int) -> tuple:
        """Make a random legal action"""
        
        # Choose a random legal action
        action = random.choice(legal_actions)
        
        # If raising, choose a random valid amount
        if action == PlayerAction.RAISE:
            # Random raise between min_bet and max_bet
            amount = random.randint(min_bet, max_bet)
            return action, amount
        
        # All other actions don't need an amount
        return action, 0
    
    def hand_complete(self, game_state: GameState, hand_result: Dict[str, Any]):
        """Track hands played"""
        self.hands_played += 1
        
        if self.hands_played % 20 == 0:
            self.logger.info(f"Played {self.hands_played} hands randomly")