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
            # Online multiplayer - connect to server
            from network import NetworkClient, WEBSOCKETS_AVAILABLE
            
            if not WEBSOCKETS_AVAILABLE:
                font = pygame.font.SysFont('sfns', 24)
                screen.fill((20, 18, 35))
                error_text = font.render("Error: 'websockets' module not installed", True, (255, 100, 100))
                help_text = font.render("Run: pip install websockets", True, (200, 200, 210))
                back_text = font.render("Press any key to go back...", True, (150, 150, 160))
                screen.blit(error_text, (50, 200))
                screen.blit(help_text, (50, 250))
                screen.blit(back_text, (50, 320))
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
            
            # Create network client and connect
            network = NetworkClient()
            
            # State for matchmaking
            match_found = False
            player_color = None
            opponent_name = None
            connection_error = None
            waiting_for_match = False
            
            def on_waiting():
                nonlocal waiting_for_match
                waiting_for_match = True
            
            def on_match_found(color, opponent):
                nonlocal match_found, player_color, opponent_name
                match_found = True
                player_color = color
                opponent_name = opponent
            
            def on_error(error):
                nonlocal connection_error
                connection_error = error
            
            network.on_waiting = on_waiting
            network.on_match_found = on_match_found
            network.on_error = on_error
            
            # Start connection
            network.start()
            
            font = pygame.font.SysFont('sfns', 24)
            title_font = pygame.font.SysFont('sfns', 32, bold=True)
            
            # Wait for match or cancel
            waiting = True
            start_time = pygame.time.get_ticks()
            
            while waiting and running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        waiting = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            waiting = False
                
                # Check for match found
                if match_found:
                    waiting = False
                    continue
                
                # Check for connection error
                if connection_error:
                    screen.fill((20, 18, 35))
                    error_text = font.render(f"Connection error: {connection_error}", True, (255, 100, 100))
                    back_text = font.render("Press ESC to go back...", True, (150, 150, 160))
                    screen.blit(error_text, (50, 200))
                    screen.blit(back_text, (50, 260))
                    pygame.display.flip()
                    continue
                
                # Draw waiting screen
                screen.fill((20, 18, 35))
                
                elapsed = (pygame.time.get_ticks() - start_time) / 1000
                dots = "." * (int(elapsed * 2) % 4)
                
                if waiting_for_match:
                    status_text = f"Waiting for opponent{dots}"
                else:
                    status_text = f"Connecting to server{dots}"
                
                title = title_font.render("Online Multiplayer", True, (255, 255, 255))
                status = font.render(status_text, True, (200, 200, 210))
                cancel = font.render("Press ESC to cancel", True, (120, 120, 130))
                
                screen.blit(title, (50, 150))
                screen.blit(status, (50, 220))
                screen.blit(cancel, (50, 280))
                
                pygame.display.flip()
                pygame.time.wait(50)
            
            if not match_found:
                network.stop()
                continue
            
            # Start game with network
            game = ChessGame(screen, 'online', network_client=network, player_color=player_color)
            game.opponent_name = opponent_name
            game_result = game.run()
            
            # Cleanup network
            network.stop()
            
            if game_result is None:
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
