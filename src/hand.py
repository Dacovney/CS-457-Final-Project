
class Hand:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def calculate_score(self):
        score = 0
        ace_count = 0

        for rank, suit in self.cards:
            if rank == "A":
                score += 11
                ace_count += 1
            elif rank in ("J", "Q", "K"):
                score += 10
            else:
                score += int(rank)

        # Reduce Aces from 11 to 1 until the hand is valid.
        while score > 21 and ace_count > 0:
            score -= 10
            ace_count -= 1

        return score

    def is_bust(self):
        return self.calculate_score() > 21

    def is_blackjack(self):
        return len(self.cards) == 2 and self.calculate_score() == 21

    def display(self):
        card_names = [
            f"{rank} of {suit}"
            for rank, suit in self.cards
        ]

        print(f"Cards: {', '.join(card_names)}")
        print(f"Score: {self.calculate_score()}")
