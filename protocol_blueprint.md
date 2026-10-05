# Protocol Blueprint

## Transport
**TCP** will be used for client-server communication. TCP will be more reliable for messages to remained delivered in order between client and server.

The server will listen for incoming client connections. Each connected client will maintain a TCP socket for communication with the server. The server will be responsible for validating all received messages and maintaining the authoritative game state.

Because TCP provides a continuous byte stream rather than individual messages, the protocol will use an explicit framing mechanism to determine where each message begins and ends.

## Serialization
**JSON** will be used to serialize application messages.

JSON was selected because it is human-readable, easy to generate and parse in Python, and allows different message types to contain different fields while maintaining a consistent structure.

Each message will contain a msg_type field identifying the purpose of the message. Additional fields will contain player information, game actions, and game state as appropriate.

Example:
```
{
    "msg_type": "MOVE",
    "player_id": "Player_1",
    "action": "HIT"
}
```

## Framing
The protocol will use **4-byte length-prefixed framing**.

Before sending a JSON message, the sender will encode the JSON object as UTF-8 and prepend a 4-byte unsigned integer containing the number of bytes in the message payload. The length value will use Network Byte Order (big-endian).

The resulting wire format is:
```
[4-byte payload length][JSON payload]
```
Example:
```
[00 00 00 NN][{"msg_type":"MOVE","player_id":"Player_1","action":"HIT"}]
```
The receiver will first read exactly 4 bytes to determine the payload length, then continue reading until the specified number of payload bytes has been received.

This ensures that the application can correctly handle TCP fragmentation and message coalescing. The assignment specifically requires your protocol to account for those TCP stream behaviors.

## Message Types
| Message Type | Direction | Purpose | Required Fields |
|---|---|---|---|
| CONNECT | Client → Server | Requests to join the game | `msg_type`, `player_id` |
| LOBBY_WAIT | Server → Client | Indicates that the player is waiting for an opponent | `msg_type`, `player_id` |
| GAME_START | Server → Client | Begins a new round and provides initial game information | `msg_type`, `player_id`, `bankroll`, `minimum_bet`, `hand` |
| PLACE_BET | Client → Server | Submits the player's bet for the round | `msg_type`, `player_id`, `amount` |
| MOVE | Client → Server | Sends a player action | `msg_type`, `player_id`, `action` |
| STATE_UPDATE | Server → Client | Sends updated game state | `msg_type`, `player_id`, `hand`, `bankroll`, `bet`, `active_player` |
| ERROR | Server → Client | Reports an invalid or malformed request | `msg_type`, `error_code`, `message` |
| DISCONNECT | Client → Server | Indicates intentional departure | `msg_type`, `player_id`, `reason` |
| GAME_OVER | Server → Client | Reports the final game result | `msg_type`, `winner`, `reason`, `final_bankroll` |


## Message Schema
| Field | Type | Required | Description |
|---|---|---|---|
| msg_type | String | Yes | Identifies the message type |
| player_id | String | Depends | Identifies the player sending or receiving the message |
| timestamp | Integer | Optional | Unix timestamp associated with the message |

- **CONNECT**
```
{
    "msg_type": "CONNECT",
    "player_id": "Player_1"
}
```

- **LOBBY_WAIT**
```
{
    "msg_type": "LOBBY_WAIT",
    "player_id": "Player_1"
}
```

- **GAME_START**
```
{
    "msg_type": "GAME_START",
    "player_id": "Player_1",
    "bankroll": 100,
    "minimum_bet": 10
}
```

- **PLACE_BET**
```
{
    "msg_type": "PLACE_BET",
    "player_id": "Player_1",
    "amount": 10
}
```

- **MOVE**
HIT
```
{
    "msg_type": "MOVE",
    "player_id": "Player_1",
    "action": "HIT"
}
```
STAND
```
{
    "msg_type": "MOVE",
    "player_id": "Player_1",
    "action": "STAND"
}
```

- **STATE_UPDATE**
```
{
    "msg_type": "STATE_UPDATE",
    "player_id": "Player_1",
    "hand": ["10H", "7C"],
    "bankroll": 90,
    "bet": 10,
    "active_player": "Player_1"
}
```

- **ERROR**
```
{
    "msg_type": "ERROR",
    "error_code": "OUT_OF_TURN",
    "message": "It is not your turn."
}
```

- **DISCONNECT**
```
{
    "msg_type": "DISCONNECT",
    "player_id": "Player_1",
    "reason": "QUIT"
}
```

- **GAME_OVER**
```
{
    "msg_type": "GAME_OVER",
    "winner": "Player_2",
    "reason": "BANKRUPTCY",
    "final_bankroll": 0
}
```

## Error Behavior
The server will validate every client message before modifying the game state.

Invalid messages will generate an **ERROR** response and will not cause a state transition.

Examples of invalid requests include:

 - MOVE received when it is not the player's turn.
 - Invalid action such as an action other than HIT or STAND.
 - Invalid player ID.
 - Malformed JSON.
 - Missing required fields.
 - Invalid bet amount.
 - A bet below the minimum.
 - Attempting to place a bet after the round has started.
 - Attempting to act after the player's turn has ended.

Example:
```
{
    "msg_type": "ERROR",
    "error_code": "OUT_OF_TURN",
    "message": "It is not your turn."
}
```

## Disconnect/Forfeit Behavior
The protocol supports both intentional and unexpected disconnections.

- **Intentional Disconnect**
Client sends:
```
{
    "msg_type": "DISCONNECT",
    "player_id": "Player_1",
    "reason": "QUIT"
}
```
The server will treat the disconnect as a forfeit, notify the remaining player, and transition to GAME_OVER.

- **Unexpected Disconnect**
If the client's TCP connection closes unexpectedly, the server will detect the disconnection through TCP EOF or a socket exception.

The server will then:
1. Mark the disconnected player as having forfeited.
2. Notify the remaining player.
3. Award the game to the remaining player.
4. Transition to GAME_OVER.
5. Close and clean up the disconnected client's socket.
