# 棋盘尺寸为 15x15
BOARD_SIZE = 15
Empty = 0  # 空位
Black = 1  # 黑子
White = 2  # 白子

def initialize_board():
    # 初始化棋盘。
    board = []
    for _ in range(BOARD_SIZE):
        row = [Empty] * BOARD_SIZE
        board.append(row)
    
    return board

def is_board_full(board):
    """检查棋盘是否已满（没有空位）"""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == Empty:
                return False
    return True

def check_win(board, r, c, player):#检查是否有获胜情况
    # 定义四个方向
    directions = [(0, 1),(1, 0),(1, 1),(1, -1)]
    # 遍历四个方向
    for dr, dc in directions:
        count = 1
        for i in range(1, 5):
            nr= r + dr * i
            nc= c + dc * i #下一个坐标
            # 是否在棋盘内
            if not (0<=nr<BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                break
            # 是否是当前玩家的棋子
            if board[nr][nc] ==player:
                count += 1
            else:
                break # 遇到空位或对手棋子
        for i in range(1, 5):
            nr = r - dr * i
            nc = c - dc * i # 相反方向
            # 是否在棋盘内
            if not (0<=nr<BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                break
            # 是否是当前玩家的棋子
            if board[nr][nc] ==player:
                count += 1
            else:
                break # 遇到空位或对手棋子
        if count >=5:
            return True
    return False