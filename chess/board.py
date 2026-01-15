"""
Board class handling chess board state and move logic.
"""

from constants import (
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, WHITE, BLACK
)
from piece import Piece


class Board:
    """Handles chess board state and move generation."""
    
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.en_passant_target = None
        self.setup_board()
    
    def setup_board(self):
        """Set up the initial board position."""
        back_row = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        
        # Black pieces (rows 0 and 1)
        for col in range(8):
            self.board[0][col] = Piece(back_row[col], BLACK)
            self.board[1][col] = Piece(PAWN, BLACK)
        
        # White pieces (rows 6 and 7)
        for col in range(8):
            self.board[6][col] = Piece(PAWN, WHITE)
            self.board[7][col] = Piece(back_row[col], WHITE)
    
    def get_piece(self, row, col):
        """Get piece at given position."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def is_valid_position(self, row, col):
        """Check if position is within board bounds."""
        return 0 <= row < 8 and 0 <= col < 8
    
    def get_raw_moves(self, row, col):
        """Get all possible moves for a piece without considering check."""
        piece = self.get_piece(row, col)
        if piece is None:
            return []
        
        if piece.piece_type == PAWN:
            return self.get_pawn_moves(row, col, piece)
        elif piece.piece_type == KNIGHT:
            return self.get_knight_moves(row, col, piece)
        elif piece.piece_type == BISHOP:
            return self.get_bishop_moves(row, col, piece)
        elif piece.piece_type == ROOK:
            return self.get_rook_moves(row, col, piece)
        elif piece.piece_type == QUEEN:
            return self.get_queen_moves(row, col, piece)
        elif piece.piece_type == KING:
            return self.get_king_moves(row, col, piece)
        return []
    
    def get_pawn_moves(self, row, col, piece):
        """Get pawn moves including en passant."""
        moves = []
        direction = -1 if piece.color == WHITE else 1
        start_row = 6 if piece.color == WHITE else 1
        
        # Forward move
        new_row = row + direction
        if self.is_valid_position(new_row, col) and self.board[new_row][col] is None:
            moves.append((new_row, col))
            
            # Double move from starting position
            if row == start_row:
                new_row2 = row + 2 * direction
                if self.board[new_row2][col] is None:
                    moves.append((new_row2, col))
        
        # Diagonal captures
        for dc in [-1, 1]:
            new_col = col + dc
            if self.is_valid_position(new_row, new_col):
                target = self.board[new_row][new_col]
                if target is not None and target.color != piece.color:
                    moves.append((new_row, new_col))
                elif (new_row, new_col) == self.en_passant_target:
                    moves.append((new_row, new_col))
        
        return moves
    
    def get_knight_moves(self, row, col, piece):
        """Get knight moves."""
        moves = []
        deltas = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                  (1, -2), (1, 2), (2, -1), (2, 1)]
        
        for dr, dc in deltas:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                target = self.board[new_row][new_col]
                if target is None or target.color != piece.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def get_sliding_moves(self, row, col, piece, directions):
        """Get moves for sliding pieces (bishop, rook, queen)."""
        moves = []
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            while self.is_valid_position(new_row, new_col):
                target = self.board[new_row][new_col]
                if target is None:
                    moves.append((new_row, new_col))
                elif target.color != piece.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
                new_row += dr
                new_col += dc
        
        return moves
    
    def get_bishop_moves(self, row, col, piece):
        """Get bishop moves."""
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self.get_sliding_moves(row, col, piece, directions)
    
    def get_rook_moves(self, row, col, piece):
        """Get rook moves."""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self.get_sliding_moves(row, col, piece, directions)
    
    def get_queen_moves(self, row, col, piece):
        """Get queen moves."""
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),
                      (-1, 0), (1, 0), (0, -1), (0, 1)]
        return self.get_sliding_moves(row, col, piece, directions)
    
    def get_king_moves(self, row, col, piece):
        """Get king moves including castling."""
        moves = []
        
        # Regular moves
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                new_row, new_col = row + dr, col + dc
                if self.is_valid_position(new_row, new_col):
                    target = self.board[new_row][new_col]
                    if target is None or target.color != piece.color:
                        moves.append((new_row, new_col))
        
        # Castling
        if not piece.has_moved and not self.is_square_attacked(row, col, piece.color):
            if self.can_castle_kingside(row, col, piece):
                moves.append((row, col + 2))
            if self.can_castle_queenside(row, col, piece):
                moves.append((row, col - 2))
        
        return moves
    
    def can_castle_kingside(self, row, col, piece):
        """Check if kingside castling is possible."""
        rook = self.get_piece(row, 7)
        if rook is None or rook.piece_type != ROOK or rook.has_moved:
            return False
        
        for c in range(col + 1, 7):
            if self.board[row][c] is not None:
                return False
        
        for c in range(col + 1, col + 3):
            if self.is_square_attacked(row, c, piece.color):
                return False
        
        return True
    
    def can_castle_queenside(self, row, col, piece):
        """Check if queenside castling is possible."""
        rook = self.get_piece(row, 0)
        if rook is None or rook.piece_type != ROOK or rook.has_moved:
            return False
        
        for c in range(1, col):
            if self.board[row][c] is not None:
                return False
        
        for c in range(col - 2, col):
            if self.is_square_attacked(row, c, piece.color):
                return False
        
        return True
    
    def is_square_attacked(self, row, col, defending_color):
        """Check if a square is attacked by the opponent."""
        attacking_color = BLACK if defending_color == WHITE else WHITE
        
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece is not None and piece.color == attacking_color:
                    if piece.piece_type == KING:
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                if dr == 0 and dc == 0:
                                    continue
                                if r + dr == row and c + dc == col:
                                    return True
                    else:
                        moves = self.get_raw_moves(r, c)
                        if (row, col) in moves:
                            return True
        return False
    
    def find_king(self, color):
        """Find the position of the king."""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.piece_type == KING and piece.color == color:
                    return (row, col)
        return None
    
    def is_in_check(self, color):
        """Check if the given color's king is in check."""
        king_pos = self.find_king(color)
        if king_pos is None:
            return False
        return self.is_square_attacked(king_pos[0], king_pos[1], color)
    
    def is_move_legal(self, from_row, from_col, to_row, to_col):
        """Check if a move is legal (doesn't leave king in check)."""
        piece = self.board[from_row][from_col]
        captured = self.board[to_row][to_col]
        
        en_passant_capture = None
        if piece.piece_type == PAWN and (to_row, to_col) == self.en_passant_target:
            en_passant_row = from_row
            en_passant_capture = self.board[en_passant_row][to_col]
            self.board[en_passant_row][to_col] = None
        
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        
        in_check = self.is_in_check(piece.color)
        
        self.board[from_row][from_col] = piece
        self.board[to_row][to_col] = captured
        
        if en_passant_capture is not None:
            self.board[en_passant_row][to_col] = en_passant_capture
        
        return not in_check
    
    def get_legal_moves(self, row, col):
        """Get all legal moves for a piece (considering check)."""
        piece = self.get_piece(row, col)
        if piece is None:
            return []
        
        raw_moves = self.get_raw_moves(row, col)
        legal_moves = []
        
        for move in raw_moves:
            if self.is_move_legal(row, col, move[0], move[1]):
                legal_moves.append(move)
        
        return legal_moves
    
    def make_move(self, from_row, from_col, to_row, to_col):
        """Make a move on the board. Returns True if it was a capture."""
        piece = self.board[from_row][from_col]
        captured = self.board[to_row][to_col]
        is_capture = captured is not None
        
        # Handle en passant capture
        if piece.piece_type == PAWN and (to_row, to_col) == self.en_passant_target:
            self.board[from_row][to_col] = None
            is_capture = True
        
        # Handle castling
        if piece.piece_type == KING and abs(to_col - from_col) == 2:
            if to_col > from_col:  # Kingside
                rook = self.board[from_row][7]
                self.board[from_row][7] = None
                self.board[from_row][5] = rook
                rook.has_moved = True
            else:  # Queenside
                rook = self.board[from_row][0]
                self.board[from_row][0] = None
                self.board[from_row][3] = rook
                rook.has_moved = True
        
        # Update en passant target
        if piece.piece_type == PAWN and abs(to_row - from_row) == 2:
            self.en_passant_target = ((from_row + to_row) // 2, from_col)
        else:
            self.en_passant_target = None
        
        # Make the move
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.has_moved = True
        
        # Handle pawn promotion
        if piece.piece_type == PAWN:
            if (piece.color == WHITE and to_row == 0) or (piece.color == BLACK and to_row == 7):
                self.board[to_row][to_col] = Piece(QUEEN, piece.color)
                self.board[to_row][to_col].has_moved = True
        
        return is_capture
    
    def has_legal_moves(self, color):
        """Check if the given color has any legal moves."""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.color == color:
                    if len(self.get_legal_moves(row, col)) > 0:
                        return True
        return False
    
    def reset(self):
        """Reset the board to initial state."""
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.en_passant_target = None
        self.setup_board()
