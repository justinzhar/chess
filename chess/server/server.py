"""
Chess Multiplayer Server
Deploy on Railway, Render, or any Python hosting.
"""

import asyncio
import json
import os
from aiohttp import web
import aiohttp

# Store active games and waiting players
games = {}  # game_id -> {players: [], board_state: ..., current_turn: ...}
waiting_player = None  # WebSocket of player waiting for match
waiting_player_info = None
player_games = {}  # ws -> {game_id, color} - track game info for each player


async def websocket_handler(request):
    """Handle WebSocket connections for multiplayer."""
    global waiting_player, waiting_player_info
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                action = data.get('action')
                
                if action == 'find_match':
                    # Player looking for a match
                    if waiting_player is None or waiting_player.closed:
                        # No one waiting, this player waits
                        waiting_player = ws
                        waiting_player_info = data.get('name', 'Player')
                        await ws.send_json({
                            'type': 'waiting',
                            'message': 'Waiting for opponent...'
                        })
                    else:
                        # Match found! Create game
                        game_id = f"game_{len(games)}"
                        games[game_id] = {
                            'players': {
                                'white': waiting_player,
                                'black': ws
                            },
                            'current_turn': 'white'
                        }
                        
                        # Track game info for both players
                        player_games[waiting_player] = {'game_id': game_id, 'color': 'white'}
                        player_games[ws] = {'game_id': game_id, 'color': 'black'}
                        
                        # Notify both players
                        await waiting_player.send_json({
                            'type': 'game_start',
                            'game_id': game_id,
                            'color': 'white',
                            'opponent': data.get('name', 'Player')
                        })
                        await ws.send_json({
                            'type': 'game_start',
                            'game_id': game_id,
                            'color': 'black',
                            'opponent': waiting_player_info
                        })
                        
                        # Clear waiting player
                        waiting_player = None
                        waiting_player_info = None
                
                elif action == 'move':
                    # Player made a move
                    game_id = data.get('game_id')
                    player_info = player_games.get(ws)
                    if game_id in games and player_info:
                        game = games[game_id]
                        player_color = player_info['color']
                        # Send move to opponent
                        opponent_color = 'black' if player_color == 'white' else 'white'
                        opponent_ws = game['players'].get(opponent_color)
                        if opponent_ws and not opponent_ws.closed:
                            await opponent_ws.send_json({
                                'type': 'opponent_move',
                                'move': data.get('move')
                            })
                
                elif action == 'resign':
                    game_id = data.get('game_id')
                    player_info = player_games.get(ws)
                    if game_id in games and player_info:
                        game = games[game_id]
                        player_color = player_info['color']
                        opponent_color = 'black' if player_color == 'white' else 'white'
                        opponent_ws = game['players'].get(opponent_color)
                        if opponent_ws and not opponent_ws.closed:
                            await opponent_ws.send_json({
                                'type': 'opponent_resigned'
                            })
                        # Cleanup
                        if opponent_ws in player_games:
                            del player_games[opponent_ws]
                        del games[game_id]
                        del player_games[ws]
                
                elif action == 'rematch_request':
                    # Player wants a rematch
                    game_id = data.get('game_id')
                    player_info = player_games.get(ws)
                    if player_info:
                        game_id = player_info['game_id']
                        if game_id in games:
                            game = games[game_id]
                            player_color = player_info['color']
                            opponent_color = 'black' if player_color == 'white' else 'white'
                            opponent_ws = game['players'].get(opponent_color)
                            
                            # Mark this player as wanting rematch
                            game.setdefault('rematch_requests', set()).add(player_color)
                            
                            # Notify opponent
                            if opponent_ws and not opponent_ws.closed:
                                await opponent_ws.send_json({
                                    'type': 'rematch_requested'
                                })
                            
                            # Check if both players want rematch
                            if len(game.get('rematch_requests', set())) >= 2:
                                # Both want rematch - swap colors and start new game
                                new_game_id = f"game_{len(games)}"
                                # Swap colors
                                new_white = game['players']['black']
                                new_black = game['players']['white']
                                
                                games[new_game_id] = {
                                    'players': {
                                        'white': new_white,
                                        'black': new_black
                                    },
                                    'current_turn': 'white'
                                }
                                
                                # Update player tracking
                                player_games[new_white] = {'game_id': new_game_id, 'color': 'white'}
                                player_games[new_black] = {'game_id': new_game_id, 'color': 'black'}
                                
                                # Notify both players
                                await new_white.send_json({
                                    'type': 'rematch_start',
                                    'game_id': new_game_id,
                                    'color': 'white'
                                })
                                await new_black.send_json({
                                    'type': 'rematch_start',
                                    'game_id': new_game_id,
                                    'color': 'black'
                                })
                                
                                # Clean up old game
                                del games[game_id]
                        
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
    
    except Exception as e:
        print(f'Error: {e}')
    
    finally:
        # Clean up on disconnect
        if waiting_player == ws:
            waiting_player = None
            waiting_player_info = None
        
        player_info = player_games.get(ws)
        if player_info:
            game_id = player_info['game_id']
            player_color = player_info['color']
            if game_id in games:
                game = games[game_id]
                opponent_color = 'black' if player_color == 'white' else 'white'
                opponent_ws = game['players'].get(opponent_color)
                if opponent_ws and not opponent_ws.closed:
                    await opponent_ws.send_json({
                        'type': 'opponent_disconnected'
                    })
                # Clean up opponent's entry
                if opponent_ws in player_games:
                    del player_games[opponent_ws]
                del games[game_id]
            del player_games[ws]
    
    return ws


async def health_check(request):
    """Health check endpoint for Railway."""
    return web.json_response({
        'status': 'ok',
        'games_active': len(games),
        'player_waiting': waiting_player is not None
    })


async def index(request):
    """Simple index page."""
    return web.Response(
        text='Chess Multiplayer Server Running!',
        content_type='text/html'
    )


def create_app():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/health', health_check)
    app.router.add_get('/ws', websocket_handler)
    return app


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=port)
