"""
Simple chess AI using minimax with alpha-beta pruning.
"""

import random
from constants import PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, WHITE, BLACK


# Piece values for evaluation
PIECE_VALUES = {
    PAWN: 100,
    KNIGHT: 320,
    BISHOP: 330,
    ROOK: 500,
    QUEEN: 900,
    KING: 20000
}

# Position bonuses for pieces (encourages good piece placement)
PAWN_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

ROOK_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

KING_TABLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
]

PIECE_TABLES = {
    PAWN: PAWN_TABLE,
    KNIGHT: KNIGHT_TABLE,
    BISHOP: BISHOP_TABLE,
    ROOK: ROOK_TABLE,
    QUEEN: QUEEN_TABLE,
    KING: KING_TABLE
}


class ChessAI:
    """Simple chess AI using minimax with alpha-beta pruning."""
    
    def __init__(self, board, color, depth=3):
        self.board = board
        self.color = color
        self.opponent_color = BLACK if color == WHITE else WHITE
        self.depth = depth
    
    def evaluate_board(self):
        """Evaluate the board position. Positive = good for AI."""
        score = 0
        
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece is not None:
                    # Base piece value
                    value = PIECE_VALUES[piece.piece_type]
                    
                    # Position bonus
                    table = PIECE_TABLES.get(piece.piece_type)
                    if table:
                        if piece.color == WHITE:
                            value += table[row][col]
                        else:
                            value += table[7 - row][col]
                    
                    # Add or subtract based on color
                    if piece.color == self.color:
                        score += value
                    else:
                        score -= value
        
        return score
    
    def get_all_moves(self, color):
        """Get all legal moves for a color."""
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece is not None and piece.color == color:
                    legal_moves = self.board.get_legal_moves(row, col)
                    for move in legal_moves:
                        moves.append((row, col, move[0], move[1]))
        return moves
    
    def make_temp_move(self, from_row, from_col, to_row, to_col):
        """Make a temporary move and return undo info."""
        piece = self.board.board[from_row][from_col]
        captured = self.board.board[to_row][to_col]
        old_en_passant = self.board.en_passant_target
        old_has_moved = piece.has_moved
        
        # Handle en passant capture
        en_passant_captured = None
        en_passant_pos = None
        if piece.piece_type == PAWN and (to_row, to_col) == self.board.en_passant_target:
            en_passant_pos = (from_row, to_col)
            en_passant_captured = self.board.board[from_row][to_col]
            self.board.board[from_row][to_col] = None
        
        # Handle castling
        castling_info = None
        if piece.piece_type == KING and abs(to_col - from_col) == 2:
            if to_col > from_col:  # Kingside
                rook = self.board.board[from_row][7]
                castling_info = (from_row, 7, from_row, 5, rook, rook.has_moved)
                self.board.board[from_row][7] = None
                self.board.board[from_row][5] = rook
                rook.has_moved = True
            else:  # Queenside
                rook = self.board.board[from_row][0]
                castling_info = (from_row, 0, from_row, 3, rook, rook.has_moved)
                self.board.board[from_row][0] = None
                self.board.board[from_row][3] = rook
                rook.has_moved = True
        
        # Update en passant target
        if piece.piece_type == PAWN and abs(to_row - from_row) == 2:
            self.board.en_passant_target = ((from_row + to_row) // 2, from_col)
        else:
            self.board.en_passant_target = None
        
        # Make the move
        self.board.board[to_row][to_col] = piece
        self.board.board[from_row][from_col] = None
        piece.has_moved = True
        
        return {
            'piece': piece,
            'captured': captured,
            'from_pos': (from_row, from_col),
            'to_pos': (to_row, to_col),
            'old_en_passant': old_en_passant,
            'old_has_moved': old_has_moved,
            'en_passant_captured': en_passant_captured,
            'en_passant_pos': en_passant_pos,
            'castling_info': castling_info
        }
    
    def undo_temp_move(self, undo_info):
        """Undo a temporary move."""
        piece = undo_info['piece']
        from_row, from_col = undo_info['from_pos']
        to_row, to_col = undo_info['to_pos']
        
        # Restore piece position
        self.board.board[from_row][from_col] = piece
        self.board.board[to_row][to_col] = undo_info['captured']
        piece.has_moved = undo_info['old_has_moved']
        self.board.en_passant_target = undo_info['old_en_passant']
        
        # Restore en passant captured piece
        if undo_info['en_passant_captured']:
            ep_row, ep_col = undo_info['en_passant_pos']
            self.board.board[ep_row][ep_col] = undo_info['en_passant_captured']
        
        # Restore castling
        if undo_info['castling_info']:
            r_from_row, r_from_col, r_to_row, r_to_col, rook, old_moved = undo_info['castling_info']
            self.board.board[r_from_col][r_from_row] = None  # Clear new position
            self.board.board[r_to_row][r_to_col] = None
            self.board.board[r_from_row][r_from_col] = rook
            rook.has_moved = old_moved
    
    def minimax(self, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return self.evaluate_board(), None
        
        current_color = self.color if maximizing else self.opponent_color
        moves = self.get_all_moves(current_color)
        
        if not moves:
            # Check for checkmate or stalemate
            if self.board.is_in_check(current_color):
                return -100000 if maximizing else 100000, None
            return 0, None  # Stalemate
        
        best_move = None
        
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                undo = self.make_temp_move(*move)
                eval_score, _ = self.minimax(depth - 1, alpha, beta, False)
                self.undo_temp_move(undo)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                undo = self.make_temp_move(*move)
                eval_score, _ = self.minimax(depth - 1, alpha, beta, True)
                self.undo_temp_move(undo)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    def get_best_move(self):
        """Get the best move for the AI."""
        _, best_move = self.minimax(self.depth, float('-inf'), float('inf'), True)
        
        if best_move is None:
            # Fallback: pick a random legal move
            moves = self.get_all_moves(self.color)
            if moves:
                best_move = random.choice(moves)
        
        return best_move
