# Fuzzyreplacer - A fuzzy string replacer in Python
# Copyright (C) 2022 J. Férard <https://github.com/jferard>
# License: GPLv3

import unittest

from fuzzyreplacer import FuzzyReplacer


class TestFuzzyReplacerCase(unittest.TestCase):
    def simple_test(self):
        text = """The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too."""

        mapping = {"GNU General Public License": "GPL"}

        self.assertEqual("""The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GPL is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GPL for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too.""", FuzzyReplacer(mapping).process(text))

    def test_fuzzy_and_accents(self):
        text = """« GPL » veut dire General Public License (licence publique générale). 
La plus répandue des licences de ce type est la licence publique générale GNU, 
ou GNU GPL pour faire court. On peut raccourcir encore plus en « GPL », 
s'il est entendu qu'il s'agit de la GNU GPL."""

        mapping = {"licence publiqu general": "GPL"}

        self.assertEqual("""« GPL » veut dire General Public License (GPL). 
La plus répandue des licences de ce type est la GPL GNU, 
ou GNU GPL pour faire court. On peut raccourcir encore plus en « GPL », 
s'il est entendu qu'il s'agit de la GNU GPL.""",
                         FuzzyReplacer(mapping).process(text))

    def test_two_matches(self):
        text = """« GPL » veut dire General Public License (licence publique générale). 
La plus répandue des licences de ce type est la licence publique générale GNU, 
ou GNU GPL pour faire court. On peut raccourcir encore plus en « GPL », 
s'il est entendu qu'il s'agit de la GNU GPL."""

        mapping = {"licence publiqu general": "GPL", "licence publique": "PL"}

        self.assertEqual("""« GPL » veut dire General Public License (GPL). 
La plus répandue des licences de ce type est la GPL GNU, 
ou GNU GPL pour faire court. On peut raccourcir encore plus en « GPL », 
s'il est entendu qu'il s'agit de la GNU GPL.""",
                         FuzzyReplacer(mapping).process(text))


if __name__ == '__main__':
    unittest.main()
