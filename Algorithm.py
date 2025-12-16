import logic
import random

# Constants
BOARD_SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2

# Search optimization - only look at positions near existing stones
SEARCH_RADIUS = 2

# Evaluation scores - higher is better
SCORES = {
    "five": 10000000,       # Five in a row 
    "live_four": 100000,    # Open four
    "four_with_gap": 10000, # Four with a gap
    "live_three": 1000,     # Open three
    "three_with_gap": 100,  # Three with a gap
    "live_two": 10,         # Open two
    "two_with_gap": 1       # Two with a gap
}

def evaluate_board(board, player):
    """Evaluate board position from player's perspective."""
    score = 0
    opponent = WHITE if player == BLACK else BLACK
    
    score += evaluate_player(board, player)
    score -= evaluate_player(board, opponent)
    
    return score

def evaluate_player(board, player):
    """Calculate total pattern score for a player."""
    score = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                score += check_patterns(board, r, c, player)
    return score

def check_patterns(board, r, c, player):
    """Check all directions for patterns around a stone."""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    total = 0
    for dr, dc in directions:
        line = get_line_pattern(board, r, c, dr, dc, player)
        total += pattern_to_score(line)
    return total

def get_line_pattern(board, r, c, dr, dc, player):
    """Get pattern representation of a line (9 positions)."""
    pattern = []
    for i in range(-4, 5):
        nr = r + dr * i
        nc = c + dc * i
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr][nc] == player:
                pattern.append(1)
            elif board[nr][nc] == EMPTY:
                pattern.append(0)
            else:
                pattern.append(2)  # Opponent stone
        else:
            pattern.append(3)  # Board edge
    return pattern

def pattern_to_score(pattern):
    """Convert pattern string to score value."""
    s = ''.join(map(str, pattern))
    
    if '11111' in s: 
        return SCORES["five"]
    if '011110' in s: 
        return SCORES["live_four"]
    
    # Four with gap patterns
    if ('01111' in s and '2' in s) or ('11110' in s and '2' in s) or \
       ('01111' in s and '3' in s) or ('11110' in s and '3' in s):
        return SCORES["four_with_gap"]
    
    if '01110' in s: 
        return SCORES["live_three"]
    
    # Three with gap patterns
    if '01112' in s or '21110' in s or '01113' in s or '31110' in s:
        return SCORES["three_with_gap"]
    
    if '0110' in s: 
        return SCORES["live_two"]
    
    # Two with gap patterns
    if '0112' in s or '2110' in s or '0113' in s or '3110' in s:
        return SCORES["two_with_gap"]
    
    return 0

def is_game_over(board):
    """Check if game has ended (win or draw)."""
    # Check for win
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                if logic.check_win(board, r, c, board[r][c]):
                    return True
    
    # Check for draw
    if logic.is_board_full(board):
        return True
        
    return False

def generate_candidate_moves(board):
    """
    Generate possible moves near existing stones.
    Reduces search space significantly.
    """
    candidate_moves = set()
    has_piece = False
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                has_piece = True
                # Look around existing stones
                for dr in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
                    for dc in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                            candidate_moves.add((nr, nc))
    
    # First move - center
    if not has_piece:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
    
    return list(candidate_moves)

def minimax(board, depth, is_maximizing, alpha, beta, player):
    """
    Minimax algorithm with alpha-beta pruning.
    Returns best evaluation score.
    """
    # Terminal conditions
    if depth == 0 or is_game_over(board):
        return evaluate_board(board, player)
    
    current_player = player if is_maximizing else (WHITE if player == BLACK else BLACK)
    candidate_moves = generate_candidate_moves(board)
    
    # Move ordering - improves pruning efficiency
    scored_moves = []
    for r, c in candidate_moves:
        board[r][c] = current_player
        score = evaluate_board(board, player)
        board[r][c] = EMPTY
        scored_moves.append((score, r, c))
    
    # Sort by score (high to low for maximizing, low to high for minimizing)
    if is_maximizing:
        best_score = -float('inf')
        scored_moves.sort(key=lambda x: x[0], reverse=True)
    else:
        best_score = float('inf')
        scored_moves.sort(key=lambda x: x[0])
    
    # Search moves
    for score_ignored, r, c in scored_moves:
        board[r][c] = current_player
        score = minimax(board, depth - 1, not is_maximizing, alpha, beta, player)
        board[r][c] = EMPTY
        
        if is_maximizing:
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if best_score >= beta:
                break  # Beta cut-off
        else:
            best_score = min(best_score, score)
            beta = min(beta, best_score)
            if best_score <= alpha:
                break  # Alpha cut-off
    
    return best_score

def find_best_move(board, player, max_depth=3):
    """
    Find the best move for the given player.
    Main decision function for AI.
    """
    best_score = -float('inf')
    best_move = None
    
    candidate_moves = generate_candidate_moves(board)
    
    # Evaluate each candidate move
    for r, c in candidate_moves:
        board[r][c] = player
        score = minimax(board, max_depth - 1, False, -float('inf'), float('inf'), player)
        board[r][c] = EMPTY
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # Fallback - return first candidate if no move found
    if best_move is None and len(candidate_moves) > 0:
        return candidate_moves[0]
    
    return best_move