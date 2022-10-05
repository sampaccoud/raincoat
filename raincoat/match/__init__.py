"""
All different types of matches.

When coded, every new type of match should be added
in the match_classes list at the end of this file
"""
import logging
from itertools import count

import importlib_metadata

from raincoat.exceptions import NotMatching  # TODO

logger = logging.getLogger(__name__)


class Checker:
    pass


class Match:
    match_type = None  # Will dynamically be given the name of the entrypoint
    checker = NotImplemented

    def __init__(self, filename, lineno):
        self.filename = filename
        self.lineno = lineno

    def __str__(self):
        return "Match in {}:{}".format(self.filename, self.lineno)

    def format(self, message, color):
        message = message.strip()
        result = ""

        result += color["match"](str(self)) + "\n"

        lines = message.splitlines()
        counter = count()

        for line in lines:
            line = line.strip()
            if line:
                result += self.format_line(line, color, next(counter))
                result += "\n"

        return result

    def format_line(self, line, color, i):
        if i == 0:
            line = color["message"](line)
        return line


def match_from_comment(match_type, filename, lineno, **kwargs):
    """
    Indentifies the correct Match subclass and
    creates a match
    """
    try:
        return match_types[match_type](filename, lineno, **kwargs)
    except KeyError:
        raise NotMatching


def check_matches(matches):
    for match_type, matches_for_type in matches.items():
        match_class = match_types[match_type]
        checker = match_class.checker

        if checker is NotImplemented:
            raise NotImplementedError("{} has no checker".format(match_class))

        for difference in checker().check(matches_for_type):
            yield difference


def get_match_entrypoints():
    entry_points = importlib_metadata.entry_points()
    try:
        return entry_points["raincoat.match"]
    except KeyError:
        # The old way of getting entry points was deprecated in importlib_metadata v5.0.0
        return importlib_metadata.entry_points(group='raincoat.match')


def compute_match_types():
    # Even builtin match types are defined using the entry points.
    match_types = {}
    for match_entry_point in get_match_entrypoints():
        match_type = match_entry_point.name
        match_class = match_entry_point.load()
        match_class.match_type = match_type

        if match_type in match_types:
            logger.warning(
                "Several classes registered for the match type {}. "
                "{} will be ignored, {} will be used."
                "".format(match_type, match_class, match_types[match_type])
            )
            continue

        match_types[match_type] = match_class

    return match_types


match_types = compute_match_types()
