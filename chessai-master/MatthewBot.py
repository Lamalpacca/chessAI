import random

class MatthewBot:
    def __init__(self): 
        pass

    def Matthew_AI_move(self):
        """Make a random move"""
        return random.choice(list(self.board.legal_moves))
