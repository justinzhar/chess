"""
ChessGame class handling rendering and game flow with modern premium UI.
"""

import pygame
import os
import random
import math

from constants import (
    VALID_MOVE_COLOR, CAPTURE_MOVE_COLOR,
    SELECTED_COLOR, LAST_MOVE_COLOR,
    WHITE, BLACK
)
from board import Board
from ai import ChessAI, PIECE_VALUES, PIECE_TABLES

# Themed board colors - dark slate
BOARD_LIGHT = (140, 135, 145)   # Slate gray
BOARD_DARK = (55, 50, 65)       # Deep charcoal purple


def evaluate_position(board):
    """Evaluate the board position. Positive = good for white."""
    score = 0
    
    for row in range(8):
        for col in range(8):
            piece = board.get_piece(row, col)
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
                
                # Add for white, subtract for black
                if piece.color == WHITE:
                    score += value
                else:
                    score -= value
    
    return score


class ChessGame:
    """Main chess game class handling rendering and game flow."""
    
    def __init__(self, screen, game_mode='human', difficulty=None, network_client=None, player_color=None):
        self.screen = screen
        self.game_mode = game_mode
        self.difficulty = difficulty
        self.network_client = network_client
        self.player_color = player_color  # 'white' or 'black' for online
        self.opponent_name = None
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.load_piece_images()
        self.load_sounds()
        self.update_dimensions()
        self.reset_game()
        
        self.selected_square = None
        self.valid_moves = []
        self.last_move = None
        
        self.ai_thinking = False
        self.ai_move_delay = 400
        self.ai_move_timer = 0
        
        # Animation
        self.time = 0
        
        # Online mode state
        self.opponent_disconnected = False
        self.pending_opponent_move = None
        self.rematch_requested = False
        self.opponent_wants_rematch = False
        self.rematch_pending = False
        
        # Set up network callbacks for online mode
        if self.network_client:
            self.network_client.on_opponent_move = self._on_opponent_move
            self.network_client.on_opponent_disconnect = self._on_opponent_disconnect
            self.network_client.on_opponent_resign = self._on_opponent_resign
            self.network_client.on_rematch_requested = self._on_rematch_requested
            self.network_client.on_rematch_start = self._on_rematch_start
    
    @property
    def board_flipped(self):
        """Return True if board should be flipped (black's perspective)."""
        return self.game_mode == 'online' and self.player_color == 'black'
    
    def flip_coords(self, row, col):
        """Flip board coordinates if viewing from black's perspective."""
        if self.board_flipped:
            return (7 - row, 7 - col)
        return (row, col)
    
    def update_dimensions(self):
        """Update dimensions based on current screen size."""
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        
        # Calculate board size to fit screen
        # Leave room for side panel and bottom labels
        side_panel_ratio = 0.25
        max_board_width = int(self.width * (1 - side_panel_ratio))
        max_board_height = self.height - 60  # More room for bottom labels
        
        # Board must be square
        self.board_size = min(max_board_width, max_board_height)
        self.board_size = (self.board_size // 8) * 8  # Make divisible by 8
        self.square_size = self.board_size // 8
        
        # Position the board (centered vertically with room for labels)
        self.board_x = 30
        self.board_y = (self.height - self.board_size) // 2 - 10
        
        # Side panel
        self.panel_x = self.board_x + self.board_size + 20
        self.panel_width = self.width - self.panel_x - 20
        self.panel_height = self.height - 40
        self.panel_y = 20
        
        # Scale piece images
        self.scale_images()
        
        # Fonts - SF Pro for quality
        base_size = min(self.width, self.height)
        self.font = pygame.font.SysFont('sfns', max(20, base_size // 32))
        self.small_font = pygame.font.SysFont('sfns', max(15, base_size // 45))
        self.title_font = pygame.font.SysFont('sfns', max(28, base_size // 22), bold=True)
    
    def load_piece_images(self):
        """Load piece images from assets folder."""
        self.original_images = {}
        self.scaled_images = {}
        base_path = os.path.join(os.path.dirname(__file__), 'assets', 'images', 'imgs-80px')
        
        piece_names = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
        colors = ['white', 'black']
        
        for color in colors:
            for piece in piece_names:
                filename = f"{color}_{piece}.png"
                filepath = os.path.join(base_path, filename)
                try:
                    image = pygame.image.load(filepath).convert_alpha()
                    self.original_images[f"{color}_{piece}"] = image
                except pygame.error as e:
                    print(f"Could not load image {filepath}: {e}")
    
    def scale_images(self):
        """Scale images to current square size."""
        target_size = int(self.square_size * 0.85)
        for key, image in self.original_images.items():
            self.scaled_images[key] = pygame.transform.smoothscale(
                image, (target_size, target_size)
            )
    
    def load_sounds(self):
        """Load sound effects."""
        self.sounds = {}
        base_path = os.path.join(os.path.dirname(__file__), 'assets', 'sounds')
        
        try:
            self.sounds['move'] = pygame.mixer.Sound(os.path.join(base_path, 'move.wav'))
            self.sounds['capture'] = pygame.mixer.Sound(os.path.join(base_path, 'capture.wav'))
        except pygame.error as e:
            print(f"Could not load sounds: {e}")
    
    def reset_game(self):
        """Reset the game to initial state."""
        self.board = Board()
        self.current_turn = WHITE
        self.game_over = False
        self.game_result = ""
        self.winner = None
        self.in_check = False
        self.move_history = []
        self.evaluation_history = []  # Track evaluation after each move
        self.current_eval = 0  # Current position evaluation
        self.selected_square = None
        self.valid_moves = []
        self.last_move = None
        self.ai_thinking = False
        self.ai_move_timer = 0
        
        # Checkmate animation
        self.checkmate_time = 0
        self.fallen_king_pos = None
        
        # Create AI if in AI mode
        if self.game_mode == 'ai':
            difficulty_settings = {
                'easy': {'depth': 1},
                'medium': {'depth': 2},
                'hard': {'depth': 3}
            }
            settings = difficulty_settings.get(self.difficulty, {'depth': 2})
            self.ai = ChessAI(self.board, BLACK, depth=settings['depth'])
        else:
            self.ai = None
    
    def get_board_pos(self, screen_pos):
        """Convert screen position to board position."""
        x, y = screen_pos
        if (self.board_x <= x < self.board_x + self.board_size and
            self.board_y <= y < self.board_y + self.board_size):
            col = (x - self.board_x) // self.square_size
            row = (y - self.board_y) // self.square_size
            # Flip for black's perspective
            return self.flip_coords(row, col)
        return None
    
    def handle_click(self, pos):
        """Handle mouse click on the board."""
        if self.game_over:
            return
        
        if self.game_mode == 'ai' and self.current_turn == BLACK:
            return
        
        # In online mode, only allow moves when it's your turn
        if self.game_mode == 'online':
            my_color = WHITE if self.player_color == 'white' else BLACK
            if self.current_turn != my_color:
                return
        
        board_pos = self.get_board_pos(pos)
        if board_pos is None:
            return
        
        row, col = board_pos
        
        if self.selected_square is None:
            piece = self.board.get_piece(row, col)
            if piece is not None and piece.color == self.current_turn:
                self.selected_square = (row, col)
                self.valid_moves = self.board.get_legal_moves(row, col)
        else:
            from_row, from_col = self.selected_square
            
            if (row, col) in self.valid_moves:
                self.make_move(from_row, from_col, row, col)
            else:
                piece = self.board.get_piece(row, col)
                if piece is not None and piece.color == self.current_turn:
                    self.selected_square = (row, col)
                    self.valid_moves = self.board.get_legal_moves(row, col)
                else:
                    self.selected_square = None
                    self.valid_moves = []
    
    def make_move(self, from_row, from_col, to_row, to_col):
        """Execute a move and update game state."""
        is_capture = self.board.make_move(from_row, from_col, to_row, to_col)
        
        if is_capture and 'capture' in self.sounds:
            self.sounds['capture'].play()
        elif 'move' in self.sounds:
            self.sounds['move'].play()
        
        self.last_move = (from_row, from_col, to_row, to_col)
        self.move_history.append(self.last_move)
        
        # Calculate and store evaluation
        self.current_eval = evaluate_position(self.board)
        self.evaluation_history.append(self.current_eval)
        
        self.current_turn = BLACK if self.current_turn == WHITE else WHITE
        self.in_check = self.board.is_in_check(self.current_turn)
        self.check_game_over()
        
        self.selected_square = None
        self.valid_moves = []
        
        if self.game_mode == 'ai' and self.current_turn == BLACK and not self.game_over:
            self.ai_thinking = True
            self.ai_move_timer = pygame.time.get_ticks()
        
        # In online mode, send move to server
        if self.game_mode == 'online' and self.network_client:
            self.network_client.send_move(from_row, from_col, to_row, to_col)
    
    def update_ai(self):
        """Handle AI move if it's AI's turn."""
        if not self.ai_thinking or self.game_over:
            return
        
        if pygame.time.get_ticks() - self.ai_move_timer < self.ai_move_delay:
            return
        
        move = self.ai.get_best_move()
        if move:
            self.make_move(move[0], move[1], move[2], move[3])
        
        self.ai_thinking = False
    
    def _on_opponent_move(self, move):
        """Callback when opponent makes a move."""
        self.pending_opponent_move = move
    
    def _on_opponent_disconnect(self):
        """Callback when opponent disconnects."""
        self.opponent_disconnected = True
        self.game_over = True
        self.game_result = "Opponent disconnected!"
    
    def _on_opponent_resign(self):
        """Callback when opponent resigns."""
        self.game_over = True
        my_color = 'White' if self.player_color == 'white' else 'Black'
        self.game_result = f"Opponent resigned! {my_color} wins!"
    
    def _on_rematch_requested(self):
        """Callback when opponent requests a rematch."""
        self.opponent_wants_rematch = True
    
    def _on_rematch_start(self, new_color):
        """Callback when rematch is confirmed and starting."""
        self.player_color = new_color
        self.rematch_pending = True
    
    def update_online(self):
        """Handle incoming opponent moves in online mode."""
        # Check for rematch start
        if self.rematch_pending:
            self.rematch_pending = False
            self.reset_game()
            # Update the board flip based on new color
            self.rematch_requested = False
            self.opponent_wants_rematch = False
            return
        
        if self.pending_opponent_move and not self.game_over:
            move = self.pending_opponent_move
            self.pending_opponent_move = None
            # Apply opponent's move directly (don't send back to server)
            from_row, from_col, to_row, to_col = move
            
            # Validate that there's a piece to move
            piece = self.board.get_piece(from_row, from_col)
            if piece is None:
                print(f"Warning: No piece at ({from_row}, {from_col}) for opponent move")
                return
            
            is_capture = self.board.make_move(from_row, from_col, to_row, to_col)
            
            if is_capture and 'capture' in self.sounds:
                self.sounds['capture'].play()
            elif 'move' in self.sounds:
                self.sounds['move'].play()
            
            self.last_move = (from_row, from_col, to_row, to_col)
            self.move_history.append(self.last_move)
            
            # Calculate and store evaluation
            self.current_eval = evaluate_position(self.board)
            self.evaluation_history.append(self.current_eval)
            
            self.current_turn = BLACK if self.current_turn == WHITE else WHITE
            self.in_check = self.board.is_in_check(self.current_turn)
            self.check_game_over()
            
            self.selected_square = None
            self.valid_moves = []
    
    def check_game_over(self):
        """Check if the game is over."""
        if not self.board.has_legal_moves(self.current_turn):
            self.game_over = True
            if self.in_check:
                self.winner = BLACK if self.current_turn == WHITE else WHITE
                self.game_result = f"Checkmate! {self.winner.capitalize()} wins!"
                # Start checkmate animation - find the losing king
                king_pos = self.board.find_king(self.current_turn)
                if king_pos:
                    self.fallen_king_pos = king_pos
                    self.checkmate_time = self.time
            else:
                self.game_result = "Stalemate! Draw!"
    
    def draw_board(self):
        """Draw the chess board with modern themed styling."""
        # Board shadow
        shadow_offset = 8
        shadow_rect = pygame.Rect(
            self.board_x + shadow_offset,
            self.board_y + shadow_offset,
            self.board_size, self.board_size
        )
        pygame.draw.rect(self.screen, (10, 8, 15), shadow_rect, border_radius=4)
        
        # Draw squares with themed colors
        for row in range(8):
            for col in range(8):
                x = self.board_x + col * self.square_size
                y = self.board_y + row * self.square_size
                
                is_light = (row + col) % 2 == 0
                color = BOARD_LIGHT if is_light else BOARD_DARK
                rect = pygame.Rect(x, y, self.square_size, self.square_size)
                pygame.draw.rect(self.screen, color, rect)
        
        # Subtle inner glow on board edges
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(self.screen, (120, 110, 130), board_rect, 2)
        
        # Highlight last move with elegant gold tint
        if self.last_move:
            for pos in [(self.last_move[0], self.last_move[1]), 
                       (self.last_move[2], self.last_move[3])]:
                row, col = self.flip_coords(pos[0], pos[1])
                highlight = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                highlight.fill((180, 160, 80, 70))  # Golden highlight
                self.screen.blit(highlight, 
                               (self.board_x + col * self.square_size,
                                self.board_y + row * self.square_size))
        
        # Highlight king in check with pulsing glow
        if self.in_check and not self.game_over:
            king_pos = self.board.find_king(self.current_turn)
            if king_pos:
                check_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                # Pulsing effect
                pulse = (math.sin(self.time * 6) + 1) / 2
                alpha = int(60 + 60 * pulse)
                check_surface.fill((255, 80, 80, alpha))
                draw_row, draw_col = self.flip_coords(king_pos[0], king_pos[1])
                self.screen.blit(check_surface,
                               (self.board_x + draw_col * self.square_size,
                                self.board_y + draw_row * self.square_size))
        
        # Highlight selected square
        if self.selected_square:
            row, col = self.flip_coords(self.selected_square[0], self.selected_square[1])
            highlight = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            highlight.fill(SELECTED_COLOR)
            self.screen.blit(highlight,
                           (self.board_x + col * self.square_size,
                            self.board_y + row * self.square_size))
        
        # Highlight valid moves
        for move in self.valid_moves:
            logical_row, logical_col = move
            draw_row, draw_col = self.flip_coords(logical_row, logical_col)
            x = self.board_x + draw_col * self.square_size
            y = self.board_y + draw_row * self.square_size
            move_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            
            if self.board.get_piece(logical_row, logical_col) is not None or move == self.board.en_passant_target:
                # Capture indicator - ring around edge
                pygame.draw.circle(move_surface, CAPTURE_MOVE_COLOR,
                                 (self.square_size // 2, self.square_size // 2),
                                 self.square_size // 2 - 4, 5)
            else:
                # Move indicator - dot in center
                pygame.draw.circle(move_surface, VALID_MOVE_COLOR,
                                 (self.square_size // 2, self.square_size // 2),
                                 self.square_size // 6)
            
            self.screen.blit(move_surface, (x, y))
        
        # Board border
        border_rect = pygame.Rect(self.board_x - 2, self.board_y - 2,
                                  self.board_size + 4, self.board_size + 4)
        pygame.draw.rect(self.screen, (80, 65, 50), border_rect, 3, border_radius=4)
        
        # Coordinate labels
        label_color = (100, 100, 110)
        for i in range(8):
            # Rank numbers (1-8) - flip for black
            rank_num = (i + 1) if self.board_flipped else (8 - i)
            rank_label = self.small_font.render(str(rank_num), True, label_color)
            self.screen.blit(rank_label,
                           (self.board_x - 18, self.board_y + i * self.square_size + self.square_size // 3))
            
            # File letters (a-h) - flip for black
            file_idx = (7 - i) if self.board_flipped else i
            file_label = self.small_font.render(chr(ord('a') + file_idx), True, label_color)
            self.screen.blit(file_label,
                           (self.board_x + i * self.square_size + self.square_size // 2 - 4,
                            self.board_y + self.board_size + 5))
    
    def draw_pieces(self):
        """Draw all pieces on the board with checkmate animation."""
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece is not None:
                    image_key = f"{piece.color}_{piece.get_name()}"
                    if image_key in self.scaled_images:
                        image = self.scaled_images[image_key]
                        # Flip coordinates for black's perspective
                        draw_row, draw_col = self.flip_coords(row, col)
                        base_x = self.board_x + draw_col * self.square_size + (self.square_size - image.get_width()) // 2
                        base_y = self.board_y + draw_row * self.square_size + (self.square_size - image.get_height()) // 2
                        
                        # Check if this is the fallen king
                        if (self.fallen_king_pos and 
                            self.fallen_king_pos == (row, col) and 
                            piece.get_name() == 'king'):
                            # Animate king falling over
                            elapsed = self.time - self.checkmate_time
                            fall_duration = 0.8
                            
                            if elapsed < fall_duration:
                                # Rotation and fall animation
                                progress = min(1.0, elapsed / fall_duration)
                                # Ease out
                                progress = 1 - (1 - progress) ** 3
                                
                                angle = progress * 90  # Rotate 90 degrees
                                
                                # Rotate the image
                                rotated = pygame.transform.rotate(image, -angle)
                                
                                # Offset to simulate falling
                                fall_offset_x = int(progress * self.square_size * 0.3)
                                fall_offset_y = int(progress * self.square_size * 0.1)
                                
                                # Center the rotated image
                                rot_rect = rotated.get_rect()
                                draw_x = base_x + fall_offset_x - (rot_rect.width - image.get_width()) // 2
                                draw_y = base_y + fall_offset_y - (rot_rect.height - image.get_height()) // 2
                                
                                self.screen.blit(rotated, (draw_x, draw_y))
                            else:
                                # Final fallen position
                                rotated = pygame.transform.rotate(image, -90)
                                rot_rect = rotated.get_rect()
                                draw_x = base_x + int(self.square_size * 0.3) - (rot_rect.width - image.get_width()) // 2
                                draw_y = base_y + int(self.square_size * 0.1) - (rot_rect.height - image.get_height()) // 2
                                self.screen.blit(rotated, (draw_x, draw_y))
                        else:
                            self.screen.blit(image, (base_x, base_y))
    
    def draw_side_panel(self):
        """Draw the modern information side panel."""
        # Panel background - subtle glass effect
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height)
        panel_surf = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        panel_surf.fill((30, 28, 40, 200))
        self.screen.blit(panel_surf, (self.panel_x, self.panel_y))
        pygame.draw.rect(self.screen, (60, 55, 70), panel_rect, 1, border_radius=12)
        
        padding = 20
        content_x = self.panel_x + padding
        y_offset = self.panel_y + padding
        
        # Game mode indicator
        if self.game_mode == 'online':
            opponent = self.opponent_name or 'Opponent'
            mode_text = f"Online vs {opponent}"
            color_text = f"(You are {self.player_color.capitalize()})"
            mode_surface = self.small_font.render(mode_text, True, (120, 115, 130))
            self.screen.blit(mode_surface, (content_x, y_offset))
            y_offset += 20
            color_surface = self.small_font.render(color_text, True, (100, 180, 100))
            self.screen.blit(color_surface, (content_x, y_offset))
            y_offset += 25
        elif self.game_mode == 'ai':
            mode_text = f"vs AI ({self.difficulty.capitalize()})" if self.difficulty else "vs AI"
            mode_surface = self.small_font.render(mode_text, True, (120, 115, 130))
            self.screen.blit(mode_surface, (content_x, y_offset))
            y_offset += 35
        else:
            mode_text = "vs Human"
            mode_surface = self.small_font.render(mode_text, True, (120, 115, 130))
            self.screen.blit(mode_surface, (content_x, y_offset))
            y_offset += 35
        
        # Current turn or game result
        if self.game_over:
            result_surface = self.font.render(self.game_result, True, (100, 200, 120))
            self.screen.blit(result_surface, (content_x, y_offset))
            
            # Show rematch UI for online mode
            if self.game_mode == 'online' and not self.opponent_disconnected:
                y_offset += 40
                if self.rematch_requested and self.opponent_wants_rematch:
                    rematch_text = "Rematch starting..."
                    rematch_color = (100, 200, 100)
                elif self.rematch_requested:
                    rematch_text = "Waiting for opponent..."
                    rematch_color = (180, 180, 100)
                elif self.opponent_wants_rematch:
                    rematch_text = "Opponent wants rematch!"
                    rematch_color = (100, 180, 255)
                    y_offset2 = y_offset + 25
                    accept_text = self.small_font.render("Press Y to accept", True, (100, 180, 255))
                    self.screen.blit(accept_text, (content_x, y_offset2))
                else:
                    rematch_text = "Press Y for rematch"
                    rematch_color = (150, 150, 160)
                
                rematch_surface = self.font.render(rematch_text, True, rematch_color)
                self.screen.blit(rematch_surface, (content_x, y_offset))
        else:
            turn_text = f"{self.current_turn.capitalize()}'s Turn"
            turn_surface = self.title_font.render(turn_text, True, (255, 255, 255))
            self.screen.blit(turn_surface, (content_x, y_offset))
            
            if self.in_check:
                y_offset += 35
                check_surface = self.font.render("CHECK!", True, (255, 100, 100))
                self.screen.blit(check_surface, (content_x, y_offset))
            
            if self.ai_thinking:
                y_offset += 35
                dots = "." * (int(self.time * 3) % 4)
                thinking_surface = self.font.render(f"AI thinking{dots}", True, (160, 155, 170))
                self.screen.blit(thinking_surface, (content_x, y_offset))
        
        y_offset += 50
        
        # Divider
        pygame.draw.line(self.screen, (50, 48, 60),
                        (content_x, y_offset), (self.panel_x + self.panel_width - padding, y_offset), 1)
        y_offset += 15
        
        # Evaluation bar
        eval_label = self.small_font.render("Evaluation", True, (140, 135, 150))
        self.screen.blit(eval_label, (content_x, y_offset))
        
        # Format eval score (convert centipawns to pawns)
        eval_pawns = self.current_eval / 100.0
        if abs(eval_pawns) >= 10:
            eval_text = f"+{int(eval_pawns)}" if eval_pawns > 0 else f"{int(eval_pawns)}"
        else:
            eval_text = f"+{eval_pawns:.1f}" if eval_pawns > 0 else f"{eval_pawns:.1f}"
        eval_color = (120, 200, 120) if eval_pawns >= 0 else (200, 120, 120)
        eval_score_surface = self.small_font.render(eval_text, True, eval_color)
        self.screen.blit(eval_score_surface, (content_x + 80, y_offset))
        y_offset += 22
        
        # Evaluation bar visual
        bar_width = self.panel_width - padding * 2
        bar_height = 12
        bar_x = content_x
        
        # Background (black side)
        pygame.draw.rect(self.screen, (40, 40, 45), (bar_x, y_offset, bar_width, bar_height), border_radius=3)
        
        # Calculate white's portion (0.5 = equal, clamped between 0 and 1)
        # Use sigmoid-like scaling for large advantages
        clamped_eval = max(-1000, min(1000, self.current_eval))
        white_portion = 0.5 + (clamped_eval / 2000.0)
        white_width = int(bar_width * white_portion)
        
        # White bar
        if white_width > 0:
            pygame.draw.rect(self.screen, (220, 220, 225), (bar_x, y_offset, white_width, bar_height), border_radius=3)
        
        # Center line
        center_x = bar_x + bar_width // 2
        pygame.draw.line(self.screen, (100, 100, 110), (center_x, y_offset), (center_x, y_offset + bar_height), 2)
        
        y_offset += 25
        
        # Move history header
        history_label = self.small_font.render("Move History", True, (140, 135, 150))
        self.screen.blit(history_label, (content_x, y_offset))
        y_offset += 25
        
        # Move history with evaluations
        max_moves = (self.panel_height - y_offset - 100) // 22
        start_idx = max(0, len(self.move_history) - max_moves)
        
        for i, move in enumerate(self.move_history[start_idx:]):
            actual_idx = start_idx + i
            move_num = actual_idx + 1
            from_sq = f"{chr(ord('a') + move[1])}{8 - move[0]}"
            to_sq = f"{chr(ord('a') + move[3])}{8 - move[2]}"
            
            # Get evaluation for this move
            if actual_idx < len(self.evaluation_history):
                move_eval = self.evaluation_history[actual_idx] / 100.0
                if abs(move_eval) >= 10:
                    eval_str = f"+{int(move_eval)}" if move_eval > 0 else f"{int(move_eval)}"
                else:
                    eval_str = f"+{move_eval:.1f}" if move_eval > 0 else f"{move_eval:.1f}"
            else:
                eval_str = ""
            
            move_text = f"{move_num}. {from_sq}-{to_sq}"
            
            is_white_move = actual_idx % 2 == 0
            color = (220, 220, 225) if is_white_move else (140, 140, 150)
            move_surface = self.small_font.render(move_text, True, color)
            self.screen.blit(move_surface, (content_x, y_offset))
            
            # Draw evaluation next to move
            if eval_str:
                eval_color = (100, 180, 100) if move_eval >= 0 else (180, 100, 100)
                eval_surface = self.small_font.render(eval_str, True, eval_color)
                self.screen.blit(eval_surface, (content_x + 95, y_offset))
            
            y_offset += 22
        
        # Controls at bottom - different for online mode
        controls_y = self.panel_y + self.panel_height - 60
        pygame.draw.line(self.screen, (50, 48, 60),
                        (content_x, controls_y - 10),
                        (self.panel_x + self.panel_width - padding, controls_y - 10), 1)
        
        if self.game_mode == 'online':
            controls = ["Y: Rematch", "ESC: Menu", "F11: Fullscreen"]
        else:
            controls = ["R: Restart", "ESC: Menu", "F11: Fullscreen"]
        for i, ctrl in enumerate(controls):
            ctrl_surface = self.small_font.render(ctrl, True, (100, 95, 110))
            self.screen.blit(ctrl_surface, (content_x, controls_y + i * 18))
    
    def draw_gradient_background(self):
        """Draw gradient background matching menu style."""
        random.seed(42)
        
        color_top = (15, 12, 30)
        color_mid = (20, 18, 42)
        color_bottom = (12, 20, 32)
        
        for y in range(self.height):
            t = y / self.height
            if t < 0.5:
                t2 = t * 2
                r = int(color_top[0] + (color_mid[0] - color_top[0]) * t2)
                g = int(color_top[1] + (color_mid[1] - color_top[1]) * t2)
                b = int(color_top[2] + (color_mid[2] - color_top[2]) * t2)
            else:
                t2 = (t - 0.5) * 2
                r = int(color_mid[0] + (color_bottom[0] - color_mid[0]) * t2)
                g = int(color_mid[1] + (color_bottom[1] - color_mid[1]) * t2)
                b = int(color_mid[2] + (color_bottom[2] - color_mid[2]) * t2)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))
        
        # Subtle noise
        noise_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for _ in range(int(self.width * self.height * 0.015)):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            alpha = random.randint(3, 10)
            noise_surf.set_at((x, y), (255, 255, 255, alpha))
        self.screen.blit(noise_surf, (0, 0))
    
    def draw(self):
        """Draw the complete game screen."""
        # Gradient background matching menu
        self.draw_gradient_background()
        
        # Board and pieces
        self.draw_board()
        self.draw_pieces()
        
        # Side panel
        self.draw_side_panel()
    
    def run(self):
        """Main game loop. Returns True to go back to menu, False/None to quit."""
        while self.running:
            self.time = pygame.time.get_ticks() / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.get_surface()
                    self.update_dimensions()
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_mode != 'online':
                        self.reset_game()
                    elif event.key == pygame.K_y and self.game_mode == 'online' and self.game_over:
                        # Request rematch
                        if not self.rematch_requested and self.network_client:
                            self.rematch_requested = True
                            self.network_client.request_rematch()
                    elif event.key == pygame.K_ESCAPE:
                        return True  # Go to menu
                    elif event.key == pygame.K_F11:
                        return 'toggle_fullscreen'
            
            if self.game_mode == 'ai':
                self.update_ai()
            elif self.game_mode == 'online':
                self.update_online()
            
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        return None
