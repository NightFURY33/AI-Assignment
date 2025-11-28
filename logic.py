
# 棋盘尺寸为 15x15
BOARD_SIZE = 15
EMPTY = 0  # 空位
BLACK = 1  # 黑子 
WHITE = 2  # 白子 

def initialize_board():
    # 初始化棋盘。
    board = []
    for _ in range(BOARD_SIZE):
        row = [EMPTY] * BOARD_SIZE
        board.append(row)
    
    return board

def check_win(board, r, c, player):#检查是否有获胜情况
    # 定义四个方向
    directions = [(0, 1),(1, 0),(1, 1),(1, -1)]
    # 遍历四个方向
    for dr, dc in directions:
        count = 1  
        for i in range(1, 5):
            nr, nc = r + dr * i, c + dc * i #下一个坐标
            # 是否在棋盘内
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                break 
            # 是否是当前玩家的棋子
            if board[nr][nc] == player:
                count += 1
            else:
                break # 遇到空位或对手棋子
        for i in range(1, 5):
            nr, nc = r - dr * i, c - dc * i # 相反方向
            # 是否在棋盘内
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                break
            # 和上一个方向同理
            if board[nr][nc] == player:
                count += 1
            else:
                break
                
        # 是否达到五子
        if count >= 5:
            return True
            
    return False
