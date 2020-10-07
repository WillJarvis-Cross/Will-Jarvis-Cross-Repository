"""CSC148 Assignment 2

=== CSC148 Winter 2020 ===
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
and Jaisie Sin

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, and Jaisie Sin

=== Module Description ===

This file contains the hierarchy of Goal classes.
"""
from __future__ import annotations
import random
from typing import List, Tuple
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> List[Goal]:
    """Return a randomly generated list of goals with length num_goals.

    All elements of the list must be the same type of goal, but each goal
    must have a different randomly generated colour from COLOUR_LIST. No two
    goals can have the same colour.

    Precondition:
        - num_goals <= len(COLOUR_LIST)
    """
    goal_list = []
    col_list = COLOUR_LIST[:]  # don't want to mutate COLOUR_LIST
    if random.random() < 0.5:  # this randomly chooses which goal we are using
        perimeter = True
    else:
        perimeter = False
    for _ in range(num_goals):
        rand_col = random.choice(col_list)
        if perimeter:
            goal_list.append(PerimeterGoal(rand_col))
        else:
            goal_list.append(BlobGoal(rand_col))
        col_list.remove(rand_col)  # so no 2 players have the same colour
    return goal_list


def _flatten(block: Block) -> List[List[Tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j]

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """
    lst = []
    if len(block.children) != 4:  # don't have to recurse here
        for _ in range(2 ** (block.max_depth - block.level)):
            # this for loop creates a 2D list where the length of the list is
            # the same as the length of all the lists inside. The creates a
            # square 2D list where all the values are the same colour

            # this looks complicated but the amount of iterations is 2 to the
            # power of the difference between max_depth and level. For example,
            # if max_depth is 4 and the block is on level 1 then this iterates
            # 8 times
            lst.append([block.colour]*(2 ** (block.max_depth - block.level)))
            # this appends a list of the same colour where the list is the same
            # length as the amount of time the loop iterates
    else:  # recursing!
        child0 = _flatten(block.children[0])
        child1 = _flatten(block.children[1])
        child2 = _flatten(block.children[2])
        child3 = _flatten(block.children[3])

        # adds to the list from left to right
        for i in range(len(child0)):  # adding the left half of the blocks
            lst.append(child1[i] + child2[i])
        for i in range(len(child0)):  # adding the right half of the blocks
            lst.append(child0[i] + child3[i])

    return lst


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def __init__(self, target_colour: Tuple[int, int, int]) -> None:
        """Initialize this goal to have the given target colour.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


def _add_points(i_pos: int, j_pos: int, size: int) -> int:
    """This is a helper function for score in the PerimeterGoal class. It takes
    in a position of the board (i, j) and the size of the board and returns
    a point total where the sides of the board is 1 point and the corners are
    on 2 points.
    """
    points = 0
    if i_pos == j_pos and i_pos in (0, size - 1):  # top left and bottom right
        points += 2  # 2 points for corner points
    elif (i_pos == 0 and j_pos == size - 1) or \
            (j_pos == 0 and i_pos == size - 1):  # top right and bottom left
        points += 2  # 2 points for corner points
    elif i_pos == 0 or j_pos == 0 or i_pos == size - 1 or j_pos == size - 1:
        points += 1  # 1 point for every edge piece
    return points


class PerimeterGoal(Goal):
    """Child class of Goal. This goal awards the most points to the user who
    has the most blocks of their colour on the perimeter of the board. Corner
    pieces are worth double.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    def score(self, board: Block) -> int:
        """returns a point total given a block where 2 points is given for a
        block on the corner of the board and 1 point is given for every edge
        piece
        """
        points = 0
        flat_board = _flatten(board)
        size = len(flat_board)
        for i in range(size):
            for j in range(size):  # iterates through every element
                col = flat_board[i][j]
                if col == self.colour:  # color of the block is the target color
                    points += _add_points(i, j, size)
        return points

    def description(self) -> str:
        """this tells the user what there goal is
        """
        return 'Get ' + colour_name(self.colour) + 'blocks on' \
            ' the sides of the board. Corners are worth double'


def _help_blob_score(current: int, new: int) -> int:
    """Take in 2 integers and return the integer which has a greater value.
    """
    if new >= current:
        return new
    return current


class BlobGoal(Goal):
    """Child class of Goal. This goal awards the most points to the user who
    has the most blocks that are connected.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    def score(self, board: Block) -> int:
        """returns the greatest number of blocks which are connected in board
        """
        best_score = 0
        flat = _flatten(board)

        board_size = len(flat)
        visited = []  # this 2D list represents the blocks which have been
        # checked
        for _ in range(board_size):
            # making every element of visited -1 because they haven't been
            # visited yet
            visited.append([-1] * board_size)
        for i in range(board_size):
            for j in range(board_size):
                if visited[i][j] == -1:  # goes through every non-checked
                    # element
                    new = self._undiscovered_blob_size((i, j), flat, visited)
                    # new is the new score using the position (i, j)
                    best_score = _help_blob_score(best_score, new)
                    # best score is the highest scoring blob
        return best_score

    def _undiscovered_blob_size(self, pos: Tuple[int, int],
                                board: List[List[Tuple[int, int, int]]],
                                visited: List[List[int]]) -> int:
        """Return the size of the largest connected blob that (a) is of this
        Goal's target colour, (b) includes the cell at <pos>, and (c) involves
        only cells that have never been visited.

        If <pos> is out of bounds for <board>, return 0.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure that, in each cell, contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.
        """
        total = 0
        if pos[0] < 0 or pos[0] >= len(board) or \
                pos[1] < 0 or pos[1] >= len(board):  # position out of range
            return 0
        if visited[pos[0]][pos[1]] == -1:  # haven't looked at this position yet
            if board[pos[0]][pos[1]] == self.colour:
                total += 1  # get a point for the current block it's on
                visited[pos[0]][pos[1]] = 1  # this block has now been visited
                pos2 = (pos[0] + 1, pos[1])  # block to the right
                total += self._undiscovered_blob_size(pos2, board, visited)
                pos2 = (pos[0] - 1, pos[1])  # block to the left
                total += self._undiscovered_blob_size(pos2, board, visited)
                pos2 = (pos[0], pos[1] + 1)  # block above
                total += self._undiscovered_blob_size(pos2, board, visited)
                pos2 = (pos[0], pos[1] - 1)  # block below
                total += self._undiscovered_blob_size(pos2, board, visited)

            else:
                # this block is not part of a blob so return 0
                visited[pos[0]][pos[1]] = 0
                return 0

        return total

    def description(self) -> str:
        """this tells the user what there goal is
        """
        return 'Connect as many blocks of ' + colour_name(self.colour) + \
               ' as possible'


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
