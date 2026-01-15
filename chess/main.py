"""
Chess Game in Pygame
Entry point with menu system and fullscreen support.
"""

import pygame
from menu import Menu
from game import ChessGame


def main():
    pygame.init()
    pygame.mixer.init()
    
    # Get display info for fullscreen
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h
    
    # Start in windowed mode with a nice default size
    window_width = min(1200, screen_width - 100)
    window_height = min(800, screen_height - 100)
    
    screen = pygame.display.set_mode(
        (window_width, window_height),
        pygame.RESIZABLE
    )
    pygame.display.set_caption("Chess")
    
    # Set icon if available
    try:
        import os
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'images', 'imgs-80px', 'white_knight.png')
        if os.path.exists(icon_path):
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
    except:
        pass
    
    running = True
    is_fullscreen = False
    
    while running:
        # Show menu
        menu = Menu(screen)
        result = menu.run()
        
        if result is None:
            # User closed the window
            break
        
        if result == 'toggle_fullscreen':
            is_fullscreen = not is_fullscreen
            if is_fullscreen:
                screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                screen = pygame.display.set_mode(
                    (window_width, window_height),
                    pygame.RESIZABLE
                )
            continue
        
        game_mode, difficulty = result
        
        if game_mode == 'online':
            # Online multiplayer - need server URL
            # For now, show a message
            font = pygame.font.SysFont('sfns', 24)
            screen.fill((20, 18, 35))
            lines = [
                "Online Multiplayer Setup",
                "",
                "1. Deploy the server folder to Railway:",
                "   - Push chess/server/ to GitHub",
                "   - Connect Railway to your repo",
                "   - Get your server URL",
                "",
                "2. Update SERVER_URL in network.py",
                "",
                "Press any key to go back..."
            ]
            y = 150
            for line in lines:
                text = font.render(line, True, (200, 200, 210))
                screen.blit(text, (50, y))
                y += 35
            pygame.display.flip()
            
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        waiting = False
                    elif event.type == pygame.KEYDOWN:
                        waiting = False
            continue
        
        # Start game with selected mode and difficulty
        game = ChessGame(screen, game_mode, difficulty)
        game_result = game.run()
        
        if game_result is None:
            # User closed the window
            break
        elif game_result == 'toggle_fullscreen':
            is_fullscreen = not is_fullscreen
            if is_fullscreen:
                screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                screen = pygame.display.set_mode(
                    (window_width, window_height),
                    pygame.RESIZABLE
                )
        # Otherwise go back to menu
    
    pygame.quit()


if __name__ == "__main__":
    main()
