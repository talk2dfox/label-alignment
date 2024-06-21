from pathlib import Path

def test_whereami():
    p = Path()
    current = p.resolve().name
    print(current)
    assert(current=='label-alignment')
# vim: et ai si sts=4   
