import tkinter as tk
import Algorithm as Algo
import logic 
from tkinter import messagebox
import Algorithm as Algo


# 之前出现常量
BOARD_SIZE = 15
Empty = 0
Black = 1
White = 2

# 界面尺寸
CELL_SIZE = 40   # 格子大小
MARGIN = 30      # 边缘留白
WINDOW_SIZE = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)

# 全局变量
root = None
canvas = None
state = None  # 标签控件
current_player=Black  # 黑子先行
player_color=None
ai_color=None
warning=0
AI_turn=0
move=0 #确认玩家是否已经移动
win=0 #确认是否有获胜
game_started = False  # 游戏是否已开始

# 用来测试初始化棋盘
board = [[Empty for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def draw_board():
    """
    功能：根据全局 board 变量的状态，绘制网格线和棋子
    """
    global canvas, board
    
    # 清空画布，准备重绘
    canvas.delete("all")
    
    # 绘制网格线
    for i in range(BOARD_SIZE):
        # 横线
        start_x = MARGIN
        start_y = MARGIN + i * CELL_SIZE
        end_x = MARGIN + (BOARD_SIZE - 1) * CELL_SIZE
        end_y = start_y
        canvas.create_line(start_x, start_y, end_x, end_y)
        
        # 竖线
        start_x = MARGIN + i * CELL_SIZE
        start_y = MARGIN
        end_x = start_x
        end_y = MARGIN + (BOARD_SIZE - 1) * CELL_SIZE
        canvas.create_line(start_x, start_y, end_x, end_y)

    # --- B. 绘制棋子 ---
    # 棋子半径 (比格子小一点，留出空隙)
    r_offset = CELL_SIZE * 0.4
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != Empty:
                # 计算棋子圆心坐标 (交叉点)
                center_x = MARGIN + c * CELL_SIZE
                center_y = MARGIN + r * CELL_SIZE
                
                # 设定颜色
                color = "black" if board[r][c] == Black else "white"
                outline_color = "gray" if board[r][c] == White else "black"
                
                # 绘制圆形
                canvas.create_oval(
                    center_x - r_offset, center_y - r_offset,
                    center_x + r_offset, center_y + r_offset,
                    fill=color, outline=outline_color
                )

def handle_click(event):
    """
    功能：处理鼠标点击事件，更新棋盘状态并重绘
    """
    if not game_started or current_player != player_color:
        return  # 不是玩家回合或游戏未开始，忽略点击
    
    global board, move, warning
    
    # 计算点击位置对应的行列
    c = round((event.x - MARGIN) / CELL_SIZE)
    r = round((event.y - MARGIN) / CELL_SIZE)
    
    # 检查坐标有效性
    if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
        return
    
    # 检查该位置是否有效
    if board[r][c] == Empty:
        warning = 0
        move = 1
        board[r][c] = player_color
        draw_board()
        
        # 检查玩家是否获胜
        if logic.check_win(board, r, c, player_color):
            messagebox.showinfo("Game Over", "You win!")
            board=logic.initialize_board()
            draw_board()
            return
        
        # 切换到AI回合
        on_player_move()
    else:
        messagebox.showwarning("Invalid Move", "This position is already occupied.")
        warning = 1
        return

def choose_color():
        choice = messagebox.askquestion("Please make your choice", "Do you want to play as black？ (Black plays first)")
        if choice == 'yes':
            global player_color, ai_color
            player_color = Black
            ai_color = White
        else:
            player_color = White
            ai_color = Black
        messagebox.showinfo("Choice made", f"You chose {'black' if player_color == Black else 'white'}. The game begins!")
        start_game_turn()

def AI_move():
    global board, current_player, ai_color, player_color, state, move
    
    state.config(text="AI is making its move...")
    root.update()
    
    position = Algo.find_best_move(board, ai_color, max_depth=3)
    if position is None:  # 没有可走的位置
        messagebox.showinfo("Game Over", "No valid moves available!")
        board=logic.initialize_board()
        draw_board()
        return
    
    board[position[0]][position[1]] = ai_color
    draw_board()
    
    if logic.check_win(board, position[0], position[1], ai_color):
        messagebox.showinfo("Game Over", "AI wins!")
        board=logic.initialize_board()
        draw_board()
        return
    
    # 切换回玩家回合
    current_player = player_color
    move = 0  # 重置move标志
    state.config(text="Your turn")

def start_game_turn():
    """启动游戏循环的第一步"""
    global board, current_player, ai_color, player_color, state, move, game_started
    game_started = True
    move = 0
    
    if ai_color == Black:  # AI先行
        current_player = ai_color
        root.after(500, AI_move)
    else:  # 玩家先行
        current_player = player_color
        state.config(text="Your turn")

def on_player_move():
    """处理玩家移动后的回合转换"""
    global board, current_player, ai_color, player_color, state, move, game_started
    
    if not game_started or move == 0:
        return
    
    current_player = ai_color
    move = 0  # 重置标志
    state.config(text="AI is thinking...")
    root.after(800, AI_move)  # 延迟800ms让AI思考
        

def reconfirm():
    if messagebox.askokcancel("Quit", "Do you really want to quit?"):
        root.destroy()

def restart():
    if messagebox.askyesno("Restart", "Do you want to restart the game?"):
      global board, current_player, game_started
      board = logic.initialize_board()
      current_player = Black  # 黑子先行
      game_started = False
      draw_board()



    

def start_gui():
    """
    功能：初始化窗口、画布，并启动主循环
    """
    global root, canvas, state, board, current_player, game_started
    
    root = tk.Tk()
    root.title("五子棋 (Gobang)")
    
    # 窗口居中计算
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - WINDOW_SIZE) // 2
    y = (screen_height - WINDOW_SIZE) // 2
    root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE + 80}+{x}+{y}")
    
    # 重置游戏状态
    board = logic.initialize_board()
    current_player = Black
    game_started = False
    
    # 创建顶部控制区
    control_frame = tk.Frame(root, height=80, bg="#E3CF57")
    control_frame.pack(side=tk.TOP, fill=tk.X)
    
    # 状态标签
    state = tk.Label(control_frame, text="Welcome to play gomoku!", bg="#E3CF57", font=("Arial", 12))
    state.pack(pady=5)
    
    # 按钮框
    button_frame = tk.Frame(control_frame, bg="#E3CF57")
    button_frame.pack(pady=5)
    
    tk.Button(button_frame, text="Start Game", command=choose_color, height=1, width=15).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Restart", command=start_gui, height=1, width=15).pack(side=tk.LEFT, padx=5)
    
    # 创建画布 (背景色：木纹色)
    canvas = tk.Canvas(root, width=WINDOW_SIZE, height=WINDOW_SIZE, bg="#E3CF57")
    canvas.pack()
    canvas.focus_set()
    # 绘制棋盘
    draw_board()
    
    root.resizable(False, False)
    

    
    root.protocol("WM_DELETE_WINDOW", reconfirm)
    canvas.bind("<Button-1>", handle_click)

    root.mainloop()




# 主程序入口
if __name__ == "__main__":
    start_gui()