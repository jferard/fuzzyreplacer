# Fuzzyreplacer - A fuzzy string replacer in Python
# Copyright (C) 2022 J. Férard <https://github.com/jferard>
# License: GPLv3

import difflib
import re
from typing import Mapping, List, Callable, Optional, Any, ItemsView


Tree = Mapping[str, Optional["Tree"]]


class Match:
    """
    A match
    """
    def __init__(self, i: int, j: int, s: str, score: float):
        """

        :param i: index of first word of match
        :param j: index of last word of match + 1
        :param s: expression to replace the match
        :param score: score of the match
        """
        self.i = i
        self.j = j
        self.s = s
        self.score = score

    def weighted_score(self) -> float:
        """
        :return: the score weighted of the match : len * score
        """
        return self.score * len(self)

    def __len__(self) -> int:
        return self.j - self.i

    def __eq__(self, other: Any) -> bool:
        return (
                isinstance(other, Match)
                and other.i == self.i and other.j == self.j and self.s == other.s
        )

    def __repr__(self) -> str:
        return "Match({}:{}, {}, ws={})".format(self.i, self.j, self.s,
                                                self.weighted_score())


class State:
    """
    Current state in the tree
    """
    def __init__(self, i: int, subtree: Tree, score: float):
        """

        :param i: the start of the match
        :param subtree: the subtree of level 1
        :param score: the score
        """
        self.i = i
        self.subtree = subtree
        self.score = score

    def items(self) -> ItemsView[str, Tree]:
        return self.subtree.items()

    def as_match(self, j: int, s: str) -> "Match":
        """
        :param j: last index
        :param s: the replacement
        :return: a match
        """
        return Match(self.i, j, s, self.score)

    def update(self, subtree: Tree, score: float):
        """
        Advance one step in the tree
        :param subtree: the subtree
        :param score: the next score
        """
        assert subtree is not None
        return State(self.i, subtree, self.score * score)

    def __repr__(self) -> str:
        return "State({}, {})".format(self.i, self.subtree)


def select_matches(matches: List[Match]) -> List[Match]:
    """
    Select the best matches. A match should not overlap another. A match should
    be as long as possible.
    :param matches: the matches
    :return: the selected matches
    """
    if not matches:
        return []

    selected_matches = []
    cur_winner = matches[0]
    for winner in matches[1:]:
        if winner.i == cur_winner.i and winner.weighted_score() > cur_winner.weighted_score():
            cur_winner = winner
        elif winner.i >= cur_winner.j:  # if the match doesn't overlap
            selected_matches.append(cur_winner)
            cur_winner = winner
    selected_matches.append(cur_winner)
    return selected_matches


SPLIT_W_DELIM_REGEX = re.compile(r"(\W+)")
SPLIT_WO_DELIM_REGEX = re.compile(r"\W+")


def dict_to_tree(
        d: Mapping[str, str], func: Callable[[str], str]) -> Tree:
    """
    {"foo bar baz" : bat}
    becomes
    {"foo":{"bar":{"baz":{"bat: None}}}}
    """
    root = {}
    for key, value in d.items():
        cur = root

        for key_chunk in SPLIT_WO_DELIM_REGEX.split(key):
            cur = cur.setdefault(func(key_chunk), {})
        cur[value] = None
    return root


class FuzzyReplacerHelper:
    """
    A helper class.
    """
    def __init__(self, root: Tree,
                 normalize_func: Callable[[str], str], cutoff: float):
        """
        :param root: the tree of expressions
        :param normalize_func: the function to normalize
        :param cutoff: the difflib cutoff
        """
        self._root: Tree = root
        self._normalize = normalize_func
        self._cutoff = cutoff
        self._states = []
        self._matches = []

    def process(self, words: List[str]) -> List[Match]:
        """
        Find the list of matches
        :param words: the words of the text
        :return: the matches
        """
        for i, word in enumerate(words):
            word = self._normalize(word)
            self._consume(i, word)

        for state in self._states:
            for k, v in state.items():
                if v is None:
                    self._matches.append(state.as_match(len(words), k))

        return self._matches

    def _consume(self, i: int, word: str):
        s = difflib.SequenceMatcher()
        s.set_seq2(word)

        cutoff = self._cutoff

        def word_matches(chunk: str) -> Optional[float]:
            """
            Returns the similarity ratio chunk/word or None
            """
            s.set_seq1(chunk)
            if (s.real_quick_ratio() >= cutoff
                    and s.quick_ratio() >= cutoff):
                ratio = s.ratio()
                if ratio >= cutoff:
                    return ratio

            return None

        new_states = []
        # try root
        for word, subtree in self._root.items():
            if subtree is None: # word is a leaf, ie a destination word
                match = Match(i, i + 1, word, 0) # we get a match
                self._matches.append(match)
            else:
                score = word_matches(word)
                if score:
                    new_states.append(State(i, subtree, score))

        # continue where we left
        for state in self._states:
            for word, subtree in state.items():
                if subtree is None:
                    self._matches.append(state.as_match(i, word))
                else:
                    score = word_matches(word)
                    if score:
                        new_states.append(state.update(subtree, score))

        self._states = new_states


class FuzzyReplacer:
    """
    The replacer
    """
    def __init__(self, to_by_from: Mapping[str, str],
                 normalize_func: Optional[Callable[[str], str]] = None,
                 cutoff: float = 0.85):
        """
        :param to_by_from: the mapping (replace key by values)
        :param normalize_func: the function to normalize the keys
        :param cutoff: the difflib cutoff
        """
        if normalize_func is None:
            normalize_func = FuzzyReplacer._default_normalize
        self._root = dict_to_tree(to_by_from, normalize_func)
        self._normalize = normalize_func
        self._cutoff = cutoff

    def process(self, s: str) -> str:
        """
        :param s: the input string
        :return: the output string, with the matches replaced if possible
        """
        words_and_spaces = SPLIT_W_DELIM_REGEX.split(s)
        if not words_and_spaces:
            return s
        else:
            words = words_and_spaces[::2]
            spaces = words_and_spaces[1::2] + ['']

        matches = FuzzyReplacerHelper(self._root, self._normalize,
                                      self._cutoff).process(words)

        if not matches:
            return s

        matches = select_matches(matches)
        for match in reversed(matches):
            words = words[:match.i] + [match.s] + words[match.j:]
            spaces = spaces[:match.i] + spaces[match.j - 1:]

        return "".join(
            [chunk for w_and_s in zip(words, spaces) for chunk in w_and_s]
        )

    @staticmethod
    def _default_normalize(word: str) -> str:
        import unicodedata
        word = unicodedata.normalize(
            'NFKD', word).encode('ascii', 'ignore').decode('ascii',
                                                           'ignore').lower()
        return ''.join([c for c in word if c.isalpha()])


__all__ = ["FuzzyReplacer"]
