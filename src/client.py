
import argparse
import socket
import sys

from protocol import send_message, receive_message


def parse_arguments():
    parser = argparse.ArgumentParser(description="Blackjack Game Client")
    parser.add_argument("-i", "--ip", required=True,
                        help="Server DNS hostname or IP address")
    parser.add_argument("-p", "--port", type=int, required=True,
                        help="Server port number")
    parser.add_argument("-n", "--name", default="Player",
                    help="Player name")
    return parser.parse_args()



def display_game_update(update, my_player_number):
    print("\n========== BLACKJACK ==========")

    for player in update["players"]:
        print(f"\n{player['name']} (Player {player['player_number']}):")

        for rank, suit in player["hand"]:
            print(f"  {rank} of {suit}")

        print(f"Score: {player['score']}")

        if player["bust"]:
            print("BUST!")

    print("\nDealer's hand:")

    for rank, suit in update["dealer_hand"]:
        print(f"  {rank} of {suit}")

    if update["state"] == "GAME_OVER":
        print(f"Dealer score: {update['dealer_score']}")

        print("\n========== RESULTS ==========")

        for result in update["result"]:
            print(f"{result['player']}: {result['result']}")

        print("=============================")

    elif update["current_player"] == my_player_number:
        print("\n[CLIENT] It is your turn!")

    else:
        current_player = update["current_player"]
        print(f"\n[CLIENT] Waiting for Player {current_player}...")

    print("===============================")



def connect_to_server(hostname, port, player_name):
    try:
        server_ip = socket.gethostbyname(hostname)

    except socket.gaierror:
        print(f"[ERROR] Unable to resolve DNS hostname '{hostname}'.")
        print("Please check your Cisco router DNS configuration "
              "('ip dns server' / 'ip host') or verify domain spelling.")
        sys.exit(1)

    print(f"[CLIENT] Resolved {hostname} to {server_ip}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, port))
            print(f"[CLIENT] Connected to {server_ip}:{port}")

            send_message(client_socket, {
                "type": "CONNECT",
                "player_name": player_name
            })

            print(f"[CLIENT] Sent CONNECT as {player_name}")

            response = receive_message(client_socket)

            if response.get("type") == "ERROR":
                print(f"[ERROR] {response.get('message')}")
                return

            print(
                f"[CLIENT] Registered as Player "
                f"{response.get('player_number')}"
            )
            print(f"[CLIENT] {response.get('message')}")

            response = receive_message(client_socket)

            if response.get("type") == "GAME_START":
                print("\n========== BLACKJACK ==========")
                print(f"[CLIENT] Players: {response.get('players')}")
                print(f"[CLIENT] You are Player {response.get('player_number')}")
                print(f"[CLIENT] Game state: {response.get('state')}")

                print("\nYour hand:")

                for rank, suit in response.get("hand", []):
                    print(f"  {rank} of {suit}")

                print(f"Your score: {response.get('score')}")

                rank, suit = response.get("dealer_upcard")
                print(f"\nDealer is showing: {rank} of {suit}")

                print("===============================")

            else:
                print(f"[ERROR] Unexpected server response: {response}")
                return

            
            my_player_number = response.get("player_number")

            while True:
                message = receive_message(client_socket)

                if message.get("type") == "STATE_UPDATE":
                    display_game_update(message, my_player_number)

                    if message.get("state") == "GAME_OVER":
                        break

                    if message.get("current_player") == my_player_number:
                        while True:
                            action = input(
                                "\nChoose HIT or STAND: "
                            ).strip().upper()

                            if action in ("HIT", "STAND"):
                                break

                            print("Invalid choice. Enter HIT or STAND.")

                        send_message(client_socket, {
                            "type": "MOVE",
                            "action": action
                        })

                elif message.get("type") == "ERROR":
                    print(f"[ERROR] {message.get('message')}")

                else:
                    print(f"[CLIENT] Unexpected message: {message}")
                    break

            print("\n[CLIENT] Game over. Disconnecting...")

            send_message(client_socket, {"type": "DISCONNECT"})
            response = receive_message(client_socket)
            print(f"[CLIENT] Received: {response}")


    except OSError as error:
        print(f"[ERROR] Unable to connect to server: {error}")
        sys.exit(1)

    except (ConnectionError, ValueError) as error:
        print(f"[ERROR] Communication failed: {error}")
        sys.exit(1)




def main():
    args = parse_arguments()
    print("[CLIENT] Blackjack Client Started")
    connect_to_server(args.ip, args.port, args.name)

if __name__ == "__main__":
    main()