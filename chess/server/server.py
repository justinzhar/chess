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


async def websocket_handler(request):
    """Handle WebSocket connections for multiplayer."""
    global waiting_player, waiting_player_info
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    player_game_id = None
    player_color = None
    
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
                        
                        player_game_id = game_id
                        player_color = 'black'
                        
                        # Clear waiting player
                        waiting_player = None
                        waiting_player_info = None
                
                elif action == 'move':
                    # Player made a move
                    game_id = data.get('game_id')
                    if game_id in games:
                        game = games[game_id]
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
                    if game_id in games:
                        game = games[game_id]
                        opponent_color = 'black' if player_color == 'white' else 'white'
                        opponent_ws = game['players'].get(opponent_color)
                        if opponent_ws and not opponent_ws.closed:
                            await opponent_ws.send_json({
                                'type': 'opponent_resigned'
                            })
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
        
        if player_game_id and player_game_id in games:
            game = games[player_game_id]
            opponent_color = 'black' if player_color == 'white' else 'white'
            opponent_ws = game['players'].get(opponent_color)
            if opponent_ws and not opponent_ws.closed:
                await opponent_ws.send_json({
                    'type': 'opponent_disconnected'
                })
            del games[player_game_id]
    
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
