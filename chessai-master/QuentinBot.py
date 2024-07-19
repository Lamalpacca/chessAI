import tkinter as tk
from tkinter import messagebox
import chess
import chess.svg
from PIL import Image, ImageTk
import io
from wand.image import Image as WandImage
import random

class QuentinBot:
    def __init__(self):
        pass

    # First AI implemented
    def Quentin_AI_move(self):
        aimove = self.depth3_search(self.board)
        return self.board.parse_san(aimove)

    def depth3_search(self, board):
        player = board.turn*2-1
        player_turn = [player*1, player*-1, player*1, player*-1] # Which players turn it is
        depth1_search = []
        depth2_search = []
        depth3_search = []
        current_move_eval = []
        all_moves = []

        for move1 in list(board.legal_moves):
            current_move_eval.append(board.san(move1))
            board.push(move1) # Make the move
            if board.is_game_over(claim_draw=True): # Check if the move meant the game was finished
                outcome = self.game_outcome(board)
                mate_moves = current_move_eval[:]
                mate_moves.extend(['','',outcome*999])
                depth1_search.append(mate_moves)
                mate_moves = []

            else:
                for move2 in list(board.legal_moves):
                    current_move_eval.append(board.san(move2)) # Save which move we are looking at
                    board.push(move2) # Make the move
                    if board.is_game_over(claim_draw=True): # Check if the move meant the game was finished
                        outcome = self.game_outcome(board)
                        mate_moves = current_move_eval[:]
                        mate_moves.extend(['',outcome*999])
                        depth2_search.append(mate_moves)
                        mate_moves = []

                    else: # If the move wasn't an ending one, check for the best next move
                        for move3 in list(board.legal_moves):
                            current_move_eval.append(board.san(move3)) # Save which move we are looking at
                            board.push(move3) # Make the move
                            
                            current_move_eval.append(self.evaluate_board(board)) # Save the evaluation since we are at a leaf node
                            depth3_search.append(current_move_eval[:]) # Track all the moves we looked at in this depth
                            all_moves.append(current_move_eval[:])
                            
                            board.pop() # Undo the last move
                            del current_move_eval[-2:] # Remove the last move and eval

                        best_move3 = max(depth3_search, key=lambda x: player_turn[2]*x[3])
                        depth2_search.append(best_move3)

                    depth3_search = []
                    board.pop()
                    current_move_eval.pop()

                best_move2 = max(depth2_search, key=lambda x: player_turn[1]*x[3])
                depth1_search.append(best_move2)

            depth2_search = []
            board.pop()
            current_move_eval.pop()

        best_move = max(depth1_search, key=lambda x: player_turn[0]*x[3])
        print(best_move)

        return best_move[0]
    
    def board_value(self, board):
        white_value, black_value = 0, 0
        for piece in self.pieces:
            white_value += self.piece_value[piece]*len(board.pieces(piece,True))
            black_value += self.piece_value[piece]*len(board.pieces(piece,False))

        return round(white_value+black_value,2), white_value, black_value
    
    def number_of_piece_type_at_squares(self, board, piece_type, squares, color):
        return len([x for x in board.pieces(piece_type,color) if x in squares])
    
    def evaluate_board(self, board):
        total_value, white_value, black_value = self.board_value(board) # First get the board piece values for white and black
        eval = white_value - black_value # The eval is positive if white is winning, negative if black is winning

        # Kings should be hidden behind pawns in early and middle game
        if total_value > 40:
            if board.king(1) in [0,1,2]:
                eval += 0.5 + 0.25 * len([x for x in board.pieces(1,1) if x in [0,1,2]])
            if board.king(1) in [6,7]:
                eval += 0.5 + 0.25 * len([x for x in board.pieces(1,1) if x in [5,6,7]])

            if board.king(0) in [56,57,58]:
                eval += -0.5 - 0.25 * len([x for x in board.pieces(1,0) if x in [48,49,50]])
            if board.king(0) in [62,63]:
                eval += -0.5 - 0.25 * len([x for x in board.pieces(1,1) if x in [53,54,55]])

            # Control of the center in early-middle game - but not rooks or queen
            four_central_squares = [27, 28, 35, 36]
            sixteen_central_squares = [18,19,20,21,26,29,34,37,42,43,44,45]
            for piece_type in [1,2,3]:
                for color in [0,1]: # 0 is black, 1 is white
                    eval += (color*2-1) * (0.5 * self.number_of_piece_type_at_squares(board, piece_type, four_central_squares, color))
                    eval += (color*2-1) * (0.25 * self.number_of_piece_type_at_squares(board, piece_type, sixteen_central_squares, color))

        if total_value >= 60:
            pass # Early game
        if total_value <= 40:
            pass # Late game
        else:
            pass # Mid game

        return eval
    
    def game_outcome(self, board):
        # If it's black's turn (white won) return 1, if it's white turn return -1
        if board.is_checkmate():
            outcome = (board.turn*-2)+1
        # If it's a draw return 0
        elif board.can_claim_draw() or board.is_stalemate() or board.is_insufficient_material():
            outcome = 0
        return outcome
    
    def resolve_game_over(self):
        if self.board.is_checkmate():
            if self.board.turn: 
                self.outcome = -1
                messagebox.showinfo("End of game","Checkmate! You lost to an AI, LOSER!")
            else:
                self.outcome = 1
                messagebox.showinfo("End of game","Checkmate! White wins")
        
        elif self.board.can_claim_draw() or self.board.is_stalemate() or self.board.is_insufficient_material():
            self.outcome = 0
            messagebox.showinfo("End of game","It's a draw!")
        