import re, sys, json, html
src = sys.argv[1]
PAGES = ['index.html','products.html','shipping.html','about_us.html']
TOK = re.compile(r'(<!--.*?-->|<style.*?</style>|<script.*?</script>|<svg.*?</svg>|<[^>]+>)', re.S)
ATTR = re.compile(r'\b(alt|aria-label|content|placeholder|value)="([^"]*)"')
units = []; seen = set()
def add(s, kind):
    k = s.strip()
    if not k or k in seen: return
    if not re.search(r'[A-Za-z]', k): return
    seen.add(k); units.append((kind, k))
for p in PAGES:
    h = open(f'{src}/{p}', encoding='utf-8').read()
    m = re.search(r'<title>(.*?)</title>', h); add(m.group(1), 'title')
    for part in TOK.split(h):
        if part.startswith('<'):
            if part.startswith('<meta') and ('name="description"' in part or 'og:description' in part or 'og:title' in part):
                for a, v in ATTR.findall(part):
                    if a == 'content': add(v, 'meta')
            elif part.startswith('<img') or 'aria-label=' in part:
                for a, v in ATTR.findall(part):
                    if a in ('alt','aria-label'): add(v, a)
            elif part.startswith('<input') and 'name="_subject"' in part:
                for a, v in ATTR.findall(part):
                    if a == 'value': add(v, 'subject')
        else:
            add(part, 'text')
json.dump(units, open(sys.argv[2],'w',encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(units), sum(len(u[1]) for u in units))
