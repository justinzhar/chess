"""
Piece class representing a chess piece.
"""

from constants import PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING


class Piece:
    """Represents a chess piece."""
    
    PIECE_NAMES = {
        PAWN: 'pawn',
        KNIGHT: 'knight',
        BISHOP: 'bishop',
        ROOK: 'rook',
        QUEEN: 'queen',
        KING: 'king'
    }
    
    def __init__(self, piece_type, color):
        self.piece_type = piece_type
        self.color = color
        self.has_moved = False
    
    def __repr__(self):
        return f"{self.color}_{self.get_name()}"
    
    def get_name(self):
        return self.PIECE_NAMES.get(self.piece_type, 'unknown')
