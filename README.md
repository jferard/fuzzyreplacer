# Fuzzyreplacer - A fuzzy string replacer in Python

Copyright (C) 2022 J. Férard <https://github.com/jferard>

License: GPLv3

This is a NIH syndrom.

## Problem
Given :

* a mapping between expressions to find and a replacement expressions,
* a text

Fuzzy search any of the keys of the mapping and replace it by the associated value.

## Algorithm
Very naive algorithm :

First, split the keys into words and build a tree. For instance, the mapping 

    {"A": "0", "A B": "1", "A C": "2"}

produces the tree:

    {"A": {
        "0": None, 
        "B": {"1": None}, 
        "C": {"2": None}
    }

Second, split the text.

Third, process the words one by one and advance if possible in the dict, 
using the `difflib`.

Four, select the best matches and do the replacement. 

## Test

    python3 -m pytest