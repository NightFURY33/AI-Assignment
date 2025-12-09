import tkinter as tk
import Algorithm as Algo
import logic 
from tkinter import messagebox
import Algorithm as Algo
import threading
from PIL import Image, ImageTk


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
pending_after_id = None  # 存放 root.after 的返回 id（用于取消）
ai_search_id = 0  # 用于标记 AI 搜索任务的代号，递增以使旧任务失效
ai_working = False  # 标记是否有 AI 后台线程正在运行
ai_stop_event = None  # threading.Event，用于协作式取消后台搜索
bg_photo = None  # 用于存放背景图的 PhotoImage，防止被垃圾回收

# 用来测试初始化棋盘
board = [[Empty for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def draw_board():
    """
    功能：根据全局 board 变量的状态，绘制网格线和棋子
    """
    global canvas, board
    
    # 清空画布，准备重绘
    canvas.delete("all")
    # 如果有背景图，先绘制背景图（放在最底层）
    try:
        global bg_photo
        if bg_photo is not None:
            # 0,0 左上角对齐
            canvas.create_image(0, 0, image=bg_photo, anchor=tk.NW)
    except Exception:
        pass
    
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
            
            return
        
        # 切换到AI回合
        on_player_move()
    else:
        messagebox.showwarning("Invalid Move", "This position is already occupied.")
        warning = 1
        return

def choose_color():
        if game_started:
            messagebox.showwarning("Game In Progress", "A game is already in progress!")
            return 
        
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
    """
    非阻塞的 AI 启动器：在主线程里产生一个后台线程去运行耗时的搜索。
    后台线程完成后通过 `root.after(0, ...)` 回到主线程更新 UI。
    使用 `ai_search_id` 来使重启或新的搜索使旧线程失效，避免旧线程把过时结果应用到界面上。
    """
    global board, current_player, ai_color, player_color, state, move, pending_after_id, game_started, ai_search_id, ai_working

    # 如果游戏已被重置/终止，直接返回
    if not game_started:
        pending_after_id = None
        return

    # 如果已有后台搜索在运行，忽略重复请求
    if ai_working:
        return

    # 标记当前搜索并记下 id
    ai_working = True
    ai_search_id += 1
    this_search_id = ai_search_id

    # 创建协作式取消事件，restart/reconfirm 会设置它来取消后台搜索
    global ai_stop_event
    ai_stop_event = threading.Event()
    stop_ev = ai_stop_event

    # 更新状态栏（主线程）
    state.config(text="AI is making its move...")
    root.update()

    # 传入棋盘快照，避免后台线程访问共享可变数据
    board_snapshot = [row[:] for row in board]

    def worker(board_snap, search_id, stop_ev):
        # 在后台线程中执行耗时搜索
        try:
            position = Algo.find_best_move(board_snap, ai_color, max_depth=3, stop_event=stop_ev)
        except Exception as e:
            position = None
            print("AI worker error:", e)

        # 回到主线程安全地应用结果
        def finish():
            global board, current_player, move, state, ai_working
            # 如果该搜索已被新的搜索或重启覆盖，则忽略结果
            if search_id != ai_search_id or not game_started or (stop_ev is not None and stop_ev.is_set()):
                ai_working = False
                return

            if position is None:
                messagebox.showinfo("Game Over", "No valid moves available!")
                # 此处选择重新初始化棋盘并返回（保持旧行为）
                board = logic.initialize_board()
                draw_board()
                ai_working = False
                return

            board[position[0]][position[1]] = ai_color
            draw_board()

            if logic.check_win(board, position[0], position[1], ai_color):
                messagebox.showinfo("Game Over", "AI wins!")
                ai_working = False
                return

            # 切换回玩家回合
            current_player = player_color
            move = 0  # 重置move标志
            state.config(text="Your turn")
            ai_working = False

        root.after(0, finish)

    t = threading.Thread(target=worker, args=(board_snapshot, this_search_id, stop_ev), daemon=True)
    t.start()

def start_game_turn():
    """启动游戏循环的第一步"""
    global board, current_player, ai_color, player_color, state, move, game_started
    game_started = True
    move = 0
    board=logic.initialize_board()
    draw_board()
    if ai_color == Black:  # AI先行
        current_player = ai_color
        # 保存 after id，便于在 restart 时取消
        global pending_after_id
        pending_after_id = root.after(500, AI_move)
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
    global pending_after_id
    pending_after_id = root.after(800, AI_move)  # 延迟800ms让AI思考
        

def reconfirm():
    global pending_after_id, game_started, root, ai_stop_event
    # 询问用户确认退出
    try:
        ok = messagebox.askokcancel("Quit", "Do you really want to quit?")
    except Exception:
        # 如果弹窗无法显示（root 可能已被销毁），尝试直接退出
        ok = True

    if ok:
        # 取消任何挂起的 after 回调
        try:
            if pending_after_id is not None:
                root.after_cancel(pending_after_id)
        except Exception:
            pass
        pending_after_id = None
        # 请求取消任何正在运行的 AI 搜索
        try:
            global ai_stop_event
            if ai_stop_event is not None:
                ai_stop_event.set()
        except Exception:
            pass
        game_started = False
        # 尝试优雅退出 Tk 主循环并销毁窗口
        try:
            if root is not None:
                root.quit()
                root.destroy()
        except Exception:
            # 已经被销毁或其他错误，尽量安全返回
            pass
        finally:
            root = None

def restart():
    global game_started, board, current_player, player_color, ai_color, state, move, ai_stop_event
    
    # 询问用户是否确认重启
    if messagebox.askyesno("Restart", "Do you want to restart the game?"):
        # 取消任何挂起的回调（比如 AI 的延迟移动）
        global pending_after_id
        try:
            if pending_after_id is not None:
                root.after_cancel(pending_after_id)
        except Exception:
            pass
        pending_after_id = None

        # 请求取消任何正在运行的 AI 搜索（协作取消）
        try:
            global ai_stop_event
            if ai_stop_event is not None:
                ai_stop_event.set()
                ai_stop_event = None
        except Exception:
            pass

        # 重新初始化棋盘和游戏状态（在同一窗口内刷新）
        board = logic.initialize_board()
        current_player = Black  # 黑子先行
        game_started = False
        player_color = None
        ai_color = None
        move = 0
        draw_board()
        state.config(text="Welcome to play gomoku!")
    else:
        return



    

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
    tk.Button(button_frame, text="Restart", command=restart, height=1, width=15).pack(side=tk.LEFT, padx=5)
    
    # 创建画布 (背景色：木纹色)
    canvas = tk.Canvas(root, width=WINDOW_SIZE, height=WINDOW_SIZE, bg="#E3CF57")
    canvas.pack()
    canvas.focus_set()
    # 尝试加载同目录下的 JPG 背景图并缩放到画布大小
    try:
        global bg_photo
        img = Image.open('mmexport1765254795139_edit_70690453677752.jpg')
        img = img.resize((WINDOW_SIZE, WINDOW_SIZE), Image.LANCZOS)
        bg_photo = ImageTk.PhotoImage(img)
        # 保存引用，避免被 GC
        canvas.bg_photo = bg_photo
    except Exception:
        bg_photo = None

    # 绘制棋盘（会在 draw_board 中先绘制背景）
    draw_board()
    
    root.resizable(False, False)
    

    
    root.protocol("WM_DELETE_WINDOW", reconfirm)
    canvas.bind("<Button-1>", handle_click)

    root.mainloop()




# 主程序入口
if __name__ == "__main__":
    start_gui()