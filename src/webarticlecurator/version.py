#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from importlib import metadata

try:
    __version__ = metadata.version('webarticlecurator')
except ModuleNotFoundError:
    __version__ = 'THIS IS NOT A PACKAGE!'


if __name__ == '__main__':
    print(__version__)
