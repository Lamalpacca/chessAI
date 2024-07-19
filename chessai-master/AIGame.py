import tkinter as tk
from tkinter import messagebox
import chess
import chess.svg
from PIL import Image, ImageTk
import io
from wand.image import Image as WandImage
import random
import time

class AIGame:
    def __init__(self, master, outcome): 
        self.master = master
        self.outcome = outcome
        self.board = chess.Board()
        self.plot_frame = tk.Frame(master)
        self.plot_frame.pack()
        self.update_board()

    def make_move(self, move):
        if move in self.board.legal_moves: # If the move is legal
            self.board.push(move)
            self.update_board()
            if self.board.is_game_over(claim_draw=True): # If the game is over or someone can claim draw
                self.resolve_game_over() # End the game
            
        elif len(list(self.board.legal_moves)) == 0: # There are no legal moves
            self.outcome = 0
            messagebox.showerror("End of game", "No legal moves, something's gone wrong")
            self.master.destroy()
        
        else:
            messagebox.showerror("Illegal Move", "The move is not legal. Please try again.")
                

    def resolve_game_over(self):
        if self.board.is_checkmate(): #TODO: improve this logic
            if self.board.turn: # It's white turn to play
                self.outcome = -1
                messagebox.showinfo("End of game","Checkmate! Black wins")
            else:
                self.outcome = 1
                messagebox.showinfo("End of game","Checkmate! White wins")
        
        elif self.board.can_claim_draw() or self.board.is_stalemate() or self.board.is_insufficient_material():
            self.outcome = 0
            messagebox.showinfo("End of game","It's a draw!")
                    
        self.master.destroy() # Close the game
    
    # Run the game after a click
    def on_click(self, event):
        # Aimove = self.AI_move()
        # self.make_move(Aimove)
        n = 0
        while n <5:
            Aimove = self.AI_move()
            time.sleep(2)
            self.make_move(Aimove)
            n += 1
    
    # Very simple random move generator
    def AI_move(self):
        return random.choice(list(self.board.legal_moves))

    def save_board_image(self, image_data):
        # Specify the path where you want to save the image
        image_path = "board_image.png" 
        with open(image_path, 'wb') as f:
            f.write(image_data)

    def update_board(self):
        for widget in self.plot_frame.winfo_children(): # Destroy the old image
            widget.destroy()

        svg_data = chess.svg.board(self.board).encode('utf-8') # Save the board as an image
        with WandImage(blob=svg_data, format='svg') as image:
            png_image = image.make_blob('jpg')

        # Open it with PIL and resize
        image = Image.open(io.BytesIO(png_image)).resize((800, 800))
        photo = ImageTk.PhotoImage(image)

        self.save_board_image(png_image)

        # Show the new image
        self.label = tk.Label(self.plot_frame, image=photo)
        self.label.image = photo
        self.label.pack()

        self.label.bind("<Button-1>", self.on_click)
