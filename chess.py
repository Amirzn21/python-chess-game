from dataclasses import dataclass
from typing import List, Optional, Tuple, Iterable

FILE_TO_COL = {c: i for i, c in enumerate("abcdefgh")}
COL_TO_FILE = {i: c for c, i in FILE_TO_COL.items()}

def in_bounds(r, c): return 0 <= r < 8 and 0 <= c < 8
def algebraic_to_rc(s): 
    s = s.strip().lower()
    if len(s) != 2: return None
    if s[0] not in FILE_TO_COL or s[1] not in "12345678": return None
    return (8 - int(s[1]), FILE_TO_COL[s[0]])
def rc_to_algebraic(r, c): return f"{COL_TO_FILE[c]}{8 - r}"

WHITE, BLACK = "W", "B"

@dataclass
class Piece:
    color: str
    def symbol(self): pass
    def is_opponent(self, other): return other is not None and other.color != self.color
    def line_moves(self, board, r, c, deltas):
        moves = []
        for dr, dc in deltas:
            rr, cc = r + dr, c + dc
            while in_bounds(rr, cc):
                t = board.at(rr, cc)
                if t is None: moves.append((rr, cc))
                else:
                    if self.is_opponent(t): moves.append((rr, cc))
                    break
                rr += dr; cc += dc
        return moves
    def pseudo_legal_moves(self, board, r, c): pass

class King(Piece):
    def symbol(self): return "♔" if self.color == WHITE else "♚"
    def pseudo_legal_moves(self, board, r, c):
        m = []
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr == 0 and dc == 0: continue
                rr, cc = r + dr, c + dc
                if in_bounds(rr, cc):
                    t = board.at(rr, cc)
                    if t is None or self.is_opponent(t): m.append((rr, cc))
        return m

class Queen(Piece):
    def symbol(self): return "♕" if self.color == WHITE else "♛"
    def pseudo_legal_moves(self, board, r, c): return self.line_moves(board, r, c, [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)])

class Rook(Piece):
    def symbol(self): return "♖" if self.color == WHITE else "♜"
    def pseudo_legal_moves(self, board, r, c): return self.line_moves(board, r, c, [(-1,0),(1,0),(0,-1),(0,1)])

class Bishop(Piece):
    def symbol(self): return "♗" if self.color == WHITE else "♝"
    def pseudo_legal_moves(self, board, r, c): return self.line_moves(board, r, c, [(-1,-1),(-1,1),(1,-1),(1,1)])

class Knight(Piece):
    def symbol(self): return "♘" if self.color == WHITE else "♞"
    def pseudo_legal_moves(self, board, r, c):
        m = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc):
                t = board.at(rr, cc)
                if t is None or self.is_opponent(t): m.append((rr, cc))
        return m

class Pawn(Piece):
    def symbol(self): return "♙" if self.color == WHITE else "♟"
    def pseudo_legal_moves(self, board, r, c):
        m = []
        d = -1 if self.color == WHITE else 1
        start = 6 if self.color == WHITE else 1
        one = (r + d, c)
        if in_bounds(*one) and board.at(*one) is None:
            m.append(one)
            two = (r + 2*d, c)
            if r == start and in_bounds(*two) and board.at(*two) is None: m.append(two)
        for dc in (-1,1):
            rr, cc = r + d, c + dc
            if in_bounds(rr, cc):
                t = board.at(rr, cc)
                if self.is_opponent(t): m.append((rr, cc))
        return m

class Board:
    def __init__(self):
        self.grid = [[None]*8 for _ in range(8)]
        self.setup_initial()
    def setup_initial(self):
        for c in range(8):
            self.grid[6][c] = Pawn(WHITE)
            self.grid[1][c] = Pawn(BLACK)
        order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for c, cls in enumerate(order):
            self.grid[7][c] = cls(WHITE)
            self.grid[0][c] = cls(BLACK)
    def at(self, r, c): return self.grid[r][c]
    def move(self, src, dst):
        r1, c1 = src; r2, c2 = dst
        p = self.at(r1, c1)
        if p is None: return False, ""
        t = self.at(r2, c2)
        if t is not None and t.color == p.color: return False, ""
        if (r2, c2) not in p.pseudo_legal_moves(self, r1, c1): return False, ""
        self.grid[r2][c2] = p; self.grid[r1][c1] = None
        if isinstance(p, Pawn) and ((p.color == WHITE and r2 == 0) or (p.color == BLACK and r2 == 7)):
            self.grid[r2][c2] = Queen(p.color)
        return True, ""
    def legal_moves_from(self, r, c):
        p = self.at(r, c)
        return p.pseudo_legal_moves(self, r, c) if p else []
    def render(self):
        lines, sep = [], "  +" + "---+"*8
        for r in range(8):
            lines.append(sep)
            row = [self.grid[r][c].symbol() if self.grid[r][c] else " " for c in range(8)]
            lines.append(f"{8 - r} | " + " | ".join(row) + " |")
        lines.append(sep); lines.append("    " + "   ".join("a b c d e f g h".split()))
        return "
".join(lines)

class Game:
    def __init__(self):
        self.board = Board()
        self.turn = WHITE
        self.history = []
        self.running = True
    def other(self, color): return BLACK if color == WHITE else WHITE
    def switch_turn(self): self.turn = self.other(self.turn)
    def input_loop(self):
        print(self.board.render())
        while self.running:
            raw = input(f"{'לבן' if self.turn == WHITE else 'שחור'} >> ").strip()
            if raw in ("quit","exit"): break
            if raw == "board": print(self.board.render()); continue
            if raw == "history":
                for m in self.history: print(m)
                continue
            if raw.startswith("moves "):
                sq = algebraic_to_rc(raw.split()[1])
                if sq is None: continue
                moves = self.board.legal_moves_from(*sq)
                print(", ".join(rc_to_algebraic(r, c) for r, c in moves))
                continue
            parts = raw.split()
            if len(parts) != 2: continue
            src, dst = algebraic_to_rc(parts[0]), algebraic_to_rc(parts[1])
            if src is None or dst is None: continue
            p = self.board.at(*src)
            if p is None or p.color != self.turn: continue
            ok, _ = self.board.move(src, dst)
            if not ok: continue
            self.history.append(f"{parts[0]} -> {parts[1]}")
            print(self.board.render())
            self.switch_turn()

if __name__ == "__main__":
    Game().input_loop()
