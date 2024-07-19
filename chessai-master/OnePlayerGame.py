import tkinter as tk
from tkinter import messagebox
import chess
import chess.svg
from PIL import Image, ImageTk
import io
from wand.image import Image as WandImage
import random
import cProfile
import pstats
from TwoPlayerGame import TwoPlayerGame
from QuentinBot import QuentinBot
from SamBot import SamBot
from DanBot import DanBot
from MatthewBot import MatthewBot


class OnePlayerGame(TwoPlayerGame, QuentinBot, SamBot, MatthewBot, DanBot):
    def __init__(self, master, outcome, bot_choice, player_white=True):
        super().__init__(master, outcome)
        # Shared variables
        self.player_white = player_white
        self.bot_choice = bot_choice
        self.piece_names = {1:'pawn', 2:'knight', 3:'bishop', 4:'rook', 5:'queen', 6:'king'}
        # Can be used as a faster check for threefold repetition
        self.board_store = [""]

        # Quentin's variables
        self.piece_value = {1:1, 2:2.9, 3:3.1, 4:5, 5:9, 6:0, None:0}
        self.pieces = [1, 2, 3, 4, 5]

        # Sam's variables
        self.sam_total_time = 60
        self.sam_current_time = 0
        self.sam_time_allowance = 1
        if player_white == True:
            self.sam_bot_white = False
        else:
            self.sam_bot_white = True
        self.sam_piece_value = {1:100, 2:300, 3:300, 4:500, 5:900, 6:10000, None:0}
        self.sam_pieces = [1, 2, 3, 4, 5, 6]
        self.endgame_pieces = [2, 3, 4, 5]
        self.endgame_value = {1:0, 2:1, 3:1, 4:2, 5:4, 6:0, None:0}
        self.fen_store = {}
        self.piece_square_tables = self.read_config("configs/piece_square_tables.json")
        self.nodes_total = 0
        self.nodes_calculated = 0
        self.board_squares = {
            'a1': 0, 'b1':1, 'c1': 2, 'd1':3 ,'e1': 4, 'f1':5 ,'g1': 6, 'h1':7,
            'a2': 8, 'b2':9, 'c2': 10, 'd2':11 ,'e2': 12, 'f2':13 ,'g2': 14, 'h2':15,
            'a3': 16, 'b3':17, 'c3': 18, 'd3':19 ,'e3': 20, 'f3':21 ,'g3': 22, 'h3':23,
            'a4': 24, 'b4':25, 'c4': 26, 'd4':27 ,'e4': 28, 'f4':29 ,'g4': 30, 'h4':31,
            'a5': 32, 'b5':33, 'c5': 34, 'd5':35 ,'e5': 36, 'f5':37 ,'g5': 38, 'h5':39,
            'a6': 40, 'b6':41, 'c6': 42, 'd6':43 ,'e6': 44, 'f6':45 ,'g6': 46, 'h6':47,
            'a7': 48, 'b7':49, 'c7': 50, 'd7':51 ,'e7': 52, 'f7':53 ,'g7': 54, 'h7':55,
            'a8': 56, 'b8':57, 'c8': 58, 'd8':59 ,'e8': 60, 'f8':61 ,'g8': 62, 'h8':63,
            }
        self.move_list = []
        self.board_store = [""]
        self.pawn_attack_grid = {
            "White": [
                list(), list(), list(), list(), list(), list(), list(), list(),
                [17], [16, 18], [17, 19], [18, 20], [19, 21], [20, 22], [21, 23], [22],
                [25], [24, 26], [25, 27], [26, 28], [27, 29], [28, 30], [29, 31], [30],
                [33], [32, 34], [33, 35], [34, 36], [35, 37], [36, 38], [37, 39], [38],
                [41], [40, 42], [41, 43], [42, 44], [43, 45], [44, 46], [45, 47], [46],
                [49], [48, 50], [49, 51], [50, 52], [51, 53], [52, 54], [53, 55], [54],
                [57], [56, 58], [57, 59], [58, 60], [59, 61], [60, 62], [61, 63], [62],
                list(), list(), list(), list(), list(), list(), list(), list()
            ],
            "Black": [
                list(), list(), list(), list(), list(), list(), list(), list(),
                [1], [0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6],
                [9], [8, 10], [9, 11], [10, 12], [11, 13], [12, 14], [13, 15], [14],
                [17], [16, 18], [17, 19], [18, 20], [19, 21], [20, 22], [21, 23], [22],
                [25], [24, 26], [25, 27], [26, 28], [27, 29], [28, 30], [29, 31], [30],
                [33], [32, 34], [33, 35], [34, 36], [35, 37], [36, 38], [37, 39], [38],
                [41], [40, 42], [41, 43], [42, 44], [43, 45], [44, 46], [45, 47], [46],
                list(), list(), list(), list(), list(), list(), list(), list()
            ]}
        self.king_attack_grid = [
            {1, 8, 9}, {0, 2, 8, 9, 10}, {1, 3, 9, 10, 11}, {2, 4, 10, 11, 12},
            {3, 5, 11, 12, 13}, {4, 6, 12, 13, 14}, {5, 7, 13, 14, 15}, {6, 14, 15},
            {0, 1, 9, 16, 17}, {0, 1, 2, 8, 10, 16, 17, 18}, {1, 2, 3, 9, 11, 17, 18, 19}, {2, 3, 4, 10, 12, 18, 19, 20},
            {3, 4, 5, 11, 13, 19, 20, 21}, {4, 5, 6, 12, 14, 20, 21, 22}, {5, 6, 7, 13, 15, 21, 22, 23}, {6, 7, 14, 22, 23},
            {8, 9, 17, 24, 25}, {8, 9, 10, 16, 18, 24, 25, 26}, {9, 10, 11, 17, 19, 25, 26, 27}, {10, 11, 12, 18, 20, 26, 27, 28},
            {11, 12, 13, 19, 21, 27, 28, 29}, {12, 13, 14, 20, 22, 28, 29, 30}, {13, 14, 15, 21, 23, 29, 30, 31}, {14, 15, 22, 30, 31},
            {32, 33, 16, 17, 25}, {32, 33, 34, 16, 17, 18, 24, 26}, {33, 34, 35, 17, 18, 19, 25, 27}, {34, 35, 36, 18, 19, 20, 26, 28},
            {35, 36, 37, 19, 20, 21, 27, 29}, {36, 37, 38, 20, 21, 22, 28, 30}, {37, 38, 39, 21, 22, 23, 29, 31}, {38, 39, 22, 23, 30},
            {33, 40, 41, 24, 25}, {32, 34, 40, 41, 42, 24, 25, 26}, {33, 35, 41, 42, 43, 25, 26, 27}, {34, 36, 42, 43, 44, 26, 27, 28},
            {35, 37, 43, 44, 45, 27, 28, 29}, {36, 38, 44, 45, 46, 28, 29, 30}, {37, 39, 45, 46, 47, 29, 30, 31}, {38, 46, 47, 30, 31},
            {32, 33, 41, 48, 49}, {32, 33, 34, 40, 42, 48, 49, 50}, {33, 34, 35, 41, 43, 49, 50, 51}, {34, 35, 36, 42, 44, 50, 51, 52},
            {35, 36, 37, 43, 45, 51, 52, 53}, {36, 37, 38, 44, 46, 52, 53, 54}, {37, 38, 39, 45, 47, 53, 54, 55}, {38, 39, 46, 54, 55},
            {40, 41, 49, 55, 57}, {40, 41, 42, 48, 50, 56, 57, 58}, {41, 42, 43, 49, 51, 57, 58, 59}, {42, 43, 44, 50, 52, 58, 59, 60},
            {43, 44, 45, 51, 53, 59, 60, 61}, {44, 45, 46, 52, 54, 60, 61, 62}, {45, 46, 47, 53, 55, 61, 62, 63}, {46, 47, 54, 62, 63},
            {48, 49, 57}, {48, 49, 50, 56, 58}, {49, 50, 51, 57, 59}, {50, 51, 52, 58, 60},
            {51, 52, 53, 59, 61}, {52, 53, 54, 60, 62}, {53, 54, 55, 61, 63}, {62, 54, 55}
            ]
        self.column_reference = {
            0: {8, 16, 24, 32, 40, 48, 56}, 1: {9, 17, 25, 33, 41, 49, 57},
            2: {10, 18, 26, 34, 42, 50, 58}, 3: {11, 19, 27, 35, 43, 51, 59},
            4: {12, 20, 28, 36, 44, 52, 60}, 5: {13, 21, 29, 37, 45, 53, 61},
            6: {14, 22, 30, 38, 46, 54, 62}, 7: {15, 23, 31, 39, 47, 55, 63},
            8: {0, 16, 24, 32, 40, 48, 56}, 9: {1, 17, 25, 33, 41, 49, 57},
            10: {2, 18, 26, 34, 42, 50, 58}, 11: {3, 19, 27, 35, 43, 51, 59},
            12: {4, 20, 28, 36, 44, 52, 60}, 13: {5, 21, 29, 37, 45, 53, 61},
            14: {6, 22, 30, 38, 46, 54, 62}, 15: {7, 23, 31, 39, 47, 55, 63},
            16: {0, 8, 24, 32, 40, 48, 56}, 17: {1, 9, 25, 33, 41, 49, 57},
            18: {2, 10, 26, 34, 42, 50, 58}, 19: {3, 11, 27, 35, 43, 51, 59},
            20: {4, 12, 28, 36, 44, 52, 60}, 21: {5, 13, 29, 37, 45, 53, 61},
            22: {6, 14, 30, 38, 46, 54, 62}, 23: {7, 15, 31, 39, 47, 55, 63},
            24: {0, 8, 16, 32, 40, 48, 56}, 25: {1, 9, 17, 33, 41, 49, 57},
            26: {2, 10, 18, 34, 42, 50, 58}, 27: {3, 11, 19, 35, 43, 51, 59},
            28: {4, 12, 20, 36, 44, 52, 60}, 29: {5, 13, 21, 37, 45, 53, 61},
            30: {6, 14, 22, 38, 46, 54, 62}, 31: {7, 15, 23, 39, 47, 55, 63},
            32: {0, 8, 16, 24, 40, 48, 56}, 33: {1, 9, 17, 25, 41, 49, 57},
            34: {2, 10, 18, 26, 42, 50, 58}, 35: {3, 11, 19, 27, 43, 51, 59},
            36: {4, 12, 20, 28, 44, 52, 60}, 37: {5, 13, 21, 29, 45, 53, 61},
            38: {6, 14, 22, 30, 46, 54, 62}, 39: {7, 15, 23, 31, 47, 55, 63},
            40: {0, 8, 16, 24, 32, 48, 56}, 41: {1, 9, 17, 25, 33, 49, 57},
            42: {2, 10, 18, 26, 34, 50, 58}, 43: {3, 11, 19, 27, 35, 51, 59},
            44: {4, 12, 20, 28, 36, 52, 60}, 45: {5, 13, 21, 29, 37, 53, 61},
            46: {6, 14, 22, 30, 38, 54, 62}, 47: {7, 15, 23, 31, 39, 55, 63},
            48: {0, 8, 16, 24, 32, 40, 56}, 49: {1, 9, 17, 25, 33, 41, 57},
            50: {2, 10, 18, 26, 34, 42, 58}, 51: {3, 11, 19, 27, 35, 43, 59},
            52: {4, 12, 20, 28, 36, 44, 60}, 53: {5, 13, 21, 29, 37, 45, 61},
            54: {6, 14, 22, 30, 38, 46, 62}, 55: {7, 15, 23, 31, 39, 47, 63},
            56: {0, 8, 16, 24, 32, 40, 48}, 57: {1, 9, 17, 25, 33, 41, 49},
            58: {2, 10, 18, 26, 34, 42, 50}, 59: {3, 11, 19, 27, 35, 43, 51},
            60: {4, 12, 20, 28, 36, 44, 52}, 61: {5, 13, 21, 29, 37, 45, 53},
            62: {6, 14, 22, 30, 38, 46, 54}, 63: {7, 15, 23, 31, 39, 47, 55}
        }
    
    def on_release(self, event):
        self.label.config(cursor="")
        x = event.x
        y = event.y
        to_square = self.pixel_to_square(x, y)
        move = self.determine_move(self.from_square, to_square)
        self.make_move(move)

        split_fen = self.board.fen().split(" ")
        fen = split_fen[0] + split_fen[1] +split_fen[3]
        self.board_store.append(fen)


        # Make sure the AI only plays during it's turn and when the game is not over
        if (self.player_white and not self.board.turn) or (not self.player_white and self.board.turn) and \
            not self.board.is_game_over(claim_draw=True):
            if self.bot_choice == "QuentinBot":
                Aimove = self.Quentin_AI_move()
            elif self.bot_choice == "SamBot":
                # with cProfile.Profile() as pr:
                #     Aimove = self.Sam_AI_move()

                # stats = pstats.Stats(pr)
                # stats.sort_stats(pstats.SortKey.TIME)
                # stats.print_stats()

                Aimove = self.Sam_AI_move()
            elif self.bot_choice == "DanBot":
                Aimove = self.Dan_AI_move()
            elif self.bot_choice == "MatthewBot":
                Aimove = self.Matthew_AI_move()
            else:
                raise exception('Bot name not recognised')

            self.make_move(Aimove)

            split_fen = self.board.fen().split(" ")
            fen = split_fen[0] + split_fen[1] +split_fen[3]
            self.board_store.append(fen)

    