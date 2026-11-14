"""Build one A4 PDF flyer per pump model.

Usage: python3 tr/flyers.py <repo> <outdir> [lang]
Text comes from STR (English); translations can be supplied later per language
as a dict with the same keys. The QR code links to that language's products page.
"""
import sys, os, html, base64
import segno
from playwright.sync_api import sync_playwright

R, OUTDIR = sys.argv[1], sys.argv[2]
LANG = sys.argv[3] if len(sys.argv) > 3 else ''
A = os.path.join(R, 'pages', 'assets')
SITE = 'https://www.lpgpumps.in'
EMAIL = 'info@wingz.in'

STR = {
    'tagline': 'LPG TRANSFER PUMPS',
    'since': 'Manufacturing and exporting LPG pumps since 2003',
    'specs': 'Specifications',
    'every': 'Every YAM pump',
    'e1': 'Handles up to 22 kg/cm² (21.5 bar)',
    'e2': 'Ships ready to use, hoses and valves in the carton',
    'e3': 'Sent from India to your door, worldwide',
    'e4': '1-year guarantee against manufacturing defects',
    'ask': 'Ask us for the price to your country',
    'reply': 'We answer every message personally.',
    'web': 'Website',
    'mail': 'Email',
    'wa': 'WhatsApp',
    'wa_note': 'Tap “WhatsApp us” on our website',
    'scan': 'Scan for videos and the price',
    'foot': 'Wingz, New Delhi, India · Export only, not sold in India',
    'use_car': 'Filling a car’s LPG tank from a cylinder',
    'use_cyl': 'Moving gas from a big cylinder to a smaller one',
    'use_spares': 'Spare parts are supplied with every pump',
    'use_manual': 'The manual pump in use: no electricity needed',
}
MODELS = [
    dict(id='dc12', file='yam-12v-dc-lpg-pump', img='pump-12v-dc.jpg', use='use-car-filling.jpg', use_cap='use_car',
         eyebrow='Model 01 · Portable · Most popular', title='0.5 HP 12V DC LPG Pump',
         desc='A portable, light and compact pump made to be carried in the car and used wherever it is needed. It connects directly to a 12V car battery, so it works in every country, whatever the mains voltage.',
         specs=[('Power', '12 V DC, car battery'), ('Motor', '0.5 HP diaphragm'), ('Current draw', 'About 30–40 A at full load'),
                ('Transfer rate', '≈ 2 kg per minute'), ('15 kg cylinder', '7–8 minutes'), ('Shipping weight', '6 kg, packed'),
                ('In the box', 'Hoses, valves, cables, plugs & spare diaphragms')]),
    dict(id='ac220', file='yam-220v-ac-lpg-pump', img='pump-220v-ac.jpg', use='use-cylinder-to-cylinder.jpg', use_cap='use_cyl',
         eyebrow='Model 02 · Mains power', title='0.5 HP 220V AC LPG Pump',
         desc='A compact 220V diaphragm pump for transferring liquefied gas. It is easy to carry and easy to use. For 220V countries only; if your mains is 110V, choose the 12V DC pump.',
         specs=[('Power', '220 V AC'), ('Motor', '0.5 HP diaphragm'), ('Transfer rate', '≈ 2 kg per minute'),
                ('15 kg cylinder', '7–8 minutes'), ('Shipping weight', '7 kg, packed'), ('In the box', 'Hoses, valves, cables & clamps')]),
    dict(id='commercial', file='yam-1hp-commercial-lpg-pump', img='pump-1hp-commercial.jpg', use='use-cylinder-to-cylinder.jpg', use_cap='use_cyl',
         eyebrow='Model 03 · Heavy duty', title='1 HP 220V Commercial LPG Pump',
         desc='A heavy-duty 1 HP pump, recommended for commercial use where the pump works through the day.',
         specs=[('Power', '220 V AC'), ('Motor', '1 HP'), ('Transfer rate', '≈ 2 kg per minute'),
                ('Shipping weight', '18 kg, packed'), ('In the box', 'Hoses, valves, cables & clamps')]),
    dict(id='belt', file='yam-1hp-belt-drive-lpg-pump', img='pump-1hp-belt-drive.jpg', use='parts-and-spares.jpg', use_cap='use_spares',
         eyebrow='Model 04 · Heavy duty', title='1 HP 220V Belt-Drive LPG Pump',
         desc='The same 1 HP performance as the commercial pump, with the motor driving the pump through a belt. Supplied complete with the motor, or as the pump alone if you already have a motor.',
         specs=[('Power', '220 V AC'), ('Motor', '1 HP, belt drive'), ('Supplied', 'With motor, or without'),
                ('Transfer rate', '≈ 2 kg per minute'), ('Shipping weight', '22 kg with motor, 10 kg without'),
                ('In the box', 'Hoses, valves, cables & clamps')]),
    dict(id='manual', file='yam-manual-lpg-pump', img='pump-manual.jpg', use='poster-manual.jpg', use_cap='use_manual', use_pos='50% 78%',
         eyebrow='Model 05 · No power needed', title='Manual LPG Pump',
         desc='A hand-operated pump for transferring liquefied gas where there is no power supply. Transfer speed depends on the user.',
         specs=[('Power', 'Hand operated'), ('Transfer rate', 'Depends on the user'), ('15 kg cylinder', '12–14 minutes'),
                ('Shipping weight', '5 kg, packed'), ('In the box', 'Hoses & valves')]),
]


def data_uri(path, mime):
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def qr_svg(url):
    q = segno.make(url, error='m')
    return q.svg_data_uri(scale=6, border=0, dark='#0F1419')


CSS = """
@page { size: A4; margin: 0 }
* { box-sizing: border-box }
html, body { margin: 0; padding: 0 }
body { width: 210mm; height: 297mm; font-family: 'IBM Plex Sans', Arial, sans-serif; color: #0F1419; background: #FFFFFF;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; position: relative; overflow: hidden; display: flex; flex-direction: column }
.mono { font-family: 'IBM Plex Mono', monospace }
.head { display: flex; align-items: center; justify-content: space-between; padding: 10mm 14mm 5mm }
.head img { height: 13mm }
.head .r { text-align: right; font-size: 8.5pt; color: #3A444D; line-height: 1.5 }
.head .r b { font-family: 'Archivo', sans-serif; font-weight: 700; letter-spacing: .12em; color: #0F1419; font-size: 9pt }
.rule { height: 1.2mm; background: #1747D1; margin: 0 14mm }
.hero { padding: 6mm 14mm 0 }
.eyebrow { font-family: 'IBM Plex Mono', monospace; font-size: 9pt; letter-spacing: .14em; text-transform: uppercase; color: #1747D1 }
h1 { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 26pt; line-height: 1.05; letter-spacing: -.01em; margin: 2mm 0 2.5mm }
.desc { font-size: 10pt; line-height: 1.5; color: #3A444D; margin: 0; max-width: 170mm }
.photo { margin: 4.5mm 14mm 0; height: 74mm; border: 0.3mm solid #C9CFC8; border-radius: 3mm; background: #FFFFFF; display: flex; align-items: center; justify-content: center; overflow: hidden }
.photo img { max-width: 100%; max-height: 100%; object-fit: contain }
.mid { display: flex; gap: 7mm; padding: 5mm 14mm 0; align-items: flex-start }
.specs { flex: 1.35 }
.specs h2, .side h2 { font-family: 'Archivo', sans-serif; font-weight: 700; font-size: 11.5pt; margin: 0 0 2mm }
table { width: 100%; border-collapse: collapse; font-size: 9.5pt }
td { padding: 1.45mm 0; border-top: 0.25mm solid #D5DAD4; vertical-align: top }
td.k { font-family: 'IBM Plex Mono', monospace; color: #3A444D; width: 40% }
td.v { font-weight: 600 }
.side { flex: 1 }
.side .use { width: 100%; aspect-ratio: 3 / 2; object-fit: cover; border-radius: 2mm; border: 0.25mm solid #D5DAD4; display: block; background: #FFF }
.side .cap { font-size: 8.5pt; color: #3A444D; margin-top: 1.5mm }
.every { margin: 4.5mm 14mm 0; padding: 3.5mm 5mm; list-style: none; font-size: 9pt; line-height: 1.4; background: #F3F4F1; border-radius: 2mm; display: grid; grid-template-columns: 1fr 1fr; gap: 1.5mm 6mm }
.every b { grid-column: 1 / -1; font-family: 'Archivo', sans-serif; font-size: 10.5pt }
.every li { padding-left: 5mm; position: relative }
.every li:before { content: ''; position: absolute; left: 0; top: 1.3mm; width: 2.4mm; height: 2.4mm; border-radius: 50%; background: #1747D1 }
.contact { margin: auto 14mm 0; background: #0F1419; color: #FFFFFF; border-radius: 3mm;
           display: flex; align-items: center; gap: 8mm; padding: 5mm 7mm }
.contact .l { flex: 1 }
.contact .ask { font-family: 'Archivo', sans-serif; font-weight: 700; font-size: 14pt; margin: 0 0 1mm }
.contact .reply { font-size: 9pt; color: #C9CFC8; margin: 0 0 2.5mm }
.contact .row { display: flex; align-items: baseline; gap: 3mm; margin-top: 1.4mm }
.contact .lab { font-family: 'IBM Plex Mono', monospace; font-size: 7.5pt; letter-spacing: .12em; text-transform: uppercase; color: #9FB4FF; width: 22mm }
.contact .site { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 19pt; color: #FFFFFF }
.contact .mail { font-weight: 600; font-size: 12pt }
.contact .wa { font-size: 9.5pt; color: #E6EAE5 }
.qr { background: #FFFFFF; border-radius: 2mm; padding: 2.5mm; text-align: center; width: 36mm }
.qr img { width: 31mm; height: 31mm; display: block; margin: 0 auto }
.qr div { color: #0F1419; font-size: 7.5pt; line-height: 1.3; margin-top: 1.5mm; font-weight: 600 }
.foot { padding: 2.5mm 14mm 4mm; font-size: 7pt; color: #6B747C; text-align: center }
"""


def page(m, S):
    url = f"{SITE}/{LANG + '/' if LANG else ''}products#{m['id']}"
    rows = ''.join(f'<tr><td class="k">{html.escape(k)}</td><td class="v">{html.escape(v)}</td></tr>' for k, v in m['specs'])
    every = ''.join(f'<li>{html.escape(S[k])}</li>' for k in ('e1', 'e2', 'e3', 'e4'))
    return f"""<!doctype html><html lang="{LANG or 'en'}"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=block">
<style>{CSS}</style></head><body>
<div class="head"><img src="{data_uri(os.path.join(A, 'yam-logo-blue.svg'), 'image/svg+xml')}" alt="YAM">
<div class="r"><b>{html.escape(S['tagline'])}</b><br>{html.escape(S['since'])}</div></div>
<div class="rule"></div>
<div class="hero"><div class="eyebrow">{html.escape(m['eyebrow'])}</div><h1>{html.escape(m['title'])}</h1><p class="desc">{html.escape(m['desc'])}</p></div>
<div class="photo"><img src="{data_uri(os.path.join(A, m['img']), 'image/jpeg')}" alt=""></div>
<div class="mid"><div class="specs"><h2>{html.escape(S['specs'])}</h2><table>{rows}</table></div>
<div class="side"><img class="use" style="object-position: {m.get('use_pos', '50% 50%')}" src="{data_uri(os.path.join(A, m['use']), 'image/jpeg')}" alt=""><div class="cap">{html.escape(S[m['use_cap']])}</div>
</div></div>
<ul class="every"><b>{html.escape(S['every'])}</b>{every}</ul>
<div class="contact"><div class="l"><p class="ask">{html.escape(S['ask'])}</p><p class="reply">{html.escape(S['reply'])}</p>
<div class="row"><span class="lab">{html.escape(S['web'])}</span><span class="site">www.lpgpumps.in</span></div>
<div class="row"><span class="lab">{html.escape(S['mail'])}</span><span class="mail">{EMAIL}</span></div>
<div class="row"><span class="lab">{html.escape(S['wa'])}</span><span class="wa">{html.escape(S['wa_note'])}</span></div></div>
<div class="qr"><img src="{qr_svg(url)}" alt=""><div>{html.escape(S['scan'])}</div></div></div>
<div class="foot">{html.escape(S['foot'])}</div>
</body></html>"""


if __name__ == '__main__':
    os.makedirs(OUTDIR, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for m in MODELS:
            pg.set_content(page(m, STR), wait_until='networkidle')
            pg.evaluate('document.fonts.ready')
            out = os.path.join(OUTDIR, m['file'] + ('-' + LANG if LANG else '') + '.pdf')
            pg.pdf(path=out, format='A4', print_background=True, prefer_css_page_size=True)
            print(out)
        b.close()
