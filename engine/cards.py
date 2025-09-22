"""
Poker card and deck management system
"""
import random
from enum import Enum
from typing import List, Tuple, Optional
from dataclasses import dataclass


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


@dataclass
class Card:
    rank: Rank
    suit: Suit
    
    def __str__(self) -> str:
        rank_str = {
            Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4", Rank.FIVE: "5",
            Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8", Rank.NINE: "9",
            Rank.TEN: "10", Rank.JACK: "J", Rank.QUEEN: "Q", Rank.KING: "K", Rank.ACE: "A"
        }
        return f"{rank_str[self.rank]}{self.suit.value}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self) -> int:
        return hash((self.rank, self.suit))


class Deck:
    def __init__(self):
        self.cards: List[Card] = []
        self.reset()
    
    def reset(self):
        """Reset deck with all 52 cards"""
        self.cards = [Card(rank, suit) for rank in Rank for suit in Suit]
    
    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)
    
    def deal_card(self) -> Optional[Card]:
        """Deal one card from the top of the deck"""
        if self.cards:
            return self.cards.pop()
        return None
    
    def cards_remaining(self) -> int:
        """Get number of cards remaining in deck"""
        return len(self.cards)


class HandEvaluator:
    """Evaluates poker hands and determines winners"""
    
    HAND_RANKINGS = {
        'high_card': 1,
        'pair': 2,
        'two_pair': 3,
        'three_of_a_kind': 4,
        'straight': 5,
        'flush': 6,
        'full_house': 7,
        'four_of_a_kind': 8,
        'straight_flush': 9,
        'royal_flush': 10
    }
    
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[str, List[int]]:
        """
        Evaluate a 5-card poker hand
        Returns: (hand_type, tie_breakers)
        tie_breakers is a list of ranks for comparison in case of ties
        """
        if len(cards) != 5:
            raise ValueError("Hand must contain exactly 5 cards")
        
        # Sort cards by rank (highest first)
        sorted_cards = sorted(cards, key=lambda x: x.rank.value, reverse=True)
        ranks = [card.rank.value for card in sorted_cards]
        suits = [card.suit for card in sorted_cards]
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight = HandEvaluator._is_straight(ranks)
        
        # Count ranks
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        # Sort by count, then by rank
        count_groups = {}
        for rank, count in rank_counts.items():
            if count not in count_groups:
                count_groups[count] = []
            count_groups[count].append(rank)
        
        # Sort each group by rank (highest first)
        for count in count_groups:
            count_groups[count].sort(reverse=True)
        
        # Determine hand type
        counts = sorted(rank_counts.values(), reverse=True)
        
        if is_straight and is_flush:
            if ranks[0] == 14 and ranks[4] == 10:  # A-K-Q-J-10
                return 'royal_flush', [14]
            else:
                return 'straight_flush', [ranks[0]]
        elif counts == [4, 1]:
            return 'four_of_a_kind', [count_groups[4][0], count_groups[1][0]]
        elif counts == [3, 2]:
            return 'full_house', [count_groups[3][0], count_groups[2][0]]
        elif is_flush:
            return 'flush', ranks
        elif is_straight:
            return 'straight', [ranks[0]]
        elif counts == [3, 1, 1]:
            return 'three_of_a_kind', [count_groups[3][0]] + sorted(count_groups[1], reverse=True)
        elif counts == [2, 2, 1]:
            pairs = sorted(count_groups[2], reverse=True)
            return 'two_pair', pairs + [count_groups[1][0]]
        elif counts == [2, 1, 1, 1]:
            return 'pair', [count_groups[2][0]] + sorted(count_groups[1], reverse=True)
        else:
            return 'high_card', ranks
    
    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        """Check if ranks form a straight"""
        # Handle ace-low straight (A-2-3-4-5)
        if ranks == [14, 5, 4, 3, 2]:
            return True
        
        # Check normal straight
        for i in range(1, len(ranks)):
            if ranks[i-1] - ranks[i] != 1:
                return False
        return True
    
    @staticmethod
    def compare_hands(hand1: List[Card], hand2: List[Card]) -> int:
        """
        Compare two hands
        Returns: 1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        hand1_type, hand1_tiebreakers = HandEvaluator.evaluate_hand(hand1)
        hand2_type, hand2_tiebreakers = HandEvaluator.evaluate_hand(hand2)
        
        # Compare hand rankings
        hand1_rank = HandEvaluator.HAND_RANKINGS[hand1_type]
        hand2_rank = HandEvaluator.HAND_RANKINGS[hand2_type]
        
        if hand1_rank > hand2_rank:
            return 1
        elif hand1_rank < hand2_rank:
            return -1
        
        # Same hand type, compare tiebreakers
        for t1, t2 in zip(hand1_tiebreakers, hand2_tiebreakers):
            if t1 > t2:
                return 1
            elif t1 < t2:
                return -1
        
        return 0  # Perfect tie