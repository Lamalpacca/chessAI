import chess
import chess.engine
import os
import asyncio


class QuentinBot2:
    def __init__(self):
        self.engine = chess.engine.SimpleEngine.popen_uci('/home/d-dhumeaq/Documents/Stockfish/src/stockfish')

    # First AI implemented
    def Quentin_AI_move2(self):
        result = self.engine.play(self.board, chess.engine.Limit(time=0.01))
        return result.move
    
