#!/bin/python3

import threading
from enum import Enum
from typing import List
import random


puzzle_width = 5
puzzle_height = 5
puzzle_no = 0
solutions = []
running = True

# class for non-blocking input
class KeyboardThread(threading.Thread):

    def __init__(self, input_cbk = None, name='keyboard-input-thread'):
        self.input_cbk = input_cbk
        super(KeyboardThread, self).__init__(name=name, daemon=True)
        self.start()

    def run(self):
        while True:
            self.input_cbk(input()) #waits to get input + Return



class Side(Enum):
    TOP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3


class Piece:
    sides: List[int]
    piece_no: int

    def __init__(self, piece_no):
        self.sides = [0] * 4
        self.piece_no = piece_no

    def getPieceNo(self):
        return self.piece_no

    def piece_type(self):
        i = 0
        for side in self.sides:
            if side != 0:
                i += 1
        return i

    def __getitem__(self, key):
        return self.sides[key]


class RPiece:
    piece: Piece
    # rotation is clockwise, quarter turn * int
    rotation: int

    def __init__(self, piece: Piece, rotation: int):
        self.piece = piece
        self.rotation = rotation

    def __getitem__(self, key):
        return self.piece.sides[(key - self.rotation) % 4]

    def getPieceNo(self):
        return self.piece.piece_no

    def turnClockwise(self):
        return type(self)(self.piece, (self.rotation - 1) % 4)


class Edge:
    edge_num: int
    pieces: List[RPiece]

    def __init__(self, edge_num: int):
        self.edge_num = edge_num
        self.pieces = list()


class EdgeList:
    edges: List[Edge]

    def __init__(self):
        self.edges = list()

    def getEdge(self, edge_num: int) -> Edge:
        for edge in self.edges:
            if edge.edge_num == edge_num:
                return edge
        edge = Edge(edge_num)
        self.edges.append(edge)
        return edge


def print_puzzle(pieces: List[Piece | RPiece], orig: List[Piece | RPiece] = None):
    for y in range(puzzle_height):
        if len(pieces) <= y:
            break
        for x in range(puzzle_width):
            if len(pieces) <= y:
                break
            print(f"   {pieces[(y * puzzle_width) + x][Side.TOP.value]: <3}      ", end='')
        print("")
        for x in range(puzzle_width):
            if len(pieces) <= y:
                break
            piece_no = pieces[(y * puzzle_width) + x].getPieceNo()
            if orig is not None:
                piece_no -= orig[(y * puzzle_width) + x].getPieceNo()
            print(f"{pieces[(y * puzzle_width) + x][Side.LEFT.value]: <3}{piece_no : <3}{pieces[(y * puzzle_width) + x][Side.RIGHT.value]: <3}   ", end='')
        print("")
        for x in range(puzzle_width):
            if len(pieces) <= y:
                break
            print(f"   {pieces[(y * puzzle_width) + x][Side.BOTTOM.value]: <3}      ", end='')
        print("\n")
    pass


def get_random_edge_value(remaining_edges: List[int]):
    edges = []
    sum_edges = 0
    for i in range(len(remaining_edges)):
        if remaining_edges[i] != 0:
            edges.append(i)
            sum_edges += remaining_edges[i]
    num = random.randrange(sum_edges)
    for edge in edges:
        num -= remaining_edges[edge]
        if (num < 0):
            return edge


def check_duplicate_solution(a: List[RPiece], b: List[RPiece]):
    for i in range(puzzle_width * puzzle_height):
        if         (a[i][0] != b[i][0]) \
                or (a[i][1] != b[i][1]) \
                or (a[i][2] != b[i][2]) \
                or (a[i][3] != b[i][3]):
            return False
    return True


def check_duplicate_pieces(edges: EdgeList):
    for edge in edges.edges:
        for a in edge.pieces:
            for b in edge.pieces:
                if      a is not b \
                        and a[0] == b[0] \
                        and a[1] == b[1] \
                        and a[2] == b[2] \
                        and a[3] == b[3]:
                    return True
    return False


def check_boring_solution(a: List[RPiece], b: List[RPiece]):
    total_zeros = 0
    for y in range(puzzle_height):
        for x in range(puzzle_width):
            if a[(y * puzzle_width) + x] is b[(y * puzzle_width) + x]:
                total_zeros += 1
            if total_zeros > 2:
                return True
    return False


def solve_puzzle_rerun(pieces: List[Piece], solved: List[RPiece], edges: EdgeList, piece: RPiece):
    new_solved = solved.copy()
    new_pieces = pieces.copy()
    new_solved.append(piece)
    new_pieces.remove(piece.piece)
    solve_puzzle_rec(new_pieces, new_solved, edges)



def solve_puzzle_rec(pieces: List[Piece], solved: List[RPiece], edges: EdgeList):
    global puzzle_width
    global puzzle_height
    global puzzle_no
    global solutions
    #print(f"layer {len(solved)}")
    #print_puzzle(solved)
    if len(solved) == puzzle_width * puzzle_height:
        for solution in solutions:
            if check_duplicate_solution(solution, solved):
                return
        #print("found solution!")
        solutions.append(solved.copy())
        return

    find_top = [False, 0]
    find_left = [False, 0]

    solved_x = len(solved) % puzzle_width

    check_bottom = len(solved) >= puzzle_width * (puzzle_height - 1)
    check_right = solved_x == puzzle_width - 1

    if solved_x > 0: #not left side
        find_left = [True, -(solved[-1][Side.RIGHT.value])]

    if len(solved) >= puzzle_width: #not top
        find_top = [True, -(solved[-puzzle_width][Side.BOTTOM.value])]


    if find_top[0]:
        if find_left[0]:
            for piece in edges.getEdge(find_top[1]).pieces:
                if piece.piece in pieces and \
                        piece[Side.LEFT.value] == find_left[1] and \
                        (check_right == (piece[Side.RIGHT.value] == 0)) and \
                        (check_bottom == (piece[Side.BOTTOM.value] == 0)):
                    solve_puzzle_rerun(pieces, solved, edges, piece)
        else:
            for piece in edges.getEdge(find_top[1]).pieces:
                if piece.piece in pieces and piece[Side.LEFT.value] == 0:
                    solve_puzzle_rerun(pieces, solved, edges, piece)

    else:
        if find_left[0]:
            for piece in edges.getEdge(find_left[1]).pieces:
                piece = piece.turnClockwise()
                if piece.piece in pieces and piece[Side.TOP.value] == 0:
                    solve_puzzle_rerun(pieces, solved, edges, piece)




def get_edges(pieces: List[Piece]) -> EdgeList:
    edges = EdgeList()
    for piece in pieces:
        if piece.sides[0] != 0:
            edge = edges.getEdge(piece.sides[0])
            edge.pieces.append(RPiece(piece, 0))

        if piece.sides[1] != 0:
            edge = edges.getEdge(piece.sides[1])
            edge.pieces.append(RPiece(piece, 3))

        if piece.sides[2] != 0:
            edge = edges.getEdge(piece.sides[2])
            edge.pieces.append(RPiece(piece, 2))

        if piece.sides[3] != 0:
            edge = edges.getEdge(piece.sides[3])
            edge.pieces.append(RPiece(piece, 1))
    return edges




def solve_puzzle(pieces: List[Piece], edges: EdgeList):
    global puzzle_width
    global puzzle_height
    global puzzle_no
    global solutions
    for piece in pieces:
        if piece.piece_type() == 2:

            if piece.sides[0] == 0 and piece.sides[3] == 0:
                rpiece = RPiece(piece, 0)
            elif piece.sides[1] == 0 and piece.sides[0] == 0:
                rpiece = RPiece(piece, 3)
            elif piece.sides[2] == 0 and piece.sides[1] == 0:
                rpiece = RPiece(piece, 2)
            elif piece.sides[3] == 0 and piece.sides[2] == 0:
                rpiece = RPiece(piece, 1)

            solved = [rpiece]
            new_pieces = pieces.copy()
            new_pieces.remove(piece)
            solve_puzzle_rec(new_pieces, solved, edges)
            break


def get_bottom_side(pieces: List[Piece], remaining_edges: List[int], index: int, curr_unique: int):
    global puzzle_width
    global puzzle_height
    global puzzle_no
    global solutions
    if index < (puzzle_height - 1) * puzzle_width:
        for side in range(min(curr_unique + 1, 20)):
            new_unique = False
            if side == curr_unique:
                new_unique = True
                curr_unique += 1
            if remaining_edges[side] < 1:
                continue
            remaining_edges[side] -= 1
            pieces[index].sides[Side.BOTTOM.value] = (side + 1)
            pieces[index + puzzle_width].sides[Side.TOP.value] = -(side + 1)
            solve_all_puzzles(pieces, remaining_edges, index + 1, curr_unique)
            pieces[index].sides[Side.BOTTOM.value] = -(side + 1)
            pieces[index + puzzle_width].sides[Side.TOP.value] = (side + 1)
            solve_all_puzzles(pieces, remaining_edges, index + 1, curr_unique)
            if new_unique:
                curr_unique -= 1
            remaining_edges[side] += 1
    else:
        pieces[index].sides[Side.BOTTOM.value] = 0
        solve_all_puzzles(pieces, remaining_edges, index + 1, curr_unique)


def solve_all_puzzles(pieces: List[Piece], remaining_edges: List[int], index: int, curr_unique: int):
    global puzzle_width
    global puzzle_height
    global puzzle_no
    global solutions
    if index == puzzle_width * puzzle_height:
        if check_duplicate_pieces:
            return
        puzzle_no += 1
        if puzzle_no % 1 == 0:
            print(f"checking puzzle number {puzzle_no}")
            print_puzzle(pieces)
        solve_puzzle(pieces, get_edges(pieces))
        if len(solutions) > 1:
            print("Double solution found!")
            print_puzzle(pieces)
            for index in range(len(solutions)):
                print(f"Solution {index + 1}:")
                print_puzzle(solutions[index])
        solutions = []
        return
    if index % puzzle_width < puzzle_width - 1:
        for side in range(min(curr_unique + 1, 20)):
            new_unique = False
            if side == curr_unique:
                new_unique = True
                curr_unique += 1
            if remaining_edges[side] < 1:
                continue
            remaining_edges[side] -= 1
            pieces[index].sides[Side.RIGHT.value] = (side + 1) #don't forget to set opposite side
            pieces[index + 1].sides[Side.LEFT.value] = -(side + 1)
            get_bottom_side(pieces, remaining_edges, index, curr_unique)
            pieces[index].sides[Side.RIGHT.value] = -(side + 1)
            pieces[index + 1].sides[Side.LEFT.value] = (side + 1)
            get_bottom_side(pieces, remaining_edges, index, curr_unique)
            if new_unique:
                curr_unique -= 1
            remaining_edges[side] += 1
    else:
        pieces[index].sides[Side.RIGHT.value] = 0
        get_bottom_side(pieces, remaining_edges, index, curr_unique)


def get_random_bottom(pieces: List[Piece], remaining_edges: List[int], index: int):
    global puzzle_width
    global puzzle_height
    global puzzle_no
    global solutions
    if index < (puzzle_height - 1) * puzzle_width:
        side = get_random_edge_value(remaining_edges)
        remaining_edges[side] -= 1
        if random.getrandbits(1):
            pieces[index].sides[Side.BOTTOM.value] = (side + 1)
            pieces[index + puzzle_width].sides[Side.TOP.value] = -(side + 1)
            return get_random_puzzle(pieces, remaining_edges, index + 1)
        else:
            pieces[index].sides[Side.BOTTOM.value] = -(side + 1)
            pieces[index + puzzle_width].sides[Side.TOP.value] = (side + 1)
            return get_random_puzzle(pieces, remaining_edges, index + 1)
    else:
        pieces[index].sides[Side.BOTTOM.value] = 0
        return get_random_puzzle(pieces, remaining_edges, index + 1)


def get_random_puzzle(pieces: List[Piece], remaining_edges: List[int], index: int):
    global puzzle_width
    global puzzle_height
    global puzzle_no
    global solutions
    if index == puzzle_width * puzzle_height:
        return pieces
    #print(f"generation depth: {index}")
    if index % puzzle_width < puzzle_width - 1:
        side = get_random_edge_value(remaining_edges)
        remaining_edges[side] -= 1
        if random.getrandbits(1):
            pieces[index].sides[Side.RIGHT.value] = (side + 1) #don't forget to set opposite side
            pieces[index + 1].sides[Side.LEFT.value] = -(side + 1)
            return get_random_bottom(pieces, remaining_edges, index)
        else:
            pieces[index].sides[Side.RIGHT.value] = -(side + 1)
            pieces[index + 1].sides[Side.LEFT.value] = (side + 1)
            return get_random_bottom(pieces, remaining_edges, index)
    else:
        pieces[index].sides[Side.RIGHT.value] = 0
        get_random_bottom(pieces, remaining_edges, index)


def terminate(inp):
    global running
    running = False


def main():
    global puzzle_no
    global solutions

    kthread = KeyboardThread(terminate)

    pieces = [0] * 25
    for index in range(25):
        pieces[index] = Piece(index + 1)
    puzzle_no = 1
    while running:
        get_random_puzzle(pieces, [2] * 20, 0)
        edges = get_edges(pieces)
        if check_duplicate_pieces(edges):
            continue
        # got an interesting puzzle
        if (puzzle_no) % 100000 == 0:
            print(f"Checking puzzle number {puzzle_no}")
        solutions = []
        solve_puzzle(pieces, edges)
        if len(solutions) > 1:
            print(f"Double solution found on puzzle {puzzle_no}!\n")
            if len(solutions) == 2 and check_boring_solution(solutions[0], solutions[1]):
                print(f"Boring solution, skipping")
                continue
            print(f"Solution 1")
            print_puzzle(solutions[0])
            for index in range(1, len(solutions)):
                print(f"Solution {index + 1}:")
                print_puzzle(solutions[index], orig=solutions[0])
        puzzle_no += 1
    print(f"checked {puzzle_no} puzzles")


if __name__ == "__main__":
    main()
