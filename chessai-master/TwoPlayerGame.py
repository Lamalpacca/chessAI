import tkinter as tk
from tkinter import messagebox
import chess
import chess.svg
from PIL import Image, ImageTk
import io
from wand.image import Image as WandImage


class TwoPlayerGame:
    def __init__(self, master, outcome): 
        self.master = master
        self.outcome = outcome
        self.board = chess.Board()
        self.plot_frame = tk.Frame(master)
        self.plot_frame.pack()
        self.update_board() 

    def determine_move(self, from_square, to_square):
            # Check if the move is a pawn promotion (pawn reaches the last rank)
            promotion = None
            moving_piece = self.board.piece_at(from_square)
            if moving_piece and moving_piece.piece_type == chess.PAWN:
                if to_square in chess.SquareSet(chess.BB_RANK_1 | chess.BB_RANK_8):
                    # TODO: promotion is not necessarily a Queen
                    promotion = chess.QUEEN

            return chess.Move(from_square=from_square, to_square=to_square, promotion=promotion)

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
    
    def on_click(self, event):
        x = event.x
        y = event.y
        self.from_square = self.pixel_to_square(x, y)  # Store the starting square
        self.label.config(cursor="hand2")  # Change cursor to indicate dragging
    
    def on_drag(self, event):
        # This function will be called when the mouse is dragged
        pass  # We don't need to do anything here, but the function must exist
    
    def on_release(self, event):
        self.label.config(cursor="")  # Reset cursor to default
        x = event.x
        y = event.y
        to_square = self.pixel_to_square(x, y)
        move = self.determine_move(self.from_square, to_square)
        self.make_move(move)
    
    def pixel_to_square(self, x, y):
        # Assuming 8x8 grid is 40 + 90*8 + 40 pixels long and wide
        row = 7 - ((y-40) // 90) # For some reason height is counted top to bottom
        col = (x-40) // 90
        return chess.square(col, row)

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
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<ButtonRelease-1>", self.on_release)
