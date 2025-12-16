import tkinter as tk
import Algorithm as Algo
import logic
from tkinter import messagebox
from PIL import Image, ImageTk

# Constants
BOARD_SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2

# UI dimensions
CELL_SIZE = 40
MARGIN = 30
WINDOW_SIZE = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)

# Global variables
root = None
canvas = None
status_label = None
current_player = BLACK
player_color = None
ai_color = None
move_made = 0
game_started = False
pending_after_id = None
bg_photo = None
board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def draw_board():
    """Draw the board grid and stones."""
    global canvas, board
    canvas.delete("all")
    
    # Draw background image if available
    try:
        global bg_photo
        if bg_photo is not None:
            canvas.create_image(0, 0, image=bg_photo, anchor=tk.NW)
    except Exception:
        pass
    
    # Draw grid lines
    for i in range(BOARD_SIZE):
        # Horizontal lines
        start_x = MARGIN
        start_y = MARGIN + i * CELL_SIZE
        end_x = MARGIN + (BOARD_SIZE - 1) * CELL_SIZE
        end_y = start_y
        canvas.create_line(start_x, start_y, end_x, end_y)
        
        # Vertical lines
        start_x = MARGIN + i * CELL_SIZE
        start_y = MARGIN
        end_x = start_x
        end_y = MARGIN + (BOARD_SIZE - 1) * CELL_SIZE
        canvas.create_line(start_x, start_y, end_x, end_y)

    # Draw stones
    stone_radius = CELL_SIZE * 0.4
    
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] != EMPTY:
                center_x = MARGIN + col * CELL_SIZE
                center_y = MARGIN + row * CELL_SIZE
                
                color = "black" if board[row][col] == BLACK else "white"
                outline = "gray" if board[row][col] == WHITE else "black"
                
                canvas.create_oval(
                    center_x - stone_radius, center_y - stone_radius,
                    center_x + stone_radius, center_y + stone_radius,
                    fill=color, outline=outline
                )


def handle_click(event):
    """Handle mouse click for player move."""
    global game_started, board, move_made
    
    if not game_started or current_player != player_color:
        return  # Not player's turn
    
    # Calculate board coordinates
    col = round((event.x - MARGIN) / CELL_SIZE)
    row = round((event.y - MARGIN) / CELL_SIZE)
    
    # Validate coordinates
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        return
    
    # Check if position is empty
    if board[row][col] == EMPTY:
        move_made = 1
        board[row][col] = player_color
        draw_board()
        
        # Check if player wins
        if logic.check_win(board, row, col, player_color):
            messagebox.showinfo("Game Over", "You win!")
            game_started = False
            return
        
        # Check for draw
        if logic.is_board_full(board):
            messagebox.showinfo("Game Over", "Game ends in a draw!")
            game_started = False
            return
        
        # Switch to AI turn
        on_player_move()
    else:
        messagebox.showwarning("Invalid Move", "This position is already occupied.")
        return


def choose_color():
    """Let player choose stone color."""
    global game_started, player_color, ai_color
    
    if game_started:
        messagebox.showwarning("Game In Progress", "A game is already in progress!")
        return 
    
    choice = messagebox.askquestion("Color Choice", "Do you want to play as black? (Black plays first)")
    if choice == 'yes':
        player_color = BLACK
        ai_color = WHITE
    else:
        player_color = WHITE
        ai_color = BLACK
    
    messagebox.showinfo("Choice Made", f"You chose {'black' if player_color == BLACK else 'white'}. The game begins!")
    start_game_turn()


def ai_move():
    """AI makes a move (blocking version)."""
    global board, current_player, ai_color, player_color, status_label, move_made, game_started, pending_after_id
    
    if not game_started:
        pending_after_id = None
        return
    
    # Disable interaction during AI thinking
    canvas.unbind("<Button-1>")
    status_label.config(text="AI is thinking...")
    root.update()  # Force UI update
    
    try:
        # Get AI move (blocking call)
        position = Algo.find_best_move(board, ai_color, max_depth=3)
    except Exception as e:
        print("AI error:", e)
        position = None
    
    # Re-enable interaction
    canvas.bind("<Button-1>", handle_click)
    
    if not game_started:
        return
    
    # Handle no valid move
    if position is None:
        if logic.is_board_full(board):
            messagebox.showinfo("Game Over", "Game ends in a draw!")
            game_started = False
        else:
            messagebox.showinfo("Game Over", "No valid moves available!")
            board = logic.initialize_board()
            draw_board()
        return
    
    # Apply AI move
    board[position[0]][position[1]] = ai_color
    draw_board()
    
    # Check if AI wins
    if logic.check_win(board, position[0], position[1], ai_color):
        messagebox.showinfo("Game Over", "AI wins!")
        game_started = False
        return
    
    # Check for draw
    if logic.is_board_full(board):
        messagebox.showinfo("Game Over", "Game ends in a draw!")
        game_started = False
        return
    
    # Switch back to player
    current_player = player_color
    move_made = 0
    status_label.config(text="Your turn")


def start_game_turn():
    """Start the game with correct turn order."""
    global board, current_player, ai_color, player_color, status_label, move_made, game_started, pending_after_id
    
    game_started = True
    move_made = 0
    board = logic.initialize_board()
    draw_board()
    
    if ai_color == BLACK:  # AI plays first
        current_player = ai_color
        pending_after_id = root.after(500, ai_move)  # Delay for visual effect
    else:  # Player plays first
        current_player = player_color
        status_label.config(text="Your turn")


def on_player_move():
    """Handle transition after player move."""
    global current_player, ai_color, status_label, move_made, game_started, pending_after_id
    
    if not game_started or move_made == 0:
        return
    
    current_player = ai_color
    move_made = 0
    status_label.config(text="AI is thinking...")
    pending_after_id = root.after(800, ai_move)  # Delay for visual effect


def confirm_exit():
    """Confirm before exiting."""
    global pending_after_id, game_started, root
    
    ok = messagebox.askokcancel("Quit", "Do you really want to quit?")
    
    if ok:
        # Cancel any pending callbacks
        try:
            if pending_after_id is not None:
                root.after_cancel(pending_after_id)
        except Exception:
            pass
        
        game_started = False
        try:
            if root is not None:
                root.quit()
                root.destroy()
        except Exception:
            pass
        finally:
            root = None


def restart_game():
    """Restart the game."""
    global game_started, board, current_player, player_color, ai_color, status_label, move_made, pending_after_id
    
    if messagebox.askyesno("Restart", "Do you want to restart the game?"):
        # Cancel any pending callbacks
        try:
            if pending_after_id is not None:
                root.after_cancel(pending_after_id)
        except Exception:
            pass
        
        # Reset game state
        board = logic.initialize_board()
        current_player = BLACK
        game_started = False
        player_color = None
        ai_color = None
        move_made = 0
        draw_board()
        status_label.config(text="Welcome to Gomoku!")


def start_gui():
    """Initialize and start the GUI."""
    global root, canvas, status_label, board, current_player, game_started, bg_photo
    
    root = tk.Tk()
    root.title("Gomoku")
    
    # Center window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - WINDOW_SIZE) // 2
    y = (screen_height - WINDOW_SIZE) // 2
    root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE + 80}+{x}+{y}")
    
    # Reset game state
    board = logic.initialize_board()
    current_player = BLACK
    game_started = False
    
    # Control panel
    control_frame = tk.Frame(root, height=80, bg="#E3CF57")
    control_frame.pack(side=tk.TOP, fill=tk.X)
    
    # Status label
    status_label = tk.Label(control_frame, text="Welcome to Gomoku!", bg="#E3CF57", font=("Arial", 12))
    status_label.pack(pady=5)
    
    # Buttons
    button_frame = tk.Frame(control_frame, bg="#E3CF57")
    button_frame.pack(pady=5)
    
    tk.Button(button_frame, text="Start Game", command=choose_color, height=1, width=15).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Restart", command=restart_game, height=1, width=15).pack(side=tk.LEFT, padx=5)
    
    # Game board canvas
    canvas = tk.Canvas(root, width=WINDOW_SIZE, height=WINDOW_SIZE, bg="#E3CF57")
    canvas.pack()
    canvas.focus_set()
    
    # Load background image
    try:
        img = Image.open('mmexport1765254795139_edit_70690453677752.jpg')
        img = img.resize((WINDOW_SIZE, WINDOW_SIZE), Image.LANCZOS)
        bg_photo = ImageTk.PhotoImage(img)
        canvas.bg_photo = bg_photo  # Keep reference
    except Exception:
        bg_photo = None
    
    # Initial draw
    draw_board()
    
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", confirm_exit)
    canvas.bind("<Button-1>", handle_click)
    
    root.mainloop()


if __name__ == "__main__":
    start_gui()