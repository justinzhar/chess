"""
Menu screen for the chess game - clean minimalist design.
"""

import pygame
import math
import os

from constants import WHITE, BLACK


class Menu:
    """Clean minimalist menu design."""
    
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.update_dimensions()
        
        self.hovered_button = None
        self.menu_state = 'mode'
        self.time = 0
        self.hover_animations = {}
        
        # Load chess piece images
        self.piece_images = {}
        self.load_pieces()
    
    def load_pieces(self):
        """Load chess piece images for decoration."""
        try:
            base_path = os.path.join(os.path.dirname(__file__), 'assets', 'images', 'imgs-80px')
            pieces = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn']
            for color in ['white', 'black']:
                for piece in pieces:
                    path = os.path.join(base_path, f'{color}_{piece}.png')
                    if os.path.exists(path):
                        img = pygame.image.load(path).convert_alpha()
                        self.piece_images[f'{color}_{piece}'] = img
        except Exception:
            pass
    
    def update_dimensions(self):
        """Update responsive dimensions."""
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        self.scale = min(self.width / 1200, self.height / 800, 1.3)
        
        # Clean modern fonts - SF Pro for high quality
        self.font_title = pygame.font.SysFont('sfnsdisplay', int(58 * self.scale), bold=True)
        self.font_button = pygame.font.SysFont('sfns', int(22 * self.scale))
        self.font_small = pygame.font.SysFont('sfns', int(15 * self.scale))
    
    def draw_background(self):
        """Draw premium gradient background with subtle texture."""
        import random
        random.seed(42)  # Consistent noise pattern
        
        # Rich gradient colors
        color_top = (15, 12, 30)       # Deep dark purple
        color_mid = (20, 18, 42)       # Rich purple
        color_bottom = (12, 20, 32)    # Dark blue
        
        # Create gradient surface
        for y in range(self.height):
            t = y / self.height
            
            # Two-stage gradient for more depth
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
        
        # Add subtle noise texture for premium feel
        noise_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for _ in range(int(self.width * self.height * 0.02)):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            alpha = random.randint(3, 12)
            noise_surf.set_at((x, y), (255, 255, 255, alpha))
        self.screen.blit(noise_surf, (0, 0))
    
    def draw_chess_board(self):
        """Draw clean chess board with pieces."""
        board_size = int(280 * self.scale)
        square_size = board_size // 8
        actual_board_size = square_size * 8  # Actual size after integer division
        
        # Position board on left side
        board_x = int(self.width * 0.28) - actual_board_size // 2
        board_y = self.height // 2 - actual_board_size // 2
        
        # Board colors - match game board
        light = (140, 135, 145)   # Slate gray
        dark = (55, 50, 65)       # Deep charcoal purple
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                is_light = (row + col) % 2 == 0
                color = light if is_light else dark
                x = board_x + col * square_size
                y = board_y + row * square_size
                pygame.draw.rect(self.screen, color, (x, y, square_size, square_size))
        
        # Simple border - use actual_board_size for correct alignment
        pygame.draw.rect(self.screen, (120, 110, 130), 
                        (board_x - 2, board_y - 2, actual_board_size + 4, actual_board_size + 4), 2)
        
        # Draw pieces
        if self.piece_images:
            piece_size = int(square_size * 0.85)
            piece_layout = [
                (0, 0, 'black_rook'), (0, 1, 'black_knight'), (0, 2, 'black_bishop'),
                (0, 3, 'black_queen'), (0, 4, 'black_king'), (0, 5, 'black_bishop'),
                (0, 6, 'black_knight'), (0, 7, 'black_rook'),
                (1, 0, 'black_pawn'), (1, 1, 'black_pawn'), (1, 2, 'black_pawn'),
                (1, 3, 'black_pawn'), (1, 4, 'black_pawn'), (1, 5, 'black_pawn'),
                (1, 6, 'black_pawn'), (1, 7, 'black_pawn'),
                (6, 0, 'white_pawn'), (6, 1, 'white_pawn'), (6, 2, 'white_pawn'),
                (6, 3, 'white_pawn'), (6, 4, 'white_pawn'), (6, 5, 'white_pawn'),
                (6, 6, 'white_pawn'), (6, 7, 'white_pawn'),
                (7, 0, 'white_rook'), (7, 1, 'white_knight'), (7, 2, 'white_bishop'),
                (7, 3, 'white_queen'), (7, 4, 'white_king'), (7, 5, 'white_bishop'),
                (7, 6, 'white_knight'), (7, 7, 'white_rook'),
            ]
            
            for row, col, piece_key in piece_layout:
                if piece_key in self.piece_images:
                    img = self.piece_images[piece_key]
                    scaled = pygame.transform.smoothscale(img, (piece_size, piece_size))
                    x = board_x + col * square_size + (square_size - piece_size) // 2
                    y = board_y + row * square_size + (square_size - piece_size) // 2
                    self.screen.blit(scaled, (x, y))
    
    def draw_text_button(self, rect, text, is_hovered):
        """Draw simple text button."""
        btn_id = text
        target = 1.0 if is_hovered else 0.0
        current = self.hover_animations.get(btn_id, 0.0)
        self.hover_animations[btn_id] = current + (target - current) * 0.2
        progress = self.hover_animations[btn_id]
        
        # Colors
        normal = (140, 135, 150)
        hover = (255, 255, 255)
        color = tuple(int(normal[i] + (hover[i] - normal[i]) * progress) for i in range(3))
        
        text_surf = self.font_button.render(text, True, color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
    
    def draw_title(self):
        """Draw title on right side."""
        title_x = int(self.width * 0.68)
        title_y = int(self.height * 0.25)
        
        title = self.font_title.render("Chess", True, (255, 255, 255))
        title_rect = title.get_rect(center=(title_x, title_y))
        self.screen.blit(title, title_rect)
    
    def draw_mode_selection(self):
        """Draw mode selection on right side."""
        menu_x = int(self.width * 0.68)
        start_y = int(self.height * 0.38)
        
        button_width = int(220 * self.scale)
        button_height = int(45 * self.scale)
        spacing = int(18 * self.scale)
        
        self.mode_buttons = {}
        
        # Player vs Player
        pvp_rect = pygame.Rect(menu_x - button_width // 2, start_y, button_width, button_height)
        self.draw_text_button(pvp_rect, "Player vs Player", self.hovered_button == 'human')
        self.mode_buttons['human'] = pvp_rect
        
        # Player vs Computer
        ai_rect = pygame.Rect(menu_x - button_width // 2, start_y + button_height + spacing, 
                             button_width, button_height)
        self.draw_text_button(ai_rect, "Player vs Computer", self.hovered_button == 'ai')
        self.mode_buttons['ai'] = ai_rect
        
        # Online Multiplayer
        online_rect = pygame.Rect(menu_x - button_width // 2, start_y + 2 * (button_height + spacing), 
                                 button_width, button_height)
        self.draw_text_button(online_rect, "Online Multiplayer", self.hovered_button == 'online')
        self.mode_buttons['online'] = online_rect
    
    def draw_difficulty_selection(self):
        """Draw difficulty selection on right side."""
        menu_x = int(self.width * 0.68)
        start_y = int(self.height * 0.40)
        
        button_width = int(150 * self.scale)
        button_height = int(40 * self.scale)
        spacing = int(15 * self.scale)
        
        difficulties = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
        self.difficulty_buttons = {}
        
        for i, (key, label) in enumerate(difficulties):
            rect = pygame.Rect(menu_x - button_width // 2, 
                             start_y + i * (button_height + spacing),
                             button_width, button_height)
            self.draw_text_button(rect, label, self.hovered_button == key)
            self.difficulty_buttons[key] = rect
        
        # Back button
        back_y = start_y + 3 * (button_height + spacing) + int(20 * self.scale)
        self.back_button = pygame.Rect(menu_x - button_width // 2, back_y, button_width, button_height)
        self.draw_text_button(self.back_button, "Back", self.hovered_button == 'back')
    
    def draw_exit_confirmation(self):
        """Draw exit confirmation overlay."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        msg = self.font_button.render("Exit to Desktop?", True, (255, 255, 255))
        msg_rect = msg.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(msg, msg_rect)
        
        button_width = int(100 * self.scale)
        button_height = int(40 * self.scale)
        spacing = 40
        
        self.exit_buttons = {}
        
        yes_rect = pygame.Rect(self.width // 2 - button_width - spacing // 2,
                              self.height // 2 + 20, button_width, button_height)
        self.draw_text_button(yes_rect, "Yes", self.hovered_button == 'exit_yes')
        self.exit_buttons['exit_yes'] = yes_rect
        
        no_rect = pygame.Rect(self.width // 2 + spacing // 2,
                             self.height // 2 + 20, button_width, button_height)
        self.draw_text_button(no_rect, "No", self.hovered_button == 'exit_no')
        self.exit_buttons['exit_no'] = no_rect
    
    def draw_footer(self):
        """Draw footer."""
        footer = self.font_small.render("F11 Fullscreen  |  ESC Menu", True, (80, 80, 90))
        footer_rect = footer.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(footer, footer_rect)
    
    def draw(self):
        """Render menu."""
        self.draw_background()
        self.draw_chess_board()
        self.draw_title()
        
        if self.menu_state == 'mode':
            self.draw_mode_selection()
        elif self.menu_state == 'difficulty':
            self.draw_difficulty_selection()
        
        self.draw_footer()
        
        if self.menu_state == 'exit_confirm':
            self.draw_exit_confirmation()
    
    def run(self):
        """Main menu loop."""
        running = True
        self.menu_state = 'mode'
        
        while running:
            self.time = pygame.time.get_ticks() / 1000.0
            mouse_pos = pygame.mouse.get_pos()
            self.update_dimensions()
            
            # Update hover
            self.hovered_button = None
            
            if self.menu_state == 'exit_confirm':
                if hasattr(self, 'exit_buttons'):
                    for name, rect in self.exit_buttons.items():
                        if rect.collidepoint(mouse_pos):
                            self.hovered_button = name
                            break
            elif self.menu_state == 'mode':
                if hasattr(self, 'mode_buttons'):
                    for name, rect in self.mode_buttons.items():
                        if rect.collidepoint(mouse_pos):
                            self.hovered_button = name
                            break
            elif self.menu_state == 'difficulty':
                if hasattr(self, 'back_button') and self.back_button.collidepoint(mouse_pos):
                    self.hovered_button = 'back'
                elif hasattr(self, 'difficulty_buttons'):
                    for name, rect in self.difficulty_buttons.items():
                        if rect.collidepoint(mouse_pos):
                            self.hovered_button = name
                            break
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.get_surface()
                    self.update_dimensions()
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        return 'toggle_fullscreen'
                    elif event.key == pygame.K_ESCAPE:
                        if self.menu_state == 'exit_confirm':
                            self.menu_state = 'mode'
                        elif self.menu_state == 'difficulty':
                            self.menu_state = 'mode'
                        else:
                            self.menu_state = 'exit_confirm'
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.hovered_button:
                        if self.menu_state == 'exit_confirm':
                            if self.hovered_button == 'exit_yes':
                                return None
                            elif self.hovered_button == 'exit_no':
                                self.menu_state = 'mode'
                        elif self.menu_state == 'mode':
                            if self.hovered_button == 'human':
                                return ('human', None)
                            elif self.hovered_button == 'ai':
                                self.menu_state = 'difficulty'
                            elif self.hovered_button == 'online':
                                return ('online', None)
                        elif self.menu_state == 'difficulty':
                            if self.hovered_button == 'back':
                                self.menu_state = 'mode'
                            else:
                                return ('ai', self.hovered_button)
            
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        return None
