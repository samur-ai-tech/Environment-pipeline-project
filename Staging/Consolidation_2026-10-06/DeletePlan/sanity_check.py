# Read-only sanity check for the delete plan (Consolidation 2026-10-06). Deletes nothing.
# Run: python sanity_check.py   (from any directory)
# Checks, for every line of every DELETE_*.txt (and, separately, OPTIONAL_lifecycle_cook.txt):
#   1. format: UTF-8 without BOM, absolute, forward slashes, no trailing spaces, no comments, path exists;
#   2. the line is not equal to, not an ancestor (prefix) of, and not inside any MUST-STAY path in
#      must_stay_paths.tsv (case-insensitive, whole path components). Only the two named carve-outs apply:
#      except_4km_hda (ModelBank/HDA/GeoCity_city_v015_4km.uasset) and except_blend1 (PE/ModelBank/**/*.blend1);
#   3. no file or folder below a folder line has a hold id (H0013, H0907, H0051, H0958, H0094) in its name;
#   4. no line repeats or nests inside another line, within or across lists.
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
HOLD = re.compile(r'H0013|H0907|H0051|H0958|H0094', re.I)
LISTS = ['DELETE_01_iran.txt', 'DELETE_02_rimal.txt', 'DELETE_03_oldmaps.txt', 'DELETE_04_pe_houdini.txt',
         'DELETE_05_staging.txt', 'OPTIONAL_lifecycle_cook.txt']

def norm(p):
    return p.replace('\\', '/').rstrip('/').lower()

must = []
with open(os.path.join(HERE, 'must_stay_paths.tsv'), encoding='utf-8') as fh:
    next(fh)
    for line in fh:
        p, reason, ex = line.rstrip('\n').split('\t')
        must.append((norm(p), p, reason, ex))

def exception_ok(ex, dpath):
    d = dpath.lower()
    if ex == 'except_4km_hda':
        return d.endswith('/content/project/shared/modelbank/hda/geocity_city_v015_4km.uasset')
    if ex == 'except_blend1':
        return d.endswith('.blend1') and '/integration/before/' not in d and not HOLD.search(d)
    return False

total_fail = 0
all_lines = []
for fn in LISTS:
    path = os.path.join(HERE, fn)
    raw = open(path, 'rb').read()
    fails = []
    if raw.startswith(b'\xef\xbb\xbf'):
        fails.append('BOM present')
    text = raw.decode('utf-8')
    if '\r' in text:
        fails.append('CR line endings')
    lines = [l for l in text.split('\n') if l != '']
    for l in lines:
        if l != l.rstrip() or l.startswith('#') or '\\' in l or not re.match(r'^[A-Z]:/', l):
            fails.append('format: ' + l)
        if not os.path.exists(l):
            fails.append('missing on disk: ' + l)
        d = norm(l)
        for mp, mo, reason, ex in must:
            if d == mp:
                fails.append('EQUALS must-stay [%s]: %s' % (reason, l))
            elif mp.startswith(d + '/'):
                fails.append('ANCESTOR of must-stay [%s] %s: %s' % (reason, mo, l))
            elif d.startswith(mp + '/'):
                if not exception_ok(ex, l):
                    fails.append('INSIDE must-stay [%s] %s: %s' % (reason, mo, l))
        if HOLD.search(os.path.basename(l)):
            fails.append('hold name: ' + l)
        if os.path.isdir(l):
            for root, dirs, files in os.walk(l):
                for n in dirs + files:
                    if HOLD.search(n):
                        fails.append('hold name below folder line: ' + os.path.join(root, n).replace('\\', '/'))
        all_lines.append((fn, l))
    print('%-30s lines=%-5d %s' % (fn, len(lines), 'PASS' if not fails else 'FAIL (%d)' % len(fails)))
    for f in fails[:50]:
        print('    ' + f)
    total_fail += len(fails)

# duplicates / nesting across lists
srt = sorted(all_lines, key=lambda x: norm(x[1]))
nest = []
for i in range(1, len(srt)):
    a, b = norm(srt[i - 1][1]), norm(srt[i][1])
    if b == a or b.startswith(a + '/'):
        nest.append('%s:%s  vs  %s:%s' % (srt[i - 1][0], srt[i - 1][1], srt[i][0], srt[i][1]))
print('cross-list duplicate/nested lines:', 'none' if not nest else len(nest))
for n in nest[:20]:
    print('    ' + n)
total_fail += len(nest)
print('must-stay entries checked:', len(must))
print('RESULT:', 'PASS' if total_fail == 0 else 'FAIL (%d findings)' % total_fail)
sys.exit(0 if total_fail == 0 else 1)
