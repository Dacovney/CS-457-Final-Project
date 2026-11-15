import argparse
import socket
import threading

from deck import Deck
from hand import Hand
from fsm import GameStateMachine
from protocol import send_message, receive_message



class GameLobby:
    def __init__(self):
        # Each client runs in its own thread, so shared game state
        # must be protected against simultaneous modifications.
        self.lock = threading.Lock()
        self.game_started = threading.Event()
        self.ready_players = 0
        self.game_ready = threading.Event()
        self.players = []
        self.fsm = GameStateMachine()
        self.deck = None
        self.dealer_hand = Hand()
        # Prevent concurrent threads from writing to the same
        # client socket at the same time.
        self.send_lock = threading.Lock()

    def register_player(self, name, address, connection):
        with self.lock:
            if len(self.players) >= 2:
                return None

            player_number = len(self.players) + 1

            player = {
                "name": name,
                "player_number": player_number,
                "address": address,
                "hand": Hand(),
                "connection": connection
            }

            self.players.append(player)

            print(
                f"[SERVER] Registered {name} as Player {player_number}"
            )

            if len(self.players) == 2:
                self.fsm.transition_to("STARTING_GAME")
                self.start_game()
                self.fsm.transition_to("PLAYER_1_TURN")
                self.game_started.set()

            return player_number

    def start_game(self):
        """Create and shuffle the deck, then deal the opening hands."""
        self.deck = Deck()
        self.deck.fisher_yates_shuffle()

        for _ in range(2):
            for player in self.players:
                player["hand"].add_card(self.deck.draw_card())

            self.dealer_hand.add_card(self.deck.draw_card())

        print("[SERVER] Initial hands dealt")

        for player in self.players:
            print(
                f"[SERVER] {player['name']}: "
                f"{player['hand'].cards} "
                f"(Score: {player['hand'].calculate_score()})"
            )

        print(
            f"[SERVER] Dealer showing: "
            f"{self.dealer_hand.cards[0]}"
        )

    def get_game_start_message(self, player_number):
        with self.lock:
            player = self.players[player_number - 1]

            return {
                "type": "GAME_START",
                "player_number": player_number,
                "players": [p["name"] for p in self.players],
                "state": self.fsm.state,
                "hand": player["hand"].cards,
                "score": player["hand"].calculate_score(),
                "dealer_upcard": self.dealer_hand.cards[0]
            }

    def mark_player_ready(self):
        """Track when each player has received GAME_START."""
        with self.lock:
            self.ready_players += 1

            if self.ready_players == 2:
                self.game_ready.set()

    def get_player_names(self):
        with self.lock:
            return [player["name"] for player in self.players]
        

    
    def process_action(self, player_number, action):
        """Validate and process a player's HIT or STAND action."""
        with self.lock:
            expected_player = {
                "PLAYER_1_TURN": 1,
                "PLAYER_2_TURN": 2
            }.get(self.fsm.state)

            if expected_player != player_number:
                return {
                    "type": "ERROR",
                    "message": "It is not your turn."
                }

            if action == "HIT":
                player = self.players[player_number - 1]
                player["hand"].add_card(self.deck.draw_card())

                score = player["hand"].calculate_score()
                print(
                    f"[SERVER] {player['name']} hits. "
                    f"New hand: {player['hand'].cards} "
                    f"(Score: {score})"
                )

                if score > 21:
                    print(f"[SERVER] {player['name']} busts!")
                    self.advance_turn()

            elif action == "STAND":
                print(
                    f"[SERVER] {self.players[player_number - 1]['name']} "
                    f"stands."
                )
                self.advance_turn()

            else:
                return {
                    "type": "ERROR",
                    "message": "Invalid action. Choose HIT or STAND."
                }

            return self.get_game_update()

    def advance_turn(self):
        """Advance the FSM to the next player's turn or dealer."""
        if self.fsm.state == "PLAYER_1_TURN":
            self.fsm.transition_to("PLAYER_2_TURN")

        elif self.fsm.state == "PLAYER_2_TURN":
            self.fsm.transition_to("DEALER_TURN")
            self.play_dealer_turn()

            self.fsm.transition_to("ROUND_COMPLETE")
            self.fsm.transition_to("GAME_OVER")

    def play_dealer_turn(self):
        """Dealer draws until reaching at least 17."""
        print("[SERVER] Dealer's turn begins.")

        while self.dealer_hand.calculate_score() < 17:
            card = self.deck.draw_card()
            self.dealer_hand.add_card(card)

            print(
                f"[SERVER] Dealer draws {card}. "
                f"Score: {self.dealer_hand.calculate_score()}"
            )

        print(
            f"[SERVER] Dealer stands at "
            f"{self.dealer_hand.calculate_score()}."
        )

    def get_game_update(self):
        """Build a game update for both connected players."""
        game_over = self.fsm.state == "GAME_OVER"

        if self.fsm.state == "PLAYER_1_TURN":
            current_player = 1
        elif self.fsm.state == "PLAYER_2_TURN":
            current_player = 2
        else:
            current_player = None

        players = []

        for player in self.players:
            hand = player["hand"]

            players.append({
                "name": player["name"],
                "player_number": player["player_number"],
                "hand": hand.cards,
                "score": hand.calculate_score(),
                "bust": hand.is_bust()
            })

        # Keep the dealer's second card hidden until the round ends.    
        dealer_cards = (
            self.dealer_hand.cards
            if game_over
            else self.dealer_hand.cards[:1]
        )

        update = {
            "type": "STATE_UPDATE",
            "state": self.fsm.state,
            "current_player": current_player,
            "players": players,
            "dealer_hand": dealer_cards
        }

        if game_over:
            update["dealer_score"] = self.dealer_hand.calculate_score()
            update["result"] = self.get_game_result()

        return update

    def get_game_result(self):
        """Determine the round winner."""
        dealer_score = self.dealer_hand.calculate_score()
        dealer_bust = self.dealer_hand.is_bust()

        results = []

        for player in self.players:
            score = player["hand"].calculate_score()

            if player["hand"].is_bust():
                result = "LOSE"
            elif dealer_bust or score > dealer_score:
                result = "WIN"
            elif score < dealer_score:
                result = "LOSE"
            else:
                result = "PUSH"

            results.append({
                "player": player["name"],
                "result": result
            })

        return results



def parse_arguments():
    parser = argparse.ArgumentParser(description="Blackjack Game Server")
    parser.add_argument("-p", "--port", type=int, required=True,
                        help="Port number for the server to listen on")
    return parser.parse_args()


def handle_client(connection, address, lobby):
    print(f"[SERVER] Connection received from {address}")

    try:
        message = receive_message(connection)

        if message.get("type") != "CONNECT":
            send_message(connection, {
                "type": "ERROR",
                "message": "Expected CONNECT message"
            })
            return

        player_name = message.get("player_name", "Player")

        player_number = lobby.register_player(player_name, address, connection)

        if player_number is None:
            send_message(connection, {
                "type": "ERROR",
                "message": "The game already has two players."
            })
            print(f"[SERVER] Rejected extra connection from {address}")
            return

        send_message(connection, {
            "type": "WAITING_FOR_PLAYERS",
            "player_number": player_number,
            "message": "Waiting for another player..."
        })

        print(f"[SERVER] {player_name} is waiting for another player")

        # Player 1 waits here until Player 2 joins and the initial
        # game state has been created.
        lobby.game_started.wait()

        game_start_message = lobby.get_game_start_message(player_number)
        send_message(connection, game_start_message)

        print(f"[SERVER] Sent GAME_START to Player {player_number}")
        
        lobby.mark_player_ready()
        lobby.game_ready.wait()

        if player_number == 1:
            initial_update = lobby.get_game_update()

            with lobby.send_lock:
                for player in lobby.players:
                    send_message(
                        player["connection"],
                        initial_update
                    )


        
        while True:
            message = receive_message(connection)

            if message.get("type") == "DISCONNECT":
                send_message(connection, {"type": "DISCONNECT_ACK"})
                print(f"[SERVER] Player {player_number} disconnected")
                break

            elif message.get("type") == "MOVE":
                action = message.get("action", "").upper()

                response = lobby.process_action(
                    player_number, action
                )

                if response.get("type") == "ERROR":
                    send_message(connection, response)
                else:
                    # Send the updated game state to both players.
                    with lobby.send_lock:
                        for player in lobby.players:
                            send_message(
                                player["connection"],
                                response
                            )

            else:
                send_message(connection, {
                    "type": "ERROR",
                    "message": "Unexpected message"
                })


    except (ConnectionError, ValueError, OSError) as error:
        print(f"[SERVER] Connection error with {address}: {error}")

    finally:
        connection.close()


def start_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(5)

    lobby = GameLobby()

    print(f"[SERVER] Listening on 0.0.0.0:{port}")
    print("[SERVER] Waiting for players...")

    try:
        while True:
            connection, address = server_socket.accept()

            client_thread = threading.Thread(
                target=handle_client,
                args=(connection, address, lobby),
                daemon=True
            )
            client_thread.start()

    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")

    finally:
        server_socket.close()


def main():
    args = parse_arguments()
    start_server(args.port)


if __name__ == "__main__":
    main()
