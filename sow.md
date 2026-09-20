# CS 457 Project Statement of Work (SOW) & Protocol Specification Template

**Student Name:** Dacovney Brochu 
**Date:** [2026-09-20]  
**Course:** CS 457 - Computer Networks  
**Target Server Domain:** `server.brochu.edu`  

---

## 1. Game Selection & Scope (Sprint 0)

> Planning is going to be an iterative process through the sprints so you don't have to have all the details now. Focus on big overview concepts. You will be updating the SOW as we plan.
> You have a lot of freedom to choose a game. There are a couple caveats.  

> - It must run in the console. The lab nodes won't be able to handle extensive graphics.
> - It has to be self-contained. You can use a internet-connector to download you code, but because the architecture must run 5 nodes you won't be able to run 
> - You are encouraged to use python, but I'm not going to make it a strict requirement. The instructor and TA's ability to help with C or Rust, etc will be diminished in other languages.

### 1.1 Game Overview
- **Chosen Game:** Blackjack
- **Player Capacity:** 2 Players (Simulated via 2 CML Client nodes)
- **Game Summary:** The game will use a two-player, console-based version of Blackjack, with both players going against a dealer for a server. Each round, the server will deal cards to itself and players, and the players must decide to hit or stand. The server will keep track of the main deck, player hands, the dealer's hand, the order of turns, and the score. After player turns, preset rules will be followed for determining the result of the round.

### 1.2 Core Game Rules & Win/Draw Conditions
- **Turn Mechanics:** The server will assign a Player 1 and Player 2. Each round, the server will deal two cards for each player and then two for itself. The player's turn will have them choose to Hit or Stand. If they exceed 21, it's a bust and they lose. Once both players have finished their turn, the server takes the Dealer's turn.
- **Victory Condition:** A player wins the round if their hand is closer to 21 than the dealer's hand without exceeding 21, or if the dealer busts and the player hasn't. The ultimate win condition stands if the player gets 21 with its original two cards equaling 21.
- **Draw/Tie Condition:** There is a chance of a draw if the player's final hand is the same as the dealer even if they both have Blackjack. A Bust does not have a chance of a draw anymore. A draw ends the round without any money gained or lost.

---

## 2. Application-Layer Messaging Protocol Blueprint (Sprint 1 Deliverable)

### 2.1 Message Transport & Serialization Format
- **Transport Protocol:** TCP
- **Serialization Format:** [JSON / Fixed-Header Binary / Delimited Text]
- **Framing Mechanism:** [e.g., Newline-delimited (`\n`) JSON payloads OR 4-byte big-endian length prefix]

### 2.2 Message Schema Definitions

#### Message Types:
1. `CONNECT` (Client -> Server): Request to join the game room.
2. `LOBBY_WAIT` (Server -> Client): Notification that server is waiting for Player 2.
3. `GAME_START` (Server -> Clients): Game initiated, assigns roles (e.g. Player X vs Player O).
4. `MOVE` (Client -> Server): Player action (e.g., cell coordinates or answer choice).
5. `STATE_UPDATE` (Server -> Clients): Broadcast current game board / state and active player turn.
6. `GAME_OVER` (Server -> Clients): Victory / Draw notification with final scores.
7. `ERROR` (Server -> Client): Invalid move or malformed packet error.

#### Example JSON Protocol Schema:
```json
{
  "msg_type": "MOVE",
  "player_id": "Player_1",
  "payload": {
    "action": "HIT"
  },
  "timestamp": 1727000000
}
```

---

### 2.3 Game State Machine (FSM) Design (Sprint 1 Deliverable)
- **State Transitions:** Detail state flow: `INIT` -> `WAITING_FOR_PLAYERS` -> `DEALING` -> `PLAYER_1_TURN` -> `PLAYER_2_TURN` -> `DEALER_TURN` -> `EVALUATE RESULTS` -> `GAME_OVER` -> `CLEANUP`.

---

## 3. Game Behavior & Server Concurrency Architecture (Sprint 2 Deliverable)

### 3.1 Server Concurrency Strategy
- **Architecture Choice:** Multi-Threading (`threading.Thread`)
- **Synchronization Logic:** The server will use a separate thread for communication with each client. The shared game state, which has the deck, player hands, scores, and current turn, will be protected with threading.Lock to keep clients from modifying the game incorrectly through simultaneous actions.

### 3.2 State & Score Synchronization Across Clients
- **Turn Enforcement:** The server will maintain the player IDs and only ensure MOVE messages are coming from the active player, while out-of-turn actions get an ERROR message.
- **Score & Board Synchronization:** The server will maintain an authoritative game state and send STATE_UPDATE messages to clients whenever a player's actions change the state. Each round will end with the server sending the final hands, results, and updated score to both clients.

---

## 4. Coding & AI Implementation Plan (Sprint 3)

- **Permitted AI Tools:** [e.g., GitHub Copilot, ChatGPT, Claude]
- **AI Prompting & Constraint Strategy:** Explain how you will constrain AI models to generate code (in Python or your chosen language) that adheres strictly to the protocol blueprint and FSM designed in Sprints 1 & 2.
- **Implementation Risk Management:** Detail your plan to leverage past programming experience and manage time to ensure code completion on schedule.

---

## 5. CML Multi-Subnet Topology & Wireshark Deployment Plan (Sprint 4 & 5 Deliverable)

> For now you can use the topology below. We may update this when we get to defining subnets.

### 5.1 Subnet & Router Design
- **Subnet A (Client 1):** `192.168.10.0/24` (Interface `Gi0/1` on Router R1)
- **Subnet B (Client 2):** `192.168.11.0/24` (Interface `Gi0/2` on Router R1)
- **Subnet C (Game Server):** `192.168.20.0/24` (Interface `Gi0/1` on Router R2)
- **Router Backbone:** `10.0.0.0/30` (Interface `Gi0/0` on R1 <-> `Gi0/0` on R2)

### 5.2 DHCP Pools & DNS Configuration Plan
- **Router R1 DHCP Pool 1 (`CLIENT1_POOL`):** Leases `192.168.10.10` - `192.168.10.50`, gateway `192.168.10.1`, DNS `10.0.0.2`.
- **Router R1 DHCP Pool 2 (`CLIENT2_POOL`):** Leases `192.168.11.10` - `192.168.11.50`, gateway `192.168.11.1`, DNS `10.0.0.2`.
- **Router R2 Authoritative DNS:** Configured with `ip dns server` and static host mapping `server.[yourlastname].edu` -> `192.168.20.100`.

### 5.3 Deployment Strategy & Wireshark Trace Capture
- **CML Deployment Strategy:** Deploy `server.py` onto Subnet C node (`192.168.20.100`) behind Router R2, and `client.py` onto Subnet A and Subnet B nodes behind Router R1.
- **Cisco Infrastructure Configuration:** Router R1 DHCP pools (`CLIENT1_POOL`, `CLIENT2_POOL`) and Router R2 authoritative DNS (`ip host server.[lastname].edu 192.168.20.100`).
- **Wireshark Trace Capture Plan:** Capture DHCP DORA exchange (`dhcp_negotiation.pcap`) and DNS query/response resolution (`dns_lookup.pcap`).
