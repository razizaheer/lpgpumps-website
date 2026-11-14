"""Build one A4 PDF flyer per pump model, in every site language.

Usage: python3 tr/flyers.py <repo> [lang ...]
Writes pages/flyers/<lang>/<model>.pdf (English under pages/flyers/en/).
Model text comes straight from pages/products.html and its translations
(tr/units.json + tr/<lang>.tsv); flyer-only lines come from tr/flyers.json.
The QR code opens a WhatsApp chat with a prefilled message naming the flyer.
"""
import sys, os, re, io, json, html, base64
from urllib.parse import quote
import segno
from PIL import Image
from playwright.sync_api import sync_playwright

R = sys.argv[1]
A = os.path.join(R, 'pages', 'assets')
OUTROOT = os.path.join(R, 'pages', 'flyers')
EMAIL = 'info@wingz.in'
WA = 'https://wa.me/918920783083'
LANGS = ['es', 'fr', 'ar', 'ru', 'pt', 'el', 'hy', 'vi', 'ms', 'th', 'sw', 'af', 'am', 'ha', 'id', 'tr', 'bn', 'tl', 'pl', 'uk',
         'it', 'de', 'fa', 'ko', 'ja', 'uz', 'az', 'km', 'lo', 'my']
LANG_EN = {'es': 'Spanish', 'fr': 'French', 'ar': 'Arabic', 'ru': 'Russian', 'pt': 'Portuguese', 'el': 'Greek', 'hy': 'Armenian',
           'vi': 'Vietnamese', 'ms': 'Malay', 'th': 'Thai', 'sw': 'Swahili', 'af': 'Afrikaans', 'am': 'Amharic', 'ha': 'Hausa',
           'id': 'Indonesian', 'tr': 'Turkish', 'bn': 'Bengali', 'tl': 'Filipino', 'pl': 'Polish', 'uk': 'Ukrainian', 'it': 'Italian',
           'de': 'German', 'fa': 'Persian', 'ko': 'Korean', 'ja': 'Japanese', 'uz': 'Uzbek', 'az': 'Azerbaijani', 'km': 'Khmer',
           'lo': 'Lao', 'my': 'Burmese'}
RTL = {'ar', 'fa'}
BASE_FONTS = 'family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600'
# lang -> (extra Google family, stack for everything or None, heading stack or None, mono stack or None)
FONTS = {
    'ar': ('IBM+Plex+Sans+Arabic:wght@400;500;600;700', "'IBM Plex Sans Arabic', sans-serif", None, None),
    'fa': ('Vazirmatn:wght@400;500;600;700;800', "'Vazirmatn', sans-serif", None, None),
    'th': ('IBM+Plex+Sans+Thai:wght@400;500;600;700', "'IBM Plex Sans Thai', sans-serif", None, None),
    'am': ('Noto+Sans+Ethiopic:wght@400;500;600;700;800', "'Noto Sans Ethiopic', 'IBM Plex Sans', sans-serif", None, None),
    'bn': ('Noto+Sans+Bengali:wght@400;500;600;700;800', "'Noto Sans Bengali', 'IBM Plex Sans', sans-serif", None, None),
    'ko': ('Noto+Sans+KR:wght@400;500;700;800', "'Noto Sans KR', sans-serif", None, None),
    'ja': ('Noto+Sans+JP:wght@400;500;700;800', "'Noto Sans JP', sans-serif", None, None),
    'km': ('Noto+Sans+Khmer:wght@400;500;600;700;800', "'Noto Sans Khmer', sans-serif", None, None),
    'lo': ('Noto+Sans+Lao:wght@400;500;600;700;800', "'Noto Sans Lao', sans-serif", None, None),
    'my': ('Noto+Sans+Myanmar:wght@400;500;600;700;800', "'Noto Sans Myanmar', sans-serif", None, None),
    'ha': ('Noto+Sans:wght@400;500;600;700;800', "'Noto Sans', sans-serif", None, None),
    'hy': ('Noto+Sans+Armenian:wght@400;500;600;700;800', "'Noto Sans Armenian', 'IBM Plex Sans', sans-serif", None, None),
    'el': ('Manrope:wght@500;600;700;800&family=Roboto+Mono:wght@400;500', None, "'Manrope', sans-serif", "'Roboto Mono', monospace"),
    'ru': ('Golos+Text:wght@500;600;700;800', None, "'Golos Text', 'Archivo', sans-serif", None),
    'uk': ('Golos+Text:wght@500;600;700;800', None, "'Golos Text', 'Archivo', sans-serif", None),
}
TALL = {'km', 'lo', 'my'}
STR_KEYS = ['Specifications', 'Scan to message us on WhatsApp', 'Filling a car’s LPG tank from a cylinder',
            'Moving gas from a big cylinder to a smaller one', 'Spare parts are supplied with every pump',
            'The manual pump in use: no electricity needed', 'Download flyer (PDF)']
MODELS = [
    dict(id='dc12', file='yam-12v-dc-lpg-pump', short='12V DC pump', img='pump-12v-dc.jpg', use='use-car-filling.jpg',
         cap='Filling a car’s LPG tank from a cylinder'),
    dict(id='ac220', file='yam-220v-ac-lpg-pump', short='220V AC pump', img='pump-220v-ac.jpg', use='use-cylinder-to-cylinder.jpg',
         cap='Moving gas from a big cylinder to a smaller one'),
    dict(id='commercial', file='yam-1hp-commercial-lpg-pump', short='1 HP commercial pump', img='pump-1hp-commercial.jpg',
         use='use-cylinder-to-cylinder.jpg', cap='Moving gas from a big cylinder to a smaller one'),
    dict(id='belt', file='yam-1hp-belt-drive-lpg-pump', short='1 HP belt-drive pump', img='pump-1hp-belt-drive.jpg',
         use='parts-and-spares.jpg', cap='Spare parts are supplied with every pump'),
    dict(id='manual', file='yam-manual-lpg-pump', short='manual pump', img='pump-manual.jpg', use='poster-manual.jpg',
         cap='The manual pump in use: no electricity needed', use_pos='50% 78%'),
]

units = json.load(open(os.path.join(R, 'tr', 'units.json'), encoding='utf-8'))
FLY = json.load(open(os.path.join(R, 'tr', 'flyers.json'), encoding='utf-8'))
U = html.unescape


def load(lang):
    if not lang:
        return {}
    d = {}
    for line in open(os.path.join(R, 'tr', f'{lang}.tsv'), encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip():
            continue
        i, t = line.split('\t', 1)
        d[U(units[int(i)][1])] = U(t)
    return d


def model_text():
    """Pull eyebrow, title, description and specs of each model from products.html."""
    h = open(os.path.join(R, 'pages', 'products.html'), encoding='utf-8').read()
    out = {}
    for m in MODELS:
        i = h.index(f'id="{m["id"]}"')
        s = h[i:h.index('</section>', i)]
        txt = lambda pat: [U(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(pat, s, re.S)]
        spans = re.findall(r'<div[^>]*>(<span[^>]*>.*?</span>(?:<span[^>]*>.*?</span>)?)</div>\s*<h2', s, re.S)[0]
        eyebrow = [U(x).strip() for x in re.findall(r'<span[^>]*>(.*?)</span>', spans)]
        pairs = re.findall(r'<div[^>]*><span[^>]*>([^<]*)</span><span[^>]*>([^<]*)</span></div>', s)
        out[m['id']] = dict(eyebrow=eyebrow, title=txt(r'<h2[^>]*>(.*?)</h2>')[0], desc=txt(r'<p[^>]*>(.*?)</p>')[0],
                            specs=[(U(k).strip(), U(v).strip()) for k, v in pairs if U(k).strip() not in eyebrow])
    return out


def jpeg_uri(name, w=1100):
    im = Image.open(os.path.join(A, name)).convert('RGB')
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, 'JPEG', quality=80, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()


def svg_uri(name):
    return 'data:image/svg+xml;base64,' + base64.b64encode(open(os.path.join(A, name), 'rb').read()).decode()


def wa_url(m, lang):
    where = m['short'] + (', ' + LANG_EN[lang] if lang else '')
    return WA + '?text=' + quote(f'Hello, I found you on your flyer ({where}). Please send me the price of a pump.')


def qr_svg(url):
    return segno.make(url, error='m').svg_data_uri(scale=6, border=0, dark='#0F1419')


CSS = """
@page { size: A4; margin: 0 }
* { box-sizing: border-box }
html, body { margin: 0; padding: 0 }
html { width: 210mm; height: 297mm; overflow: hidden }
body { width: 210mm; height: 296.5mm; font-family: @BODY; color: #0F1419; background: #FFFFFF;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; overflow: hidden; display: flex; flex-direction: column }
.head { display: flex; align-items: center; justify-content: space-between; padding: 10mm 14mm 5mm; gap: 8mm }
.head img { height: 13mm }
.head .r { text-align: end; font-size: 8.5pt; color: #3A444D; line-height: 1.5; max-width: 110mm }
.head .r b { font-family: @HEAD; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #0F1419; font-size: 9pt }
.rule { height: 1.2mm; background: #1747D1; margin: 0 14mm }
.hero { padding: 6mm 14mm 0 }
.eyebrow { font-family: @MONO; font-size: 9pt; letter-spacing: .14em; text-transform: uppercase; color: #1747D1 }
h1 { font-family: @HEAD; font-weight: 800; font-size: 26pt; line-height: 1.08; letter-spacing: -.01em; margin: 2mm 0 2.5mm }
.desc { font-size: 10pt; line-height: 1.5; color: #3A444D; margin: 0; max-width: 175mm }
.photo { margin: 4.5mm 14mm 0; height: 70mm; border: 0.3mm solid #C9CFC8; border-radius: 3mm; background: #FFFFFF; display: flex; align-items: center; justify-content: center; overflow: hidden; flex-shrink: 0 }
.photo img { max-width: 100%; max-height: 100%; object-fit: contain }
.mid { display: flex; gap: 7mm; padding: 5mm 14mm 0; align-items: flex-start }
.specs { flex: 1.35 }
.specs h2 { font-family: @HEAD; font-weight: 700; font-size: 11.5pt; margin: 0 0 2mm }
table { width: 100%; border-collapse: collapse; font-size: 9.5pt }
td { padding: 1.4mm 0; border-top: 0.25mm solid #D5DAD4; vertical-align: top; text-align: start }
td.k { font-family: @MONO; color: #3A444D; width: 40%; padding-inline-end: 3mm }
td.v { font-weight: 600 }
.side { flex: 1 }
.side .use { width: 100%; aspect-ratio: 3 / 2; object-fit: cover; border-radius: 2mm; border: 0.25mm solid #D5DAD4; display: block; background: #FFF }
.side .cap { font-size: 8.5pt; color: #3A444D; margin-top: 1.5mm; line-height: 1.4 }
.every { margin: 4.5mm 14mm 0; padding: 3.5mm 5mm; list-style: none; font-size: 9pt; line-height: 1.45; background: #F3F4F1; border-radius: 2mm; display: flex; gap: 8mm }
.every li { padding-inline-start: 5mm; position: relative }
.every li:first-child { flex: 1 }
.every li:last-child { white-space: nowrap; font-weight: 600 }
.every li:before { content: ''; position: absolute; inset-inline-start: 0; top: 1.3mm; width: 2.4mm; height: 2.4mm; border-radius: 50%; background: #1747D1 }
.contact { margin: auto 14mm 0; background: #0F1419; color: #FFFFFF; border-radius: 3mm;
           display: flex; align-items: center; gap: 8mm; padding: 5mm 7mm }
.contact .l { flex: 1; min-width: 0 }
.contact .ask { font-family: @HEAD; font-weight: 700; font-size: 14pt; margin: 0 0 1mm }
.contact .reply { font-size: 9pt; color: #C9CFC8; margin: 0 0 2.5mm }
.contact .row { display: flex; align-items: baseline; gap: 3mm; margin-top: 1.4mm }
.contact .lab { font-family: @MONO; font-size: 7.5pt; letter-spacing: .12em; text-transform: uppercase; color: #9FB4FF; width: 22mm; flex-shrink: 0 }
.contact .site { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 19pt; color: #FFFFFF; direction: ltr }
.contact .mail { font-family: 'IBM Plex Sans', sans-serif; font-weight: 600; font-size: 12pt; direction: ltr }
.contact .wa { font-size: 9.5pt; color: #E6EAE5 }
.qr { background: #FFFFFF; border-radius: 2mm; padding: 2.5mm; text-align: center; width: 37mm; flex-shrink: 0 }
.qr img { width: 31mm; height: 31mm; display: block; margin: 0 auto }
.qr div { color: #0F1419; font-size: 7.5pt; line-height: 1.3; margin-top: 1.5mm; font-weight: 600 }
.qr .wl { color: #128C4A; font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 9pt; margin-top: .8mm; letter-spacing: .02em }
.foot { padding: 2.5mm 14mm 4mm; font-size: 7pt; color: #6B747C; text-align: center }
"""


def css_for(lang):
    extra, allstack, head, mono = FONTS.get(lang, (None, None, None, None))
    body = allstack or "'IBM Plex Sans', Arial, sans-serif"
    head = allstack or head or "'Archivo', sans-serif"
    mono = allstack or mono or "'IBM Plex Mono', monospace"
    c = CSS.replace('@BODY', body).replace('@HEAD', head).replace('@MONO', mono)
    if lang in RTL or lang in TALL or lang in ('th', 'am', 'bn', 'ko', 'ja'):
        c = re.sub(r'letter-spacing: [^;}]+;?', '', c) if lang in RTL else c
        c = c.replace('line-height: 1.08', 'line-height: 1.3')
    if lang in TALL:
        c = c.replace('line-height: 1.5;', 'line-height: 1.75;').replace('font-size: 26pt', 'font-size: 23pt')
        c += '\nbody { overflow-wrap: anywhere }'
    if lang in RTL:
        c += "\n.contact .row { justify-content: flex-start }"
    link = f'https://fonts.googleapis.com/css2?{BASE_FONTS}' + (f'&family={extra}' if extra else '') + '&display=block'
    return c, link


def page(m, lang, d, T, mt, missing):
    def t(s):
        if not lang:
            return s
        if s in d:
            return d[s]
        if re.search(r'[A-Za-z]', s):
            missing.add(s)
        return s
    def f(s):
        return T.get(s, s) if lang else s
    e = html.escape
    x = mt[m['id']]
    eyebrow = ' · '.join(t(s) for s in x['eyebrow'])
    rows = ''.join(f'<tr><td class="k">{e(t(k))}</td><td class="v">{e(t(v))}</td></tr>' for k, v in x['specs'])
    css, link = css_for(lang)
    return f"""<!doctype html><html lang="{lang or 'en'}"{' dir="rtl"' if lang in RTL else ''}><head><meta charset="utf-8">
<link rel="stylesheet" href="{link}">
<style>{css}</style></head><body>
<div class="head"><img src="{svg_uri('yam-logo-blue.svg')}" alt="YAM">
<div class="r"><b>{e(t('LPG Transfer Pumps'))}</b><br>{e(t('Export only · Manufacturing and exporting LPG vacuum pumps since 2003'))}</div></div>
<div class="rule"></div>
<div class="hero"><div class="eyebrow">{e(eyebrow)}</div><h1>{e(t(x['title']))}</h1><p class="desc">{e(t(x['desc']))}</p></div>
<div class="photo"><img src="{jpeg_uri(m['img'], 1400)}" alt=""></div>
<div class="mid"><div class="specs"><h2>{e(f('Specifications'))}</h2><table>{rows}</table></div>
<div class="side"><img class="use" style="object-position: {m.get('use_pos', '50% 50%')}" src="{jpeg_uri(m['use'], 900)}" alt=""><div class="cap">{e(f(m['cap']))}</div>
</div></div>
<ul class="every"><li>{e(t('Every YAM pump handles up to 22 kg/cm² (21.5 bar) and ships in ready-to-use condition, with its hoses and valves in the carton.'))}</li><li>{e(t('1-year guarantee'))}</li></ul>
<div class="contact"><div class="l"><p class="ask">{e(t('Ask the price'))}</p><p class="reply">{e(t('We answer every message personally.'))}</p>
<div class="row"><span class="lab">{e(t('Web'))}</span><span class="site">www.lpgpumps.in</span></div>
<div class="row"><span class="lab">{e(t('Email'))}</span><span class="mail">{EMAIL}</span></div>
<div class="row"><span class="lab">WhatsApp</span><span class="wa">{e(f('Scan to message us on WhatsApp'))}</span></div></div>
<div class="qr"><img src="{qr_svg(wa_url(m, lang))}" alt=""><div class="wl">WhatsApp</div></div></div>
<div class="foot">Wingz · {e(t('New Delhi, India · Export only'))}</div>
</body></html>"""


if __name__ == '__main__':
    want = sys.argv[2:] or [''] + LANGS
    mt = model_text()
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for lang in want:
            lang = '' if lang == 'en' else lang
            d, T, missing = load(lang), FLY.get(lang, {}), set()
            od = os.path.join(OUTROOT, lang or 'en')
            os.makedirs(od, exist_ok=True)
            for m in MODELS:
                pg.set_content(page(m, lang, d, T, mt, missing), wait_until='networkidle')
                pg.evaluate('document.fonts.ready')
                # shrink the main photo until everything fits on one A4 page
                fit = pg.evaluate('''() => { const ph = document.querySelector('.photo'), f = document.querySelector('.foot');
                    let h = 70; const over = () => f.getBoundingClientRect().bottom > document.body.getBoundingClientRect().bottom + 0.5;
                    while (over() && h > 36) { h -= 2; ph.style.height = h + 'mm'; }
                    if (over()) { document.querySelector('.desc').style.fontSize = '9pt'; document.querySelector('table').style.fontSize = '8.5pt';
                                  document.querySelector('.every').style.fontSize = '8.5pt'; h = 70; ph.style.height = '70mm';
                                  while (over() && h > 36) { h -= 2; ph.style.height = h + 'mm'; } }
                    return over() ? -h : h; }''')
                if fit != 70: print('  photo', fit, lang or 'en', m['id'])
                pg.pdf(path=os.path.join(od, m['file'] + '.pdf'), format='A4', print_background=True, prefer_css_page_size=True)
            print(lang or 'en', 'done', ('MISSING: ' + ' | '.join(sorted(missing))) if missing else '')
        b.close()
