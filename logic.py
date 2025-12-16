# Board constants
BOARD_SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2

def initialize_board():
    """Create and return an empty board."""
    board = []
    for _ in range(BOARD_SIZE):
        row = [EMPTY] * BOARD_SIZE
        board.append(row)
    return board

def is_board_full(board):
    """Check if board has no empty spaces."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == EMPTY:
                return False
    return True

def check_win(board, r, c, player):
    """Check if player has won with a move at (r,c)."""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for dr, dc in directions:
        count = 1
        
        # Forward direction
        for i in range(1, 5):
            nr = r + dr * i
            nc = c + dc * i
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                break
            if board[nr][nc] == player:
                count += 1
            else:
                break
        
        # Backward direction
        for i in range(1, 5):
            nr = r - dr * i
            nc = c - dc * i
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                break
            if board[nr][nc] == player:
                count += 1
            else:
                break
        
        if count >= 5:
            return True
    
    return False