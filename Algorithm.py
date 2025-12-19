import logic 
import random

#Constants and configuration
BOARD_SIZE = 15
Empty = 0
Black = 1
White = 2

# Search radius around existing pieces
SEARCH_RADIUS = 2 

# Evaluation scores (higher = better)
SCORES = {
    "five": 10000000,      # Five in a row (win)
    "live_four": 100000,   # Open four
    "four_with_gap": 10000, # Four with one gap
    "live_three": 1000,    # Open three
    "three_with_gap": 100,  # Three with one gap
    "live_two": 10,        # Open two
    "two_with_gap": 1      # Two with one gap
}
    
class SearchStopped(Exception):
    #Exception raised when search is cancelled externally
    pass

# --- Board evaluation: core of AI strength ---

def evaluate_board(board, player):
    #Evaluate board advantage for given player
    score = 0
    opponent = White if player == Black else Black
    
    # Player score minus opponent score
    score += evaluate_player(board, player)
    score -= evaluate_player(board, opponent)
    
    return score

def evaluate_player(board, player):
    #Calculate pattern scores for a player
    score = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                score += check_patterns(board, r, c, player)
    return score

def check_patterns(board, r, c, player):
    #Check patterns around a position in all directions
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    total = 0
    for dr, dc in directions:
        line = get_line_pattern(board, r, c, dr, dc, player)
        total += pattern_to_score(line)
    return total

def get_line_pattern(board, r, c, dr, dc, player):
    #Get pattern string along a direction
    pattern = []
    for i in range(-4, 5):
        nr = r + dr * i
        nc = c + dc * i
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr][nc] == player:
                pattern.append(1)  # Player piece
            elif board[nr][nc] == Empty:
                pattern.append(0)  # Empty
            else:
                pattern.append(2)  # Opponent piece
        else:
            pattern.append(3)  # Board edge
    return pattern

def pattern_to_score(pattern):
    #Convert pattern to score using SCORES dictionary
    s = ''.join(map(str, pattern))
    
    # Identify highest scoring patterns
    if '11111' in s: return SCORES["five"]
    if '011110' in s: return SCORES["live_four"]

    # Four with gap
    is_four_with_gap = ('01111' in s or '11110' in s or '10111' in s or '11011' in s or '11101' in s)
    if is_four_with_gap:
         # Simplified boundary check
         if ('01111' in s and '2' in s) or ('11110' in s and '2' in s) or \
            ('01111' in s and '3' in s) or ('11110' in s and '3' in s):
            return SCORES["four_with_gap"]
    
    if '01110' in s: return SCORES["live_three"]
        
    # Three with gap
    if '01112' in s or '21110' in s or '01113' in s or '31110' in s or \
       '1011' in s or '1101' in s or '010110' in s:
        return SCORES["three_with_gap"]
        
    if '0110' in s: return SCORES["live_two"]
        
    if '0112' in s or '2110' in s or '0113' in s or '3110' in s:
        return SCORES["two_with_gap"]
    
    return 0

def is_game_over(board):
    #Check if game has ended (win or draw)
    # Check for winner
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != Empty:
                if logic.check_win(board, r, c, board[r][c]):
                    return True
    
    # Check for draw (full board)
    if logic.is_board_full(board):
        return True
        
    return False

#Optimization: limit search area

def generate_candidate_moves(board):
    
    #Generate candidate moves only around existing pieces
    #Key optimization to reduce search space
    
    candidate_moves = set()
    has_piece = False
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != Empty:
                has_piece = True
                # Check surrounding SEARCH_RADIUS
                for dr in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
                    for dc in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
                        nr, nc = r + dr, c + dc
                        
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == Empty:
                            candidate_moves.add((nr, nc))
                            
    # If board empty, start from center
    if not has_piece:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]

    return list(candidate_moves)

# --- Minimax with Alpha-Beta pruning ---

def minimax(board, depth, is_maximizing, alpha, beta, player, stop_event=None):
    
    #Minimax algorithm with Alpha-Beta pruning
    
    # Cooperative cancellation
    if stop_event is not None and stop_event.is_set():
        raise SearchStopped()

    # Terminal conditions
    if depth == 0 or is_game_over(board):
        return evaluate_board(board, player)

    current_player = player if is_maximizing else (White if player == Black else Black)
    candidate_moves = generate_candidate_moves(board)

    # Move ordering: sort by quick evaluation
    scored_moves = []
    for r, c in candidate_moves:
        board[r][c] = current_player
        score = evaluate_board(board, player) 
        board[r][c] = Empty
        scored_moves.append((score, r, c))

    if is_maximizing:
        best_score = -float('inf')
        scored_moves.sort(key=lambda x: x[0], reverse=True)  # High scores first
    else:
        best_score = float('inf')
        scored_moves.sort(key=lambda x: x[0])  # Low scores first
    
    # Traverse and recurse
    for score_ignored, r, c in scored_moves:
        # Check cancellation before each move
        if stop_event is not None and stop_event.is_set():
            raise SearchStopped()
        board[r][c] = current_player
        score = minimax(board, depth - 1, not is_maximizing, alpha, beta, player, stop_event=stop_event)
        board[r][c] = Empty
        
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

def find_best_move(board, player, max_depth=3, stop_event=None):
    
    #Find best move for AI player
    #Main decision function
    
    best_score = -float('inf')
    best_move = None
    
    candidate_moves = generate_candidate_moves(board)
    
    # Evaluate all candidate moves
    for r, c in candidate_moves:
        board[r][c] = player
        try:
            score = minimax(board, max_depth - 1, False, -float('inf'), float('inf'), player, stop_event=stop_event)
        except SearchStopped:
            # Search cancelled, return None
            return None

        board[r][c] = Empty  # Undo move
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    # Safety: return first move if none found
    if best_move is None and len(candidate_moves) > 0:
         return candidate_moves[0]
            
    return best_move