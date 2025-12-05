# 棋盘评估权重（可根据实际情况调整）
SCORES = {
    "five": 100000,    # 五子连珠
    "live_four": 10000, # 活四
    "four_with_gap": 1000,       # 冲四（有一个缺口的四连）
    "live_three": 100,  # 活三
    "three_with_gap": 10,         # 冲三（有一个缺口的三连）
    "live_two": 5,      # 活二
    "two_with_gap": 1           # 冲二
}

def evaluate_board(board, player):
    """评估当前棋盘对指定玩家的分数"""
    score = 0
    opponent = White if player == Black else Black
    
    # 评估玩家和对手的棋型，玩家加分，对手减分
    score += evaluate_player(board, player)
    score -= evaluate_player(board, opponent)
    
    return score

def evaluate_player(board, player):
    """评估指定玩家在棋盘上的棋型分数"""
    score = 0
    # 遍历棋盘所有位置
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                # 检查以该位置为中心的四个方向的棋型
                score += check_patterns(board, r, c, player)
    return score

def check_patterns(board, r, c, player):
    """检查指定位置周围的棋型并返回对应分数"""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # 四个方向
    total = 0
    
    for dr, dc in directions:
        # 获取该方向上的连续棋子和空位情况
        line = get_line_pattern(board, r, c, dr, dc, player)
        # 根据棋型计算分数
        total += pattern_to_score(line)
    
    return total

def get_line_pattern(board, r, c, dr, dc, player):
    """获取指定方向上的棋子排列模式"""
    pattern = []
    # 向一个方向延伸4步
    for i in range(-4, 5):
        nr = r + dr * i
        nc = c + dc * i
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr][nc] == player:
                pattern.append(1)  # 玩家棋子
            elif board[nr][nc] == Empty:
                pattern.append(0)  # 空位
            else:
                pattern.append(2)  # 对手棋子
        else:
            pattern.append(3)  # 边界外
    return pattern

def pattern_to_score(pattern):
    """将棋子模式转换为对应分数"""
    # 简化的棋型判断（实际情况需更复杂）
    s = ''.join(map(str, pattern))
    
    # 五子连珠
    if '11111' in s:
        return SCORES["five"]
    # 活四（两端为空位）
    if '011110' in s:
        return SCORES["live_four"]
    # 冲四（一端有空位，另一端被阻挡或边界）
    if '011112' in s or '211110' in s or '011113' in s or '311110' in s:
        return SCORES["four_with_gap"]
    # 活三（两端为空位的三连）
    if '01110' in s:
        return SCORES["live_three"]
    # 冲三（一端有空位的三连）
    if '01112' in s or '21110' in s or '01113' in s or '31110' in s:
        return SCORES["three_with_gap"]
    # 活二（两端为空位的二连）
    if '0110' in s:
        return SCORES["live_two"]
    # 冲二（一端有空位的二连）
    if '0112' in s or '2110' in s or '0113' in s or '3110' in s:
        return SCORES["two_with_gap"]
    
    return 0

def is_game_over(board):
    """检查游戏是否结束（有玩家获胜）"""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != Empty:
                if check_win(board, r, c, board[r][c]):
                    return True
    return False

def minimax(board, depth, is_maximizing, alpha, beta, player):
    """Minimax算法带alpha-beta剪枝"""
    # 终止条件：深度为0或游戏结束
    if depth == 0 or is_game_over(board):
        return evaluate_board(board, player)
    
    current_player = player if is_maximizing else (White if player == Black else Black)
    best_score = -float('inf') if is_maximizing else float('inf')
    
    # 遍历所有可能的走法
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == Empty:
                # 模拟落子
                board[r][c] = current_player
                # 递归调用
                score = minimax(board, depth - 1, not is_maximizing, alpha, beta, player)
                # 撤销落子
                board[r][c] = Empty
                
                if is_maximizing:
                    # 最大化玩家：取最大值
                    if score > best_score:
                        best_score = score
                    if best_score >= beta:
                        return best_score  # beta剪枝
                    alpha = max(alpha, best_score)
                else:
                    # 最小化玩家：取最小值
                    if score < best_score:
                        best_score = score
                    if best_score <= alpha:
                        return best_score  # alpha剪枝
                    beta = min(beta, best_score)
    
    return best_score

def find_best_move(board, player, max_depth=3):
    """寻找最佳落子位置"""
    best_score = -float('inf')
    best_move = None
    
    # 遍历所有空位
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == Empty:
                # 模拟落子
                board[r][c] = player
                # 评估该走法（下一层是对手走，最小化玩家）
                score = minimax(board, max_depth - 1, False, -float('inf'), float('inf'), player)
                # 撤销落子
                board[r][c] = Empty
                
                # 更新最佳走法
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    return best_move