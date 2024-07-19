import random

class DanBot:
    def __init__(self):
        pass

    def Dan_AI_move(self):
        """Make a random move"""
        return random.choice(list(self.board.legal_moves))
