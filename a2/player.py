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
Misha Schwartz, and Jaisie Sin.

=== Module Description ===

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import KEY_ACTION, ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE


def create_players(num_human: int, num_random: int, smart_players: List[int]) \
        -> List[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human players, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.
    """
    player_list = []
    goals = generate_goals(num_human + num_random + len(smart_players))
    i = 0
    while i < num_human:  # creates humans first
        player_list.append(HumanPlayer(i, goals[i]))
        i += 1
    while i < num_random + num_human:  # creating random players
        player_list.append((RandomPlayer(i, goals[i])))
        i += 1
    while i < num_random + num_human + len(smart_players):  # smart players
        index = i - num_human - num_random
        player_list.append((SmartPlayer(i, goals[i], smart_players[index])))
        i += 1
    return player_list


def _get_block(block: Block, location: Tuple[int, int], level: int) -> \
        Optional[Block]:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside of it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - 0 <= level <= max_depth
    """
    x_in = block.position[0] <= location[0] < block.position[0] + block.size
    y_in = block.position[1] <= location[1] < block.position[1] + block.size
    if not x_in or not y_in:  # The x or y coordinate is not in range of block
        return None
    elif block.level != level and len(block.children) == 4:
        # This is the case where the we haven't reached the given level but we
        # can still recurse more because the block has children
        if location[0] < block.position[0] + block.size // 2:
            # This is where the the x position is in the left half of the block
            if location[1] < block.position[1] + block.size // 2:
                # the location is within the top left block
                return _get_block(block.children[1], location, level)
            else:  # the location is within the bottom left block
                return _get_block(block.children[2], location, level)
        else:
            # This is where the the x position is in the right half of the block
            if location[1] < block.position[1] + block.size // 2:
                # the location is within the top right block
                return _get_block(block.children[0], location, level)
            else:  # the location is within the bottom right block
                return _get_block(block.children[3], location, level)
    else:
        return block


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    === Public Attributes ===
    id:
        This player's number.
    goal:
        This player's assigned goal for the game.
    """
    id: int
    goal: Goal

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a potential move to make on the game board.

        The move is a tuple consisting of a string, an optional integer, and
        a block. The string indicates the move being made (i.e., rotate, swap,
        or smash). The integer indicates the direction (i.e., for rotate and
        swap). And the block indicates which block is being acted on.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError


def _create_move(action: Tuple[str, Optional[int]], block: Block) -> \
        Tuple[str, Optional[int], Block]:
    return action[0], action[1], block


class HumanPlayer(Player):
    """A human player where the user chooses the moves.
    """
    # === Private Attributes ===
    # _level:
    #     The level of the Block that the user selected most recently.
    # _desired_action:
    #     The most recent action that the user is attempting to do.
    #
    # == Representation Invariants concerning the private attributes ==
    #     _level >= 0
    _level: int
    _desired_action: Optional[Tuple[str, Optional[int]]]

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, self._level)

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level = max(0, self._level - 1)
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            return None
        else:
            move = _create_move(self._desired_action, block)

            self._desired_action = None
            return move


def _get_rand_block(board_copy: Block, col: Tuple[int, int, int]) -> \
        Optional[Tuple[str, Optional[int], Block]]:
    """ This private function is used by generate_move() for both random player
    and smart player. This finds a random action, and a valid block for the
    action.
    """

    num_actions = len(KEY_ACTION)
    rand_num = random.randint(0, num_actions - 2)
    # This will be used to get a random action from the dictionary of actions.
    counter = 0
    action = None

    for key in KEY_ACTION:  # getting the random action
        if counter == rand_num:
            action = KEY_ACTION[key]
            break
        counter += 1

    if action in (ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, SWAP_HORIZONTAL,
                  SWAP_VERTICAL):
        # I put these actions together because they all have the same
        # requirements for the action to work
        new_level = random.randint(0, board_copy.max_depth - 1)
        # The blocks for these actions must have children so a block at
        # max_depth is not possible
        new_block = _find_block(board_copy, new_level, action[0])
        random.shuffle(new_block)
        for possible_block in new_block:
            # returns an action and a block which is viable together
            if len(possible_block.children) == 4:
                return action[0], action[1], possible_block

    elif action == SMASH and board_copy.max_depth > 1:
        # For smash to work, max_depth must be greater than 1
        new_level = random.randint(1, board_copy.max_depth - 1)
        # smash can't be performed on a block at level 0 or max_depth
        new_block = _find_block(board_copy, new_level, action[0])
        random.shuffle(new_block)
        for possible_block in new_block:
            # returns an action and a block which is viable together
            if possible_block.smashable():
                # I'm checking to see if this block is viable for smash() and if
                # it is then I return it
                return action[0], action[1], possible_block
    elif action == COMBINE:
        new_level = board_copy.max_depth - 1
        # combine only works at this level
        new_block = _find_block(board_copy, new_level, action[0])
        random.shuffle(new_block)
        for possible_block in new_block:
            # returns an action and a block which is viable together
            copy = possible_block.create_copy()
            if copy.combine():
                # checking to see of the block is viable for combine()
                return action[0], action[1], possible_block
    elif action == PAINT:
        new_level = board_copy.max_depth
        # only works at max_depth
        new_block = _find_block(board_copy, new_level, action[0])
        random.shuffle(new_block)
        for possible_block in new_block:
            # returns an action and a block which is viable together
            copy = possible_block.create_copy()
            if copy.paint(col):
                # checking to see of the block is viable for paint()
                return action[0], action[1], possible_block
    _get_rand_block(board_copy, col)
    # when no action is returned call the function again
    return None


def _find_block(fake_board: Block, level: int, action: str) -> \
        List[Optional[Block]]:
    """This is a helper method for _get_rand_block(). This returns a list of
    the possible blocks at the given level in the given fake_board. If there is
    no such block at level then return empty list.
    """
    block_list = []
    if fake_board.level == level:
        if action in ('smash', 'paint'):  # these actions require 0 children
            if len(fake_board.children) == 0:
                block_list.append(fake_board)
        else:  # all other actions require 4 children
            if len(fake_board.children) == 4:
                block_list.append(fake_board)
    elif fake_board.level < level and len(fake_board.children) == 4:
        # haven't reached the required level yet so recurse on the children
        block_list.extend(_find_block(fake_board.children[0], level, action))
        block_list.extend(_find_block(fake_board.children[1], level, action))
        block_list.extend(_find_block(fake_board.children[2], level, action))
        block_list.extend(_find_block(fake_board.children[3], level, action))
    return block_list


class RandomPlayer(Player):
    """A random player which chooses completely random moves
    """
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        Player.__init__(self, player_id, goal)
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid, randomly generated move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """

        if not self._proceed:
            return None
        board_copy = board.create_copy()
        new_block = _get_rand_block(board_copy, self.goal.colour)
        # new_block is a tuple of the action string, action int, and the block
        # the action is performed on
        if new_block is None:  # couldn't find a viable action
            return None
        else:
            self._proceed = False  # Must set to False before returning!
            block = _get_block(board, new_block[2].position, new_block[2].level)
            # this block is the same as the block from new_block except it is
            # part of <board>
            return new_block[0], new_block[1], block


class SmartPlayer(Player):
    """A Smart Player which chooses moves which will benefit it
    """
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.
    _proceed: bool
    _difficulty: int

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        Player.__init__(self, player_id, goal)
        self._proceed = False
        self._difficulty = difficulty

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid move by assessing multiple valid moves and choosing
        the move that results in the highest score for this player's goal (i.e.,
        disregarding penalties).

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove

        first_score = self.goal.score(board)  # score before a move is chosen
        best_score = None  # the score of the best performing action
        best = None  # the action which outputs the best score

        for _ in range(self._difficulty):
            board_copy = board.create_copy()
            next_move = _get_rand_block(board_copy, self.goal.colour)
            # next_move is a random move
            if next_move is not None:
                # here I am mutating the copy of the board to see how many
                # points next_move gets
                if next_move[0] == 'rotate':
                    next_move[2].rotate(next_move[1])
                    # next_move[1] is the direction the block is rotating
                elif next_move[0] == 'swap':
                    next_move[2].swap(next_move[1])
                    # next_move[1] is the direction the block is swapping
                elif next_move[0] == 'smash':
                    next_move[2].smash()
                elif next_move[0] == 'combine':
                    next_move[2].combine()
                else:
                    next_move[2].paint(self.goal.colour)

                new_score = self.goal.score(board_copy)
                # new_score is the score after the action is performed
                if best_score is None:
                    # setting a new best_score and best
                    best_score = new_score
                    best = next_move
                elif best is not None and new_score > best_score:
                    # setting a new best_score and best
                    best_score = new_score
                    best = next_move

        self._proceed = False  # Must set to False before returning!
        if best is None or best_score <= first_score:
            # when there is no best score then the player passes
            return PASS[0], PASS[1], board
        else:
            block = _get_block(board, best[2].position, best[2].level)
            # this block is the same as the block from new_block except it is
            # part of <board>
            return best[0], best[1], block


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
