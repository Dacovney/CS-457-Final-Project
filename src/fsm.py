 
class GameStateMachine:
    """Manage valid state transitions for a Blackjack round."""

    TRANSITIONS = {
        "WAITING_FOR_PLAYERS": ["STARTING_GAME"],
        "STARTING_GAME": ["PLAYER_1_TURN"],
        "PLAYER_1_TURN": ["PLAYER_2_TURN"],
        "PLAYER_2_TURN": ["DEALER_TURN"],
        "DEALER_TURN": ["ROUND_COMPLETE"],
        "ROUND_COMPLETE": ["GAME_OVER"],
        "GAME_OVER": []
    }

    def __init__(self):
        self.state = "WAITING_FOR_PLAYERS"

    def transition_to(self, new_state):
        """Move to a new state if the transition is valid."""
        allowed_states = self.TRANSITIONS[self.state]

        if new_state not in allowed_states:
            raise ValueError(
                f"Invalid transition: {self.state} -> {new_state}"
            )

        old_state = self.state
        self.state = new_state

        print(f"[FSM] {old_state} -> {new_state}")
