
import secrets


class Deck:
    def __init__(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = [
            "2", "3", "4", "5", "6", "7", "8", "9", "10",
            "J", "Q", "K", "A"
        ]

        self.cards = [
            (rank, suit)
            for suit in suits
            for rank in ranks
        ]

    def fisher_yates_shuffle(self): ##personal preference for sorting
        """Shuffle the deck in place using Fisher-Yates."""
        rng = secrets.SystemRandom()

        for i in range(len(self.cards) - 1, 0, -1):
            j = rng.randrange(i + 1)

            self.cards[i], self.cards[j] = (
                self.cards[j],
                self.cards[i]
            )

    def draw_card(self):
        """Remove and return the top card of the deck."""
        if not self.cards:
            raise ValueError("The deck is empty.")

        return self.cards.pop()

    def remaining_cards(self):
        return len(self.cards)
