"""
Network client for multiplayer chess.
Handles connection to the server and communication.
"""

import asyncio
import json
import threading
import queue

# Server URL - Update this with your Railway deployment URL
SERVER_URL = "wss://chess-production-dc4e.up.railway.app/ws"

# Try to import websockets (will need to be installed)
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class NetworkClient:
    """Client for connecting to the multiplayer server."""
    
    def __init__(self, server_url=None):
        self.server_url = server_url or SERVER_URL
        self.ws = None
        self.connected = False
        self.game_id = None
        self.player_color = None
        self.opponent_name = None
        
        # Message queues for thread-safe communication
        self.incoming_queue = queue.Queue()
        self.outgoing_queue = queue.Queue()
        
        # Callbacks
        self.on_match_found = None
        self.on_opponent_move = None
        self.on_opponent_disconnect = None
        self.on_opponent_resign = None
        self.on_waiting = None
        self.on_error = None
        self.on_rematch_requested = None
        self.on_rematch_start = None
        
        self._running = False
        self._thread = None
    
    def start(self):
        """Start the network client in a background thread."""
        if not WEBSOCKETS_AVAILABLE:
            if self.on_error:
                self.on_error("websockets module not installed")
            return False
        
        self._running = True
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()
        return True
    
    def stop(self):
        """Stop the network client."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
    
    def _run_async_loop(self):
        """Run the async event loop in background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
        finally:
            loop.close()
    
    async def _connect_and_listen(self):
        """Connect to server and listen for messages."""
        try:
            async with websockets.connect(self.server_url) as ws:
                self.ws = ws
                self.connected = True
                
                # Send find_match request
                await ws.send(json.dumps({
                    'action': 'find_match',
                    'name': 'Player'
                }))
                
                while self._running:
                    try:
                        # Check for outgoing messages
                        while not self.outgoing_queue.empty():
                            msg = self.outgoing_queue.get_nowait()
                            await ws.send(json.dumps(msg))
                        
                        # Wait for incoming message with timeout
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=0.1)
                            data = json.loads(message)
                            self._handle_message(data)
                        except asyncio.TimeoutError:
                            pass
                        
                    except websockets.exceptions.ConnectionClosed:
                        break
                        
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
        finally:
            self.connected = False
    
    def _handle_message(self, data):
        """Handle incoming server message."""
        msg_type = data.get('type')
        
        if msg_type == 'waiting':
            if self.on_waiting:
                self.on_waiting()
        
        elif msg_type == 'game_start':
            self.game_id = data.get('game_id')
            self.player_color = data.get('color')
            self.opponent_name = data.get('opponent')
            if self.on_match_found:
                self.on_match_found(self.player_color, self.opponent_name)
        
        elif msg_type == 'opponent_move':
            move = data.get('move')
            if self.on_opponent_move:
                self.on_opponent_move(move)
        
        elif msg_type == 'opponent_disconnected':
            if self.on_opponent_disconnect:
                self.on_opponent_disconnect()
        
        elif msg_type == 'opponent_resigned':
            if self.on_opponent_resign:
                self.on_opponent_resign()
        
        elif msg_type == 'rematch_requested':
            if self.on_rematch_requested:
                self.on_rematch_requested()
        
        elif msg_type == 'rematch_start':
            self.game_id = data.get('game_id')
            self.player_color = data.get('color')
            if self.on_rematch_start:
                self.on_rematch_start(self.player_color)
    
    def send_move(self, from_row, from_col, to_row, to_col):
        """Send a move to the server."""
        self.outgoing_queue.put({
            'action': 'move',
            'game_id': self.game_id,
            'move': [from_row, from_col, to_row, to_col]
        })
    
    def resign(self):
        """Resign from the current game."""
        self.outgoing_queue.put({
            'action': 'resign',
            'game_id': self.game_id
        })
    
    def find_new_match(self):
        """Request a new match after game ends."""
        self.game_id = None
        self.player_color = None
        self.outgoing_queue.put({
            'action': 'find_match',
            'name': 'Player'
        })
    
    def request_rematch(self):
        """Request a rematch with the current opponent."""
        self.outgoing_queue.put({
            'action': 'rematch_request',
            'game_id': self.game_id
        })
