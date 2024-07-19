import tkinter as tk
from TwoPlayerGame import TwoPlayerGame
from ZeroPlayerGame import ZeroPlayerGame
from OnePlayerGame import OnePlayerGame
import chess
import chess.svg
from PIL import Image, ImageTk
from wand.image import Image as WandImage

def run():
    root = tk.Tk()
    x = OnePlayerGame(root, None, bot_choice="SamBot", player_white=True)
    root.mainloop()
    x.outcome

    # root = tk.Tk()
    # x = TwoPlayerGame(root, None)
    # root.mainloop()
    # x.outcome

    # root = tk.Tk()
    # x = ZeroPlayerGame(root, None, white_bot="SamBot", black_bot="QuentinBot")
    # root.mainloop()
    # x.outcome

if __name__ == "__main__":
    run()
