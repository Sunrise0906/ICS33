# test_queens.py
#
# ICS 33 Winter 2026
# Project 0: History of Modern
#
# Unit tests for the QueensState class in "queens.py".
#
# Docstrings are not required in your unit tests, though each test does need to have
# a name that clearly indicates its purpose.  Notice, for example, that the provided
# test method is named "test_queen_count_is_zero_initially" instead of something generic
# like "test_queen_count", since it doesn't entirely test the "queen_count" method,
# but instead focuses on just one aspect of how it behaves.  You'll want to do likewise.

from queens import QueensState, Position, DuplicateQueenError, MissingQueenError
import unittest



class TestQueensState(unittest.TestCase):
    def test_queen_count_is_zero_initially(self):
        state = QueensState(8, 8)
        self.assertEqual(state.queen_count(), 0)

    """ Unit tests for with_queens_added() """
    def test_queen_count_is_one_after_adding_one(self):
        state = QueensState(8, 8)
        new_state = state.with_queens_added([Position(0, 0)])
        self.assertEqual(state.queen_count(), 0)
        self.assertEqual(new_state.queen_count(), 1)

    def test_adding_multiple_queens_accumulates(self):
        state = QueensState(8, 8)
        state1 = state.with_queens_added([Position(0, 0)])
        print(state1.queen_count())
        state2 = state1.with_queens_added([Position(1, 1)])

        self.assertEqual(state.queen_count(), 0)
        self.assertEqual(state1.queen_count(), 1)
        self.assertEqual(state2.queen_count(), 2)

    def test_adding_multiple_queens_once(self):
        state = QueensState(8, 8)
        new_state = state.with_queens_added([Position(0, 0), Position(1, 1)])

        self.assertEqual(state.queen_count(), 0)
        self.assertEqual(new_state.queen_count(), 2)

    def test_adding_duplicate_queen_raises_error(self):
        state = QueensState(8, 8)
        state_with_one = state.with_queens_added([Position(0, 0)])

        with self.assertRaises(DuplicateQueenError) as err:
            state_with_one.with_queens_added([Position(0, 0)])

        msg = str(err.exception)
        self.assertIn('row 0', msg)
        self.assertIn('column 0', msg)


    """ Unite tests for has_queen() """

    def test_has_queen_is_false_on_empty_board(self):
        state = QueensState(8, 8)
        self.assertFalse(state.has_queen(Position(0, 0)))
        self.assertFalse(state.has_queen(Position(3, 4)))

    def test_has_queen_is_true_where_queen_was_added(self):
        state = QueensState(8, 8)
        state1 = state.with_queens_added([Position(2, 3)])

        self.assertTrue(state1.has_queen(Position(2, 3)))

    def test_has_queen_is_false_where_no_queen(self):
        state = QueensState(8, 8)
        state1 = state.with_queens_added([Position(2, 3)])

        self.assertFalse(state1.has_queen(Position(0, 0)))
        self.assertFalse(state1.has_queen(Position(2, 4)))


    """ Unit tests for queens() """

    def test_queens_is_empty_on_new_board(self):
        state = QueensState(8, 8)
        self.assertEqual(state.queens(), [])

    def test_queens_returns_all_positions_where_queens_were_added(self):
        state = QueensState(8, 8)
        state = state.with_queens_added([
            Position(0, 0),
            Position(1, 2),
            Position(3, 4),
        ])

        result = state.queens()

        self.assertEqual(set(result), {
            Position(0, 0),
            Position(1, 2),
            Position(3, 4),
        })

        self.assertEqual(len(result), 3)
        self.assertEqual(state.queen_count(), 3)

    """ Unit tests for with_queens_removed() """

    def test_removing_existing_queen_decreases_count(self):
        state = QueensState(8, 8)
        state = state.with_queens_added([Position(0, 0), Position(1, 1)])

        new_state = state.with_queens_removed([Position(0, 0)])

        self.assertEqual(state.queen_count(), 2)
        self.assertEqual(new_state.queen_count(), 1)

        self.assertFalse(new_state.has_queen(Position(0, 0)))
        self.assertTrue(new_state.has_queen(Position(1, 1)))

    def test_removing_multiple_queens(self):
        state = QueensState(8, 8)
        state = state.with_queens_added([
            Position(0, 0),
            Position(1, 1),
            Position(2, 2),
        ])

        new_state = state.with_queens_removed([Position(0, 0), Position(2, 2)])

        self.assertEqual(new_state.queen_count(), 1)
        self.assertFalse(new_state.has_queen(Position(0, 0)))
        self.assertFalse(new_state.has_queen(Position(2, 2)))
        self.assertTrue(new_state.has_queen(Position(1, 1)))

    def test_removing_missing_queen_raises_error(self):
        state = QueensState(8, 8)
        state = state.with_queens_added([Position(0, 0)])

        with self.assertRaises(MissingQueenError) as err:
            state.with_queens_removed([Position(1, 1)])

        msg = str(err.exception)
        self.assertIn('row 1', msg)
        self.assertIn('column 1', msg)

    """ Unit tests for any_queens_unsafe() """
    def test_any_queens_unsafe_is_false_on_empty_or_single_queen(self):
        empty = QueensState(8, 8)
        self.assertFalse(empty.any_queens_unsafe())

        one = empty.with_queens_added([Position(0, 0)])
        self.assertFalse(one.any_queens_unsafe())

    def test_any_queens_unsafe_true_when_same_row(self):
        state = QueensState(8, 8)
        state = state.with_queens_added([
            Position(0, 0),
            Position(0, 5),
        ])
        self.assertTrue(state.any_queens_unsafe())

    def test_any_queens_unsafe_true_when_same_column(self):
        state = QueensState(8, 8)
        state = state.with_queens_added([
            Position(0, 3),
            Position(5, 3),
        ])
        self.assertTrue(state.any_queens_unsafe())

    def test_any_queens_unsafe_true_when_same_diagonal(self):
        state = QueensState(8, 8)
        state = state.with_queens_added([
            Position(0, 0),
            Position(3, 3),
        ])
        self.assertTrue(state.any_queens_unsafe())

    def test_any_queens_unsafe_false_when_all_safe(self):
        state = QueensState(8, 8)
        state = state.with_queens_added([
            Position(0, 0),
            Position(1, 2),
            Position(2, 4),
        ])
        self.assertFalse(state.any_queens_unsafe())



if __name__ == '__main__':
    unittest.main()
