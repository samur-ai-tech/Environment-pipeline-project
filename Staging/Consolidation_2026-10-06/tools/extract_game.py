import re, sys
pat = re.compile(rb'/Game/[A-Za-z0-9_/.\-]+')
pat16 = re.compile(rb'(?:/\x00G\x00a\x00m\x00e\x00/\x00)(?:[A-Za-z0-9_/.\-]\x00)+')
out = set()
for fn in sys.argv[1:]:
    data = open(fn, 'rb').read()
    for m in pat.findall(data):
        out.add(m.decode('ascii'))
    for m in pat16.findall(data):
        out.add(m.decode('utf-16-le'))
for p in sorted(out):
    print(p)
