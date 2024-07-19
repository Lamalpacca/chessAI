import tkinter as tk
from tkinter import messagebox
import chess
import chess.svg
from PIL import Image, ImageTk
import io
from wand.image import Image as WandImage
import random
from TwoPlayerGame import TwoPlayerGame
import numpy as np
import json
from time import perf_counter
import cProfile
import pstats
# from operator import itemgetter


class SamBot():
    def __init__(self): 
        pass

    def read_config(self, filepath):
        """read config"""
        config = json.load(open(filepath))

        return config

    def endgame_base_val(self):
        """Calculates how far through the game you are on a scale of 0-24 with 
        low numbers being closer to the endgame"""

        endgame_points = sum([self.endgame_value[piece]*len(self.board.pieces(piece,False)) + self.endgame_value[piece]*len(self.board.pieces(piece,True)) for piece in self.endgame_pieces])

        return endgame_points

    def piece_square_val(self, endgame_val):
        """Calculate base board value by checking the value of each piece given its position"""
        value = 0
        for piece in self.sam_pieces:
            value += sum([self.piece_square_tables[f'white_early_{piece}'][position] for position in self.board.pieces(piece,True)])*endgame_val
            value += sum([self.piece_square_tables[f'black_early_{piece}'][position] for position in self.board.pieces(piece,False)])*endgame_val
            value += sum([self.piece_square_tables[f'white_end_{piece}'][position] for position in self.board.pieces(piece,True)])*(24-endgame_val)
            value += sum([self.piece_square_tables[f'black_end_{piece}'][position] for position in self.board.pieces(piece,False)])*(24-endgame_val)
        
        return value

    def evaluate_rule_points(self, white_pawn_attacks, black_pawn_attacks):
        """Calculate points due to the relation between pieces"""
        score = 0

        for piece in [1, 2, 3, 4, 5]:
            score += sum([240 for position in self.board.pieces(piece, True) if position in white_pawn_attacks])
            score += sum([240 for position in self.board.pieces(piece, False) if position in black_pawn_attacks])

        score += sum([480 for position in self.board.pieces(5, True) if {position in self.board.pieces(1, True)}.intersection(self.column_reference[position]) == set()])
        score += sum([-480 for position in self.board.pieces(5, False) if {position in self.board.pieces(1, False)}.intersection(self.column_reference[position]) == set()])
        
        return score

    def sam_evaluate_board(self, board_val):
        """Calculate the total board value"""
        endgame_val = self.endgame_base_val()
        board_val += self.piece_square_val(endgame_val)
        # board_val += self.evaluate_rule_points(endgame_val)

        return board_val

    def check_repetition(self, board_store, fen):
        """Check for threefold repetition"""
        result = False
        if board_store.count(fen) == 2:
            result = True
        
        return result

    def check_attacking_pieces(self, moves, last_move, square, piece, piece_colour, pawn_attacks):
        """Return list of pieces attacking a square"""
        attacking_pieces = {"White": [], "Black": []}

        # Check pawn attacks
        attacking_pieces["White"] = [1 for attack in pawn_attacks["White"] if attack==square]
        attacking_pieces["Black"] = [1 for attack in pawn_attacks["Black"] if attack==square]
        if piece == 1 and str(last_move)[0] != str(last_move)[2]:
            if piece_colour == True:
                del attacking_pieces["White"][-1]
            else:
                del attacking_pieces["Black"][-1]

        # Identify attacks for other pieces
        for move in moves:
            move_to = self.board_squares[str(move)[2:4]]
            if move_to == square and move != last_move:
                move_from = self.board_squares[str(move)[0:2]]
                piece = self.board.piece_type_at(move_from)
                if piece in {3, 4, 5}:
                    if piece_colour == True:
                        attacking_pieces["White"].append(piece)
                    else:
                        attacking_pieces["Black"].append(piece)
                elif piece == 2:
                    if piece_colour == True:
                        attacking_pieces["White"].append(3)
                    else:
                        attacking_pieces["Black"].append(3)

        # Check king attacks
        # Not including check to see if last move was a king move as if it was none of this matters
        white_king_square = self.board.king(True)
        black_king_square = self.board.king(False)
        if square in self.king_attack_grid[white_king_square]:
            attacking_pieces["White"].append(6)
        if square in self.king_attack_grid[black_king_square]:
            attacking_pieces["Black"].append(6)

        # Order attacks by piece cost
        attacking_pieces["White"].sort()
        attacking_pieces["Black"].sort()

        return attacking_pieces
    
    def check_capture_chain_white(self, attacking_pieces, piece_on_square, total_score):
        """Resolve chain of captures after piece is moved"""
        next_attack = attacking_pieces["White"].pop(0)
        white_len = len(attacking_pieces["White"])
        black_len = len(attacking_pieces["Black"])

        if black_len == 0:
            total_score += self.sam_piece_value[piece_on_square]
        elif next_attack <= piece_on_square:
            total_score += self.sam_piece_value[piece_on_square]
            total_score = self.check_capture_chain_black(attacking_pieces, next_attack, total_score)
        elif black_len > white_len:
            return total_score
        elif black_len == 1:
            if self.sam_piece_value[next_attack] + self.sam_piece_value[attacking_pieces["White"][0]] <= self.sam_piece_value[piece_on_square] + self.sam_piece_value[attacking_pieces["Black"][0]]:
                total_score -= self.sam_piece_value[piece_on_square]
        else:
            point_total = - self.sam_piece_value[next_attack] + self.sam_piece_value[piece_on_square]
            for n in range(0, white_len-1):
                if n < white_len:
                    point_total += - self.sam_piece_value[attacking_pieces["White"][n]] + self.sam_piece_value[attacking_pieces["Black"][n]]
                else:
                    point_total += self.sam_piece_value[attacking_pieces["Black"][n]]
                if point_total >= 0:
                    total_score += self.sam_piece_value[piece_on_square]
                    total_score = self.check_capture_chain_black(attacking_pieces, next_attack, total_score)
                    break

        return total_score


    def check_capture_chain_black(self, attacking_pieces, piece_on_square, total_score):
        """Resolve chain of captures after piece is moved"""
        next_attack = attacking_pieces["Black"].pop(0)
        white_len = len(attacking_pieces["White"])
        black_len = len(attacking_pieces["Black"])

        if white_len == 0:
            total_score -= self.sam_piece_value[piece_on_square]
        elif next_attack <= piece_on_square:
            total_score -= self.sam_piece_value[piece_on_square]
            total_score = self.check_capture_chain_white(attacking_pieces, next_attack, total_score)
        elif white_len > black_len:
            return total_score
        elif white_len == 1:
            if self.sam_piece_value[next_attack] + self.sam_piece_value[attacking_pieces["Black"][0]] <= self.sam_piece_value[piece_on_square] + self.sam_piece_value[attacking_pieces["White"][0]]:
                total_score -= self.sam_piece_value[piece_on_square]
        else:
            point_total = self.sam_piece_value[next_attack] - self.sam_piece_value[piece_on_square]
            for n in range(0, white_len-1):
                if n < white_len:
                    point_total += self.sam_piece_value[attacking_pieces["Black"][n]] - self.sam_piece_value[attacking_pieces["White"][n]]
                else:
                    point_total -= self.sam_piece_value[attacking_pieces["White"][n]]
                if point_total >= 0:
                    total_score -= self.sam_piece_value[piece_on_square]
                    total_score = self.check_capture_chain_white(attacking_pieces, next_attack, total_score)
                    break

        return total_score

    def order_moves_white(self):
        """Ranks candidate moves for white pieces"""
        moves = list(self.board.legal_moves)

        white_pawn_attacks = set()
        for pawn in self.board.pieces(1, True):
            white_pawn_attacks.update(self.pawn_attack_grid["White"][pawn])

        black_pawn_attacks = set()
        for pawn in self.board.pieces(1, False):
            black_pawn_attacks.update(self.pawn_attack_grid["Black"][pawn])

        # pawn_attack_count_white = {
        #     0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0,
        #     8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0,
        #     16:0, 17:0, 18:0, 19:0, 20:0, 21:0, 22:0, 23:0,
        #     24:0, 25:0, 26:0, 27:0, 28:0, 29:0, 30:0, 31:0,
        #     32:0, 33:0, 34:0, 35:0, 36:0, 37:0, 38:0, 39:0,
        #     40:0, 41:0, 42:0, 43:0, 44:0, 45:0, 46:0, 47:0,
        #     48:0, 49:0, 50:0, 51:0, 52:0, 53:0, 54:0, 55:0,
        #     56:0, 57:0, 58:0, 59:0, 60:0, 61:0, 62:0, 63:0
        # }
        # pawn_attack_count_black = {
        #     0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0,
        #     8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0,
        #     16:0, 17:0, 18:0, 19:0, 20:0, 21:0, 22:0, 23:0,
        #     24:0, 25:0, 26:0, 27:0, 28:0, 29:0, 30:0, 31:0,
        #     32:0, 33:0, 34:0, 35:0, 36:0, 37:0, 38:0, 39:0,
        #     40:0, 41:0, 42:0, 43:0, 44:0, 45:0, 46:0, 47:0,
        #     48:0, 49:0, 50:0, 51:0, 52:0, 53:0, 54:0, 55:0,
        #     56:0, 57:0, 58:0, 59:0, 60:0, 61:0, 62:0, 63:0
        # }

        # for pawn in self.board.pieces(1, True):
        #     for attack in self.pawn_attack_grid["White"][pawn]:
        #         pawn_attack_count_white[attack] += 1

        # for pawn in self.board.pieces(1, False):
        #     for attack in self.pawn_attack_grid["Black"][pawn]:
        #         pawn_attack_count_black[attack] += 1

        init_score = self.evaluate_rule_points(white_pawn_attacks, black_pawn_attacks)
            
        move_scores = []
        for move in moves:
            # score = 0
            move_to = self.board_squares[str(move)[2:4]]
            move_from = self.board_squares[str(move)[0:2]]
            piece = self.board.piece_type_at(move_from)
            piece_captured = self.board.piece_type_at(move_to)

            # if piece_captured is not None:
            #     score += 5*self.sam_piece_value[piece_captured] - self.sam_piece_value[piece]
            # if str(move)[-1] == "q":
            #     score += 800
            # elif move_to in pawn_attacks:
            #     score -= self.sam_piece_value[piece]

            # attacking_pieces = self.check_attacking_pieces(moves, move, move_to, piece, True, pawn_attacks)
            # if len(attacking_pieces["Black"]) != 0:
            #     score = self.check_capture_chain_black(attacking_pieces, piece, 0)
            # else:
            #     score = 0
            score = init_score

            if piece_captured is not None:
                score += 24*self.sam_piece_value[piece_captured]
            # if pawn_attack_count_black[move_to] > 0:
            #     score -= 24*self.sam_piece_value[piece]
            if move_to in black_pawn_attacks:
                score -= 24*self.sam_piece_value[piece]
            if str(move)[-1] == "q":
                score += 19200

            move_scores.append((move, score))

        # TODO: Check if your pieces/pawns defend the new space

        move_scores.sort(key = lambda x: x[1], reverse=True)
        top_score = move_scores[0][1]
        # score_list = sorted(move_scores, key=itemgetter(1), reverse=True)
        priority_moves = list(zip(*move_scores))[0]

        return priority_moves, top_score

    def order_moves_black(self):
        """Ranks candidate moves for black pieces"""
        moves = list(self.board.legal_moves)

        white_pawn_attacks = set()
        for pawn in self.board.pieces(1, True):
            white_pawn_attacks.update(self.pawn_attack_grid["White"][pawn])

        black_pawn_attacks = set()
        for pawn in self.board.pieces(1, False):
            black_pawn_attacks.update(self.pawn_attack_grid["Black"][pawn])
        
        # pawn_attack_count_white = {
        #     0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0,
        #     8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0,
        #     16:0, 17:0, 18:0, 19:0, 20:0, 21:0, 22:0, 23:0,
        #     24:0, 25:0, 26:0, 27:0, 28:0, 29:0, 30:0, 31:0,
        #     32:0, 33:0, 34:0, 35:0, 36:0, 37:0, 38:0, 39:0,
        #     40:0, 41:0, 42:0, 43:0, 44:0, 45:0, 46:0, 47:0,
        #     48:0, 49:0, 50:0, 51:0, 52:0, 53:0, 54:0, 55:0,
        #     56:0, 57:0, 58:0, 59:0, 60:0, 61:0, 62:0, 63:0
        # }
        # pawn_attack_count_black = {
        #     0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0,
        #     8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0,
        #     16:0, 17:0, 18:0, 19:0, 20:0, 21:0, 22:0, 23:0,
        #     24:0, 25:0, 26:0, 27:0, 28:0, 29:0, 30:0, 31:0,
        #     32:0, 33:0, 34:0, 35:0, 36:0, 37:0, 38:0, 39:0,
        #     40:0, 41:0, 42:0, 43:0, 44:0, 45:0, 46:0, 47:0,
        #     48:0, 49:0, 50:0, 51:0, 52:0, 53:0, 54:0, 55:0,
        #     56:0, 57:0, 58:0, 59:0, 60:0, 61:0, 62:0, 63:0
        # }

        # for pawn in self.board.pieces(1, True):
        #     for attack in self.pawn_attack_grid["White"][pawn]:
        #         pawn_attack_count_white[attack] += 1

        # for pawn in self.board.pieces(1, False):
        #     for attack in self.pawn_attack_grid["Black"][pawn]:
        #         pawn_attack_count_black[attack] += 1
        
        init_score = self.evaluate_rule_points(white_pawn_attacks, black_pawn_attacks)

        move_scores = []
        for move in moves:
            move_to = self.board_squares[str(move)[2:4]]
            move_from = self.board_squares[str(move)[0:2]]
            piece = self.board.piece_type_at(move_from)
            piece_captured = self.board.piece_type_at(move_to)

            # if piece_captured is not None:
            #     score += 5*self.sam_piece_value[piece_captured] - self.sam_piece_value[piece]
            # if str(move)[-1] == "q":
            #     score += 800
            # elif move_to in pawn_attacks:
            #     score -= self.sam_piece_value[piece]

            # attacking_pieces = self.check_attacking_pieces(moves, move, move_to, piece, False, pawn_attacks)
            # if len(attacking_pieces["White"]) != 0:
            #     score = self.check_capture_chain_white(attacking_pieces, piece, 0)
            # else:
            #     score = 0
            score = init_score

            if piece_captured is not None:
                score -= 24*self.sam_piece_value[piece_captured]
            # if pawn_attack_count_white[move_to] > 0:
            #     score += 24*self.sam_piece_value[piece]
            if move_to in white_pawn_attacks:
                score += 24*self.sam_piece_value[piece]
            if str(move)[-1] == "q":
                score -= 19200
            
            move_scores.append((move, score))

        move_scores.sort(key = lambda x: x[1])
        top_score = move_scores[0][1]
        priority_moves = list(zip(*move_scores))[0]
        # score_list = sorted(move_scores, key=itemgetter(1))
        # priority_moves = list(zip(*score_list))[0]
        
        return priority_moves, top_score

    def minimaxmax(self, depth, alpha, beta, board_store):
        """In depth call to minimax algorithm for white moves"""
        split_fen = self.board.fen().split(" ")
        repetition_fen = split_fen[0] + split_fen[1] + split_fen[3]
        fen = split_fen[0] + split_fen[1]
        if self.board.is_stalemate() or self.board.is_insufficient_material() or split_fen[4] == 50 or self.check_repetition(board_store, repetition_fen):
            return 0.0

        if self.board.is_check():
            depth += 1

        if depth==0:
            self.nodes_total += 1
            if fen not in self.fen_store:
                self.nodes_calculated += 1
                moves, base_eval = self.order_moves_white()
                score = self.sam_evaluate_board(base_eval)
                self.fen_store[fen] = score
            return self.fen_store[fen]
        
        moves, base_eval = self.order_moves_white()
        score = -5000000
        new_board_store = board_store.copy()
        new_board_store.append(repetition_fen)
        for move in moves:
            self.board.push(move)
            if self.board.is_checkmate():
                self.board.pop()
                return 5000000
            score = max(score, self.minimaxmin(depth-1, alpha, beta, new_board_store)) 
            self.board.pop()
            if score > beta:
                break
            alpha = max(alpha, score)

        return score


    def minimaxmin(self, depth, alpha, beta, board_store):
        """In depth call to minimax algorithm for black moves"""
        split_fen = self.board.fen().split(" ")
        repetition_fen = split_fen[0] + split_fen[1] + split_fen[3]
        fen = split_fen[0] + split_fen[1]
        if self.board.is_stalemate() or self.board.is_insufficient_material() or split_fen[4] == 50 or self.check_repetition(board_store, repetition_fen):
            return 0.0

        if self.board.is_check():
            depth += 1

        if depth==0:
            self.nodes_total += 1
            if fen not in self.fen_store:
                self.nodes_calculated += 1
                moves, base_eval = self.order_moves_black()
                score = self.sam_evaluate_board(base_eval)
                self.fen_store[fen] = score
            return self.fen_store[fen]
        
        moves, base_eval = self.order_moves_black()
        score = 5000000
        new_board_store = board_store.copy()
        new_board_store.append(repetition_fen)
        for move in moves:
            self.board.push(move)
            if self.board.is_checkmate():
                self.board.pop()
                return -5000000
            score = min(score, self.minimaxmax(depth-1, alpha, beta, new_board_store))
            self.board.pop()
            if score < alpha:
                break 
            beta = min(beta, score)

        return score

    def initminimaxmax(self, depth, alpha, beta, priority_moves):
        """Initial call to minimax algorithm for white moves"""
        if self.board.is_check():
            depth += 1

        score = -5000000
        best_move = priority_moves[0]
        board_store = self.board_store.copy()

        for move in priority_moves:
            self.board.push(move)
            move_score = self.minimaxmin(depth-1, alpha, beta, board_store)

            if move_score >= score:
                score = max(score, move_score) 
                best_move = move

            self.board.pop()
            alpha = max(alpha, score)

        return best_move

    def initminimaxmin(self, depth, alpha, beta, priority_moves):
        """Initial call to minimax algorithm for black moves"""
        if self.board.is_check():
            depth += 1

        score = 5000000
        best_move = priority_moves[0]
        board_store = self.board_store.copy()

        for move in priority_moves:
            self.board.push(move)
            move_score = self.minimaxmax(depth-1, alpha, beta, board_store)

            if move_score <= score:
                score = min(score, move_score)
                best_move = move

            self.board.pop()
            beta = min(beta, score)

        return best_move

    def firstminimaxmax(self):
        """Initial call to minimax algorithm for white moves"""
        moves = list(self.board.legal_moves)
        move_scores = []

        for move in moves:
            self.board.push(move)
            if self.board.is_checkmate():
                self.board.pop()
                return [move, 'checkmate']
            
            split_fen = self.board.fen().split(" ")
            repetition_fen = split_fen[0] + split_fen[1] + split_fen[3]
            fen = split_fen[0] + split_fen[1]

            if self.board.is_stalemate() or self.board.is_insufficient_material() or split_fen[4] == 50 or self.check_repetition(self.board_store, repetition_fen):
                move_score = 0.0
            elif fen not in self.fen_store:
                future_moves, base_eval = self.order_moves_black()
                move_score = self.sam_evaluate_board(base_eval)
                self.fen_store[fen] = move_score
            else:
                move_score = self.fen_store[fen]

            self.board.pop()

            move_scores.append((move, move_score))

        move_scores.sort(key = lambda x: x[1])
        priority_moves = list(zip(*move_scores))[0]

        return priority_moves

    def firstminimaxmin(self):
        """Initial call to minimax algorithm for black moves"""
        moves = list(self.board.legal_moves)
        move_scores = []

        for move in moves:
            self.board.push(move)
            if self.board.is_checkmate():
                self.board.pop()
                return [move, 'checkmate']

            split_fen = self.board.fen().split(" ")
            repetition_fen = split_fen[0] + split_fen[1] + split_fen[3]
            fen = split_fen[0] + split_fen[1]

            if self.board.is_stalemate() or self.board.is_insufficient_material() or split_fen[4] == 50 or self.check_repetition(self.board_store, repetition_fen):
                move_score = 0.0
            elif fen not in self.fen_store:
                future_moves, base_eval = self.order_moves_white()
                move_score = self.sam_evaluate_board(base_eval)
                self.fen_store[fen] = move_score
            else:
                move_score = self.fen_store[fen]    
            
            self.board.pop()
            move_scores.append((move, move_score))

        move_scores.sort(key = lambda x: x[1])
        priority_moves = list(zip(*move_scores))[0]

        return priority_moves
    

    def Sam_AI_move(self):
        """Determine the AI move"""
        start_time = perf_counter()
        alpha = -5000000
        beta = 5000000
        self.sam_time_allowance = start_time + self.sam_total_time / 60

        if self.sam_bot_white == True:
            priority_moves = self.firstminimaxmax()
            if priority_moves[-1] != "checkmate":
                depth = 3
                best_move = self.initminimaxmax(depth, alpha, beta, priority_moves)
                # for depth in range(2, 3):
                #     best_move = self.initminimaxmax(depth, alpha, beta, priority_moves)
            else:
                best_move = priority_moves[0]

        else:
            priority_moves = self.firstminimaxmin()
            if priority_moves[-1] != "checkmate":
                depth = 3
                best_move = self.initminimaxmin(depth, alpha, beta, priority_moves)
                # for depth in range(2, 3):
                    # best_move = self.initminimaxmin(depth, alpha, beta, priority_moves)
            else:
                best_move = priority_moves[0]

        end = perf_counter()
        self.sam_total_time -= (end - start_time)

        print(f'Move taken: {end-start_time}')
        print(f'Total time left: {self.sam_total_time}')
        print(f'Total nodes: {self.nodes_total}')
        print(f'Calculated nodes: {self.nodes_calculated}')
        # print(self.board_store)

        return best_move
