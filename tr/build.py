import re, sys, json, os, shutil
S = sys.argv[1]
SRC, OUT = f'{S}/pages', f'{S}/out'
MAIN = {'index.html': '', 'products.html': 'products', 'shipping.html': 'shipping', 'about_us.html': 'about_us', 'pay.html': 'pay'}
LANGS = {'es': ('Español', 'Spanish'), 'fr': ('Français', 'French'), 'ar': ('العربية', 'Arabic'), 'ru': ('Русский', 'Russian'), 'pt': ('Português', 'Portuguese'), 'el': ('Ελληνικά', 'Greek'), 'hy': ('Հայերեն', 'Armenian'), 'vi': ('Tiếng Việt', 'Vietnamese'), 'ms': ('Bahasa Melayu', 'Malay'), 'th': ('ไทย', 'Thai'), 'sw': ('Kiswahili', 'Swahili'), 'af': ('Afrikaans', 'Afrikaans'), 'am': ('አማርኛ', 'Amharic'), 'ha': ('Hausa', 'Hausa'), 'id': ('Bahasa Indonesia', 'Indonesian'), 'tr': ('Türkçe', 'Turkish'), 'bn': ('বাংলা', 'Bengali'), 'tl': ('Filipino', 'Filipino'), 'pl': ('Polski', 'Polish'), 'uk': ('Українська', 'Ukrainian'), 'it': ('Italiano', 'Italian'), 'de': ('Deutsch', 'German'), 'fa': ('فارسی', 'Persian'), 'ko': ('한국어', 'Korean'), 'ja': ('日本語', 'Japanese'), 'uz': ('Oʻzbekcha', 'Uzbek'), 'az': ('Azərbaycanca', 'Azerbaijani'), 'km': ('ខ្មែរ', 'Khmer'), 'lo': ('ລາວ', 'Lao'), 'my': ('မြန်မာ', 'Burmese')}
RTL = {'ar': ('IBM+Plex+Sans+Arabic:wght@400;500;600;700', "'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, 'Noto Sans Arabic', sans-serif"), 'fa': ('Vazirmatn:wght@400;500;600;700;800', "'Vazirmatn', 'Segoe UI', Tahoma, 'Noto Sans Arabic', sans-serif")}
BASE = 'https://www.lpgpumps.in'
units = json.load(open(f'{S}/tr/units.json', encoding='utf-8'))
PHONE = '⁦+91 89207 83083⁩'
def load(lang):
    d = {}
    for line in open(f'{S}/tr/{lang}.tsv', encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip(): continue
        i, t = line.split('\t', 1)
        if lang in RTL: t = t.replace('{PHONE}', PHONE)
        if lang == 'fr':
            t = re.sub(r' ([?!:;])', ' \\1', t); t = t.replace('« ', '« ').replace(' »', ' »').replace(' %', ' %')
        d[units[int(i)][1]] = t
    return d
TOK = re.compile(r'(<!--.*?-->|<style.*?</style>|<script.*?</script>|<svg.*?</svg>|<[^>]+>)', re.S)
ARABIC = re.compile(r'[؀-ۿ]')
KEEP = {'Telegram @lpgpumps', 'Telegram', '@lpgpumps', 'YAM', 'info@wingz.in', 'PayPal', 'EMS Speed Post', 'WhatsApp / Viber', 'lpgpumps.in · propanepumps.in', 'WhatsApp +91 89207 83083', 'Web', 'Motor', 'Manual', 'Contact', 'FAQ', 'Message', '1 HP', 'Carton'}
missing = {}
def tr_text(s, d, lang):
    k = s.strip()
    if not k: return s
    lead, trail = s[:len(s) - len(s.lstrip())], s[len(s.rstrip()):]
    if k in d: out = d[k]
    else:
        out = k
        if re.search(r'[A-Za-z]', k) and k not in KEEP: missing.setdefault(lang, set()).add(k)
    if lang in RTL and not ARABIC.search(out) and re.search(r'\d\S*\s+\S*\d|^[+≈]', out):
        out = '⁦' + out + '⁩'
    return lead + out + trail
def tr_attr(tag, names, d, lang):
    def rep(m):
        if m.group(1) not in names: return m.group(0)
        v = m.group(2)
        if v in d: return f'{m.group(1)}="{d[v]}"'
        if re.search(r'[A-Za-z]', v) and v not in KEEP: missing.setdefault(lang, set()).add(v)
        return m.group(0)
    return re.sub(r'\b(alt|aria-label|content)="([^"]*)"', rep, tag)
def url(lang, path):
    p = f'/{lang}/' if lang else '/'
    return BASE + p + path
NAMES = dict([('', 'English')] + [(k, v[0]) for k, v in LANGS.items()])
GLOBE = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.8 3 2.8 15 0 18M12 3c-2.8 3-2.8 15 0 18"/></svg>'
def switcher(cur, path, rtl=False):
    links = []
    for code, name in NAMES.items():
        href = (f'/{code}/' if code else '/') + (path or '')
        on = code == cur
        st = 'color: #FFFFFF; font-weight: 500; text-decoration: underline' if on else 'color: #C9D1D6; text-decoration: none'
        links.append(f'<a href="{href}" lang="{code or "en"}" hreflang="{code or "en"}" dir="auto" style="{st}; display: inline-flex; align-items: center; min-height: 40px"{" aria-current=\"page\"" if on else ""}>{name}</a>')
    return ('<details style="max-width: 100%"><summary style="cursor: pointer; display: inline-flex; align-items: center; gap: 8px; min-height: 44px; color: #FFFFFF; font-weight: 500; list-style: none">' + GLOBE
            + f'<span lang="{cur or "en"}">{NAMES[cur]}</span><span aria-hidden="true">&#9662;</span></summary>'
            + '<nav aria-label="Language" style="display: flex; flex-wrap: wrap; gap: 0 20px; padding: 2px 0 10px; max-width: 760px">' + ''.join(links) + '</nav></details>')
BAR = re.compile(r'(<div style="padding: 10px 0">[^<]*</div>)\s*')
def add_switcher(h, cur, path):
    h2, n = BAR.subn(lambda m: m.group(1) + '\n' + switcher(cur, path) + '\n', h, count=1); assert n == 1
    return h2
LANDING = {'tr':'turkey','id':'indonesia','ha':'nigeria','am':'ethiopia','bn':'bangladesh','pl':'poland','uk':'ukraine','tl':'philippines','vi':'vietnam','es':'peru','fr':'mauritius','th':'thailand','sw':'kenya','af':'south-africa'}
NEWC = {'turkey':'Turkey','indonesia':'Indonesia','nigeria':'Nigeria','ethiopia':'Ethiopia','bangladesh':'Bangladesh','poland':'Poland','ukraine':'Ukraine','philippines':'Philippines','vietnam':'Vietnam'}
FOOT = re.compile(r'(<a href="/lpg-pump-kenya" (style="color: #B4BDC3[^"]*")>[^<]*</a>)')
def head_links(h, lang, path, codes=None):
    alts = ''.join(f'<link rel="alternate" hreflang="{c or "en"}" href="{url(c, path)}">\n' for c in (codes if codes is not None else [''] + list(LANGS))) + f'<link rel="alternate" hreflang="x-default" href="{url("", path)}">\n'
    h2, n = re.subn(r'<link rel="canonical" href="[^"]*">\n', f'<link rel="canonical" href="{url(lang, path)}">\n' + alts, h, count=1); assert n == 1
    return h2
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(SRC, OUT)
# English pages: switcher + hreflang on main pages; switcher only on landing pages
for f in sorted(os.listdir(SRC)):
    if not f.endswith('.html'): continue
    h = open(f'{SRC}/{f}', encoding='utf-8').read()
    if f in MAIN:
        h = head_links(add_switcher(h, '', MAIN[f]), '', MAIN[f])
    else:
        h = add_switcher(h, '', '')
        slug = f[len('lpg-pump-'):-5]
        loc = [l for l, s in LANDING.items() if s == slug]
        if loc: h = head_links(h, '', f[:-5], ['', loc[0]])
    h, n = FOOT.subn(lambda m: m.group(1) + ''.join(f'<a href="/lpg-pump-{s}" {m.group(2)}>{nm}</a>' for s, nm in NEWC.items()), h); assert n == 1, f
    open(f'{OUT}/{f}', 'w', encoding='utf-8').write(h)
for lang, (lname, ename) in LANGS.items():
    d = load(lang); os.makedirs(f'{OUT}/{lang}')
    d.update(json.load(open(f'{S}/tr/pay/{lang}.json', encoding='utf-8')))
    todo = dict(MAIN)
    if lang in LANDING:
        ld = json.load(open(f'{S}/tr/landing/{lang}.json', encoding='utf-8'))
        if lang == 'fr': ld = {k: re.sub(r' ([?!:;])', '\u00a0\\1', v) for k, v in ld.items()}
        d.update(ld); todo[f'lpg-pump-{LANDING[lang]}.html'] = f'lpg-pump-{LANDING[lang]}'
    for f, path in todo.items():
        landing = f not in MAIN
        h = open(f'{SRC}/{f}', encoding='utf-8').read()
        parts = TOK.split(h); out = []
        for part in parts:
            if part.startswith('<'):
                if part.startswith('<meta') and re.search(r'name="description"|og:description|og:title', part): part = tr_attr(part, {'content'}, d, lang)
                elif part.startswith('<img') or 'aria-label=' in part: part = tr_attr(part, {'alt', 'aria-label'}, d, lang)
                out.append(part)
            else: out.append(tr_text(part, d, lang))
        h = ''.join(out)
        t = re.search(r'<title>(.*?)</title>', open(f'{SRC}/{f}', encoding='utf-8').read()).group(1)
        h = re.sub(r'<title>.*?</title>', lambda m: '<title>' + d[t] + '</title>', h, count=1)
        # internal links
        h = re.sub(r'href="/((?:products|shipping|about_us|pay)?)((?:#[^"]*)?)"', lambda m: f'href="/{lang}/{m.group(1)}{m.group(2)}"', h)
        h = h.replace(f'value="{BASE}/about_us#contact"', f'value="{BASE}/{lang}/about_us#contact"')
        h = h.replace('value="New enquiry from lpgpumps.in"', f'value="New enquiry from lpgpumps.in ({ename} page)"')
        if lang in LANDING:
            s = LANDING[lang]
            h = h.replace(f'href="/lpg-pump-{s}"', f'href="/{lang}/lpg-pump-{s}"')
            if s in NEWC: h, n = FOOT.subn(lambda m: m.group(1) + f'<a href="/{lang}/lpg-pump-{s}" {m.group(2)}>{d[NEWC[s]]}</a>', h); assert n == 1
        h = add_switcher(h, lang, '' if landing else path); h = head_links(h, lang, path, ['', lang] if landing else None)
        if lang in RTL:
            h = h.replace('<html lang="en">', f'<html lang="{lang}" dir="rtl">')
            h = h.replace('display=swap">', 'display=swap">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=' + RTL[lang][0] + '&display=swap">', 1)
            a, b = h.index('<body>'), h.index('</body>')
            body = h[a:b]
            body = body.replace('text-align: left', 'text-align: @@R').replace('text-align: right', 'text-align: left').replace('text-align: @@R', 'text-align: right')
            body = body.replace('padding: 22px 24px 22px 0', 'padding: 22px 0 22px 24px')
            body = re.sub(r'letter-spacing: [^;"]+(; )?', '', body)
            body = re.sub(r'line-height: 1\.[01]\d?(?=[;"])', 'line-height: 1.4', body)
            body = re.sub(r"font-family: [^;\"]+", "font-family: " + RTL[lang][1], body)
            h = h[:a] + body + h[b:]
        else:
            h = h.replace('<html lang="en">', f'<html lang="{lang}">')
            if lang == 'el':
                h = h.replace('display=swap">', 'display=swap">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Roboto+Mono:wght@400;500&display=swap">', 1)
                h = h.replace("font-family: 'Archivo', sans-serif", "font-family: 'Manrope', 'Segoe UI', Arial, sans-serif")
                h = h.replace("font-family: 'IBM Plex Mono', monospace", "font-family: 'Roboto Mono', 'IBM Plex Mono', monospace")
            if lang == 'hy':
                h = h.replace('display=swap">', 'display=swap">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+Armenian:wght@400;500;600;700;800&display=swap">', 1)
                a, b = h.index('<body'), h.index('</body>')
                h = h[:a] + re.sub(r"font-family: [^;\"]+", "font-family: 'Noto Sans Armenian', 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif", h[a:b]) + h[b:]
            FULL = {'th': ('IBM+Plex+Sans+Thai:wght@400;500;600;700', "'IBM Plex Sans Thai', 'Leelawadee UI', Tahoma, sans-serif"),
                    'am': ('Noto+Sans+Ethiopic:wght@400;500;600;700;800', "'Noto Sans Ethiopic', 'Nyala', 'IBM Plex Sans', sans-serif"),
                    'bn': ('Noto+Sans+Bengali:wght@400;500;600;700;800', "'Noto Sans Bengali', 'Nirmala UI', 'IBM Plex Sans', sans-serif"),
                    'ko': ('Noto+Sans+KR:wght@400;500;700;800', "'Noto Sans KR', 'Malgun Gothic', sans-serif"),
                    'ja': ('Noto+Sans+JP:wght@400;500;700;800', "'Noto Sans JP', 'Yu Gothic', 'Hiragino Sans', sans-serif"),
                    'km': ('Noto+Sans+Khmer:wght@400;500;600;700;800', "'Noto Sans Khmer', 'Khmer OS', 'Leelawadee UI', sans-serif"),
                    'lo': ('Noto+Sans+Lao:wght@400;500;600;700;800', "'Noto Sans Lao', 'Phetsarath OT', 'Leelawadee UI', sans-serif"),
                    'my': ('Noto+Sans+Myanmar:wght@400;500;600;700;800', "'Noto Sans Myanmar', 'Myanmar Text', 'Padauk', sans-serif"),
                    'ha': ('Noto+Sans:wght@400;500;600;700;800', "'Noto Sans', 'Segoe UI', Arial, sans-serif")}
            if lang in FULL:
                fam, stack = FULL[lang]
                h = h.replace('display=swap">', f'display=swap">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={fam}&display=swap">', 1)
                a, b2 = h.index('<body'), h.index('</body>')
                body = re.sub(r"font-family: [^;\"]+", "font-family: " + stack, h[a:b2])
                if lang in ('km', 'lo', 'my'):
                    body = re.sub(r'line-height: 1\.(?:5|55)(?=[;"])', 'line-height: 1.8', body)
                    body = re.sub(r'line-height: 1(?:\.[0-2]\d?)?(?=[;"])', 'line-height: 1.45', body)
                elif lang in ('th', 'am', 'bn', 'ko', 'ja'):
                    body = re.sub(r'line-height: 1\.[01]\d?(?=[;"])', 'line-height: 1.3', body)
                h = h[:a] + body + h[b2:]
                if lang in ('km', 'lo', 'my'):
                    h = h.replace('body{margin:0}', 'body{margin:0;overflow-wrap:anywhere}', 1)
            if lang in ('ru', 'uk'):
                h = h.replace('display=swap">', 'display=swap">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@500;600;700;800&display=swap">', 1)
                h = h.replace("font-family: 'Archivo', sans-serif", "font-family: 'Golos Text', 'Archivo', 'Segoe UI', Arial, sans-serif")
        open(f'{OUT}/{lang}/{f}', 'w', encoding='utf-8').write(h)
# sitemap
sm = open(f'{OUT}/sitemap.xml', encoding='utf-8').read()
extra = ''.join(f'<url><loc>{url(l, p)}</loc></url>\n' for l in LANGS for p in MAIN.values()) + ''.join(f'<url><loc>{url(l, "lpg-pump-" + s)}</loc></url>\n' for l, s in LANDING.items())
open(f'{OUT}/sitemap.xml', 'w', encoding='utf-8').write(sm.replace('</urlset>', extra + '</urlset>'))
for l, m in missing.items(): print('MISSING', l, len(m), sorted(m)[:40])
print('built', sum(len(fs) for _, _, fs in os.walk(OUT)), 'files')
