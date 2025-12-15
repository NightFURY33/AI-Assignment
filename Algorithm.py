import logic 
import random

# --- 全局常量和配置 ---
BOARD_SIZE = 15
Empty = 0
Black = 1
White = 2

# 限制搜索区域半径，只看棋子周围 2 格
SEARCH_RADIUS = 2 

# 棋盘评估分数，分数越高，优先级越高
SCORES = {
    "five": 10000000,    # 必胜/五连，分数设置非常高，保证优先级
    "live_four": 100000, # 活四
    "four_with_gap": 10000,       # 冲四 
    "live_three": 1000,  # 活三 
    "three_with_gap": 100,         # 冲三 
    "live_two": 10,      # 活二
    "two_with_gap": 1           # 冲二
}
<<<<<<< HEAD
    
class SearchStopped(Exception):
    """在搜索被外部请求停止时抛出的异常（协作式取消）。"""
    pass
=======

# --- 置换表 (Transposition Table) 和 Zobrist Hashing 设置 ---
# 用于存储计算过的局面结果，避免重复搜索
TRANSPOSITION_TABLE = {}
# 评估值的边界类型标记
TT_EXACT = 0      # 准确值
TT_LOWER_BOUND = 1 # 评估值是下限 (Beta 剪枝发生时)
TT_UPPER_BOUND = 2 # 评估值是上限 (Alpha 剪枝发生时)

# Zobrist Hash所需的随机数表，用于快速生成棋盘哈希
# 这是一个 15x15x3 的大表，每个位置、每种棋子都有一个随机数
ZOBRIST_TABLE = [[[random.getrandbits(64) for _ in range(3)] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


class SearchStopped(Exception):
    """在搜索被外部请求停止时抛出的异常（协作式取消）。"""
    pass

def get_zobrist_hash(board):
    """根据 Zobrist 算法快速计算当前棋盘的唯一哈希值"""
    h = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece != Empty:
                # 通过异或操作计算哈希，比直接复制棋盘快得多
                h ^= ZOBRIST_TABLE[r][c][piece]
    return h
>>>>>>> 204e0b4ec4150e7662e5dac06311b53d28650857

# --- 棋盘评估函数：决定 AI 棋力上限的核心部分 ---

def evaluate_board(board, player):
    """评估当前棋盘对指定玩家的相对分数"""
    score = 0
    opponent = White if player == Black else Black
    
    # 玩家得分 - 对手得分，得到优势值
    score += evaluate_player(board, player)
    score -= evaluate_player(board, opponent)
    
    return score

def evaluate_player(board, player):
    """评估指定玩家在棋盘上的棋型分数"""
    score = 0
    # 遍历所有棋子，计算它们在四个方向上的棋型价值
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                score += check_patterns(board, r, c, player)
    return score

def check_patterns(board, r, c, player):
    """检查并计算指定位置周围的棋型分数"""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    total = 0
    for dr, dc in directions:
        line = get_line_pattern(board, r, c, dr, dc, player)
        total += pattern_to_score(line)
    return total

def get_line_pattern(board, r, c, dr, dc, player):
    """获取一个方向上连续的棋子排列模式（用于识别棋型）"""
    pattern = []
    # 延伸至最多 4 步
    for i in range(-4, 5):
        nr = r + dr * i
        nc = c + dc * i
        # 判断是否在棋盘内
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr][nc] == player:
                pattern.append(1) # 玩家棋子
            elif board[nr][nc] == Empty:
                pattern.append(0) # 空位
            else:
                pattern.append(2) # 对手棋子
        else:
            pattern.append(3) # 边界
    return pattern

def pattern_to_score(pattern):
    """将棋子模式转换为对应分数 (基于 SCORES 字典)"""
    s = ''.join(map(str, pattern))
    
    # 识别最高分棋型
    if '11111' in s: return SCORES["five"]
    if '011110' in s: return SCORES["live_four"]

    # 冲四判断
    is_four_with_gap = ('01111' in s or '11110' in s or '10111' in s or '11011' in s or '11101' in s)
    if is_four_with_gap:
         # 简化处理冲四边界条件
         if ('01111' in s and '2' in s) or ('11110' in s and '2' in s) or \
            ('01111' in s and '3' in s) or ('11110' in s and '3' in s):
            return SCORES["four_with_gap"]
    
    if '01110' in s: return SCORES["live_three"]
        
    # 冲三判断
    if '01112' in s or '21110' in s or '01113' in s or '31110' in s or \
       '1011' in s or '1101' in s or '010110' in s:
        return SCORES["three_with_gap"]
        
    if '0110' in s: return SCORES["live_two"]
        
    if '0112' in s or '2110' in s or '0113' in s or '3110' in s:
        return SCORES["two_with_gap"]
    
    return 0

def is_game_over(board):
    """检查是否有玩家获胜，游戏是否结束"""
    # 检查是否有玩家获胜
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != Empty:
                if logic.check_win(board, r, c, board[r][c]):
                    return True
    
    # 检查是否平局（棋盘已满）
    if logic.is_board_full(board):
        return True
        
    return False

# --- 核心优化函数：限制搜索区域 ---

def generate_candidate_moves(board):
    """
    生成 Minimax 搜索所需的候选走法，只搜索已有棋子周围的 N 格。
    这是减少搜索空间的关键优化。
    """
    candidate_moves = set()
    has_piece = False
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != Empty:
                has_piece = True
                # 遍历棋子周围 SEARCH_RADIUS 范围内的格子
                for dr in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
                    for dc in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
                        nr, nc = r + dr, c + dc
                        
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == Empty:
                            candidate_moves.add((nr, nc))
                            
    # 如果棋盘是空的，从中心开始
    if not has_piece:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]

    return list(candidate_moves)

# --- Minimax 核心算法（带 Alpha-Beta） ---

def minimax(board, depth, is_maximizing, alpha, beta, player, stop_event=None):
    """
    Minimax 算法，集成了 Alpha-Beta 剪枝优化。
    """
    
    # 可协作取消：如果 stop_event 被置位，立即中断搜索
    if stop_event is not None and stop_event.is_set():
        raise SearchStopped()

    # 1. 终止条件
    if depth == 0 or is_game_over(board):
        return evaluate_board(board, player)

<<<<<<< HEAD
=======
    # 再次检查是否需要取消（避免长时间在后续计算中浪费）
    if stop_event is not None and stop_event.is_set():
        raise SearchStopped()

    # 3. 初始化并生成走法
    original_alpha = alpha # 记录原始 alpha 值，用于 TT 存储
>>>>>>> 204e0b4ec4150e7662e5dac06311b53d28650857
    current_player = player if is_maximizing else (White if player == Black else Black)
    candidate_moves = generate_candidate_moves(board)

    # 走法排序 (Move Ordering)：根据快速评估分数排序，提高剪枝效率
    scored_moves = []
    for r, c in candidate_moves:
        board[r][c] = current_player
        score = evaluate_board(board, player) 
        board[r][c] = Empty
        scored_moves.append((score, r, c))

    if is_maximizing:
        best_score = -float('inf')
        scored_moves.sort(key=lambda x: x[0], reverse=True) # Max 玩家，高分优先
    else:
        best_score = float('inf')
        scored_moves.sort(key=lambda x: x[0]) # Min 玩家，低分优先
    
    # 遍历和递归
    for score_ignored, r, c in scored_moves:
        # 每次遍历新的走法前检查取消请求
        if stop_event is not None and stop_event.is_set():
            raise SearchStopped()
        board[r][c] = current_player
        score = minimax(board, depth - 1, not is_maximizing, alpha, beta, player, stop_event=stop_event)
        board[r][c] = Empty
        
        if is_maximizing:
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if best_score >= beta:
                break  # Beta 剪枝
        else:
            best_score = min(best_score, score)
            beta = min(beta, best_score)
            if best_score <= alpha:
                break  # Alpha 剪枝
    
    return best_score

def find_best_move(board, player, max_depth=3, stop_event=None):
    """
    寻找最佳落子位置。这是 AI 决策的主函数。
    """
    best_score = -float('inf')
    best_move = None
    
    candidate_moves = generate_candidate_moves(board)
    
    # 遍历候选走法，找到分数最高的那个
    for r, c in candidate_moves:
        board[r][c] = player
        # 评估该走法（下一层是对手，所以 is_maximizing=False）
        try:
            score = minimax(board, max_depth - 1, False, -float('inf'), float('inf'), player, stop_event=stop_event)
        except SearchStopped:
            # 搜索被外部取消，返回 None 表示没有决定
            return None

        board[r][c] = Empty # 撤销落子
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    # 安全处理，如果没有找到任何走法，返回第一个候选走法
    if best_move is None and len(candidate_moves) > 0:
         return candidate_moves[0]
            
    return best_move