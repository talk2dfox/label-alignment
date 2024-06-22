"""
Test for current working directory when running tests

Copyright (C) 2024-present David C. Fox <talk2dfox@gmail.com>
"""
from pathlib import Path

def test_whereami():
    p = Path()
    current = p.resolve().name
    print(current)
    assert(current=='label-alignment')
# vim: et ai si sts=4   
