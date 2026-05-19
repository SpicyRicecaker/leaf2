from dataclasses import asdict, dataclass
from types import SimpleNamespace

p = SimpleNamespace()
p.a = "a"
#print(p)

class Q:
    a = 1
    b = 2
    c = 3
q = Q()
print(q.__dict__)

raw_code = """
print(a + b)
print(c)
"""

dont_care = {}
#print(q.a)
exec(raw_code, q.__dict__, dont_care)
