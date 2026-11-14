"""Generate the English how-to guide pages in pages/ from the layout of an existing landing page.
Run: python3 tr/guides.py .   (then python3 tr/build.py .)"""
import re, sys, html

R = sys.argv[1] if len(sys.argv) > 1 else '.'
TPL = open(f'{R}/pages/lpg-pump-for-car.html', encoding='utf-8').read()
HEAD_END = TPL.index('</header>') + len('</header>')
BAND = TPL.index('<section style="background: #1747D1')
HEAD, FOOT = TPL[:HEAD_END], TPL[BAND:]

WRAP = 'max-width: 1240px; margin: 0 auto; padding: 0 32px'
EYEBROW = "font-family: 'IBM Plex Mono', monospace; font-size: 13px; letter-spacing: 0.12em; text-transform: uppercase; color: #1747D1"
H2 = "margin: 0; font-family: 'Archivo', sans-serif; font-weight: 700; font-size: clamp(26px, 2.8vw, 36px); line-height: 1.1; letter-spacing: -0.01em"
P = 'margin: 0; color: #3A444D; font-size: 18px; max-width: 42em'
BTN = 'color: #FFFFFF; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 10px; min-height: 52px; padding: 0 22px; border-radius: 6px'

def esc(s): return html.escape(s, quote=False)

def head(title, desc, slug):
    h = re.sub(r'<title>.*?</title>', f'<title>{esc(title)}</title>', HEAD, count=1, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + html.escape(desc), h, count=1)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + html.escape(title), h, count=1)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + html.escape(desc), h, count=1)
    h = re.sub(r'(<link rel="canonical" href="https://www\.lpgpumps\.in/)[^"]*', lambda m: m.group(1) + slug, h, count=1)
    return h

def hero(eyebrow, h1, intro, img, alt):
    return (f'\n<section style="max-width: 1240px; margin: 0 auto; padding: 64px 32px 40px; display: flex; flex-wrap: wrap; gap: 48px; align-items: center">\n'
            f'<div style="flex: 1 1 460px; min-width: 0; display: flex; flex-direction: column; gap: 22px">\n'
            f'<div style="{EYEBROW}">{esc(eyebrow)}</div>\n'
            f'<h1 style="margin: 0; font-family: \'Archivo\', sans-serif; font-weight: 800; font-size: clamp(34px, 4.4vw, 56px); line-height: 1.06; letter-spacing: -0.02em">{esc(h1)}</h1>\n'
            f'<p style="margin: 0; font-size: 20px; color: #3A444D; max-width: 32em">{esc(intro)}</p>\n</div>\n'
            f'<div style="flex: 1 1 420px; min-width: 0"><img src="{img}" alt="{html.escape(alt)}" style="display: block; width: 100%; height: auto; aspect-ratio: 3 / 2; object-fit: contain; border: 1px solid #C9CFC8; border-radius: 10px; box-sizing: border-box; background: #FFFFFF"></div>\n</section>')

def block(h2, *paras, items=None, ordered=False):
    out = [f'<section style="{WRAP}; padding-top: 40px"><div style="display: flex; flex-direction: column; gap: 14px; max-width: 900px">', f'<h2 style="{H2}">{esc(h2)}</h2>']
    for p in paras: out.append(f'<p style="{P}">{p}</p>')
    if items:
        tag = 'ol' if ordered else 'ul'
        lis = ''.join(f'<li style="padding: 6px 0">{i}</li>' for i in items)
        out.append(f'<{tag} style="margin: 0; padding-left: 1.3em; color: #3A444D; font-size: 18px; max-width: 42em">{lis}</{tag}>')
    out.append('</div></section>')
    return '\n'.join(out)

def steps(h2, items):
    rows = ''.join(
        f'<li style="display: flex; gap: 18px; padding: 18px 0; border-top: 1px solid #D5DAD4"><span aria-hidden="true" style="flex: 0 0 auto; width: 36px; height: 36px; border-radius: 50%; background: #1747D1; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; font-weight: 700">{n}</span>'
        f'<div style="display: flex; flex-direction: column; gap: 6px"><strong style="font-family: \'Archivo\', sans-serif; font-size: 20px">{esc(t)}</strong><span style="color: #3A444D; font-size: 17px">{b}</span></div></li>'
        for n, (t, b) in enumerate(items, 1))
    return (f'<section style="{WRAP}; padding-top: 48px"><div style="max-width: 900px"><h2 style="{H2}; margin-bottom: 16px">{esc(h2)}</h2>'
            f'<ol style="list-style: none; margin: 0; padding: 0; border-bottom: 1px solid #D5DAD4">{rows}</ol></div></section>')

def warn(title, text):
    return (f'<section style="{WRAP}; padding-top: 40px"><div style="background: #FFE9A8; border: 1px solid #D9B23C; border-radius: 10px; padding: 22px 28px; font-size: 17px; max-width: 900px; box-sizing: border-box">'
            f'<strong>{esc(title)}</strong> {text}</div></section>')

def faq(h2, qa):
    det = ''.join(f'<details style="border-top: 1px solid #C9CFC8; padding: 4px 0"><summary style="font-weight: 600; font-size: 18px; padding: 15px 0; min-height: 44px; box-sizing: border-box">{esc(q)}</summary><p style="margin: 0 0 20px; color: #3A444D; max-width: 44em">{a}</p></details>' for q, a in qa)
    return f'<section style="{WRAP}; padding-top: 56px"><div style="max-width: 900px"><h2 style="{H2}; margin-bottom: 12px">{esc(h2)}</h2>{det}</div></section>'

def cta(h2, text, product_link, product_label):
    return (f'<section style="{WRAP}; padding-top: 56px"><div style="background: #FFFFFF; border: 1px solid #D5DAD4; border-radius: 10px; padding: 32px; display: flex; flex-direction: column; gap: 14px; max-width: 900px; box-sizing: border-box">'
            f'<h2 style="{H2}">{esc(h2)}</h2><p style="{P}">{text}</p>'
            f'<div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center"><a href="https://wa.me/918920783083" style="background: #0B7A43; {BTN}">WhatsApp us</a>'
            f'<a href="https://t.me/lpgpumps" style="background: #1B7DB3; {BTN}">Telegram</a>'
            f'<a href="{product_link}" style="font-weight: 600; display: inline-flex; align-items: center; min-height: 44px; padding: 0 8px">{esc(product_label)}</a></div></div></section>')

def related(h2, links):
    a = ''.join(f'<li style="padding: 6px 0"><a href="{u}" style="font-weight: 600; display: inline-flex; align-items: center; min-height: 44px">{esc(t)}</a></li>' for u, t in links)
    return f'<section style="{WRAP}; padding-top: 48px; padding-bottom: 88px"><div style="max-width: 900px"><h2 style="{H2}; font-size: 24px">{esc(h2)}</h2><ul style="margin: 8px 0 0; padding-left: 1.2em">{a}</ul></div></section>'

G1, G2, G3 = 'guide-fill-car-lpg-tank-from-cylinder', 'guide-lpg-cylinder-to-cylinder-transfer', 'guide-which-lpg-transfer-pump'
ALL = [(f'/{G1}', 'How to fill a car LPG tank from a gas cylinder'),
       (f'/{G2}', 'How to transfer LPG from a big cylinder to a small one'),
       (f'/{G3}', 'Which LPG transfer pump do you need? 12V, 220V, 1 HP or manual')]
def others(me): return [x for x in ALL if x[0] != '/' + me]
LAW = 'Rules for transferring LPG between cylinders and cars are different in every country. Please check the rules where you live before you start. We export only and do not sell these pumps in India.'

pages = {}

pages[G1] = (
    head('How to Fill a Car LPG Tank from a Gas Cylinder (Step by Step) | YAM',
         'Step-by-step guide to filling a car LPG (autogas) tank from a gas cylinder with a 12V transfer pump: what you need, safety, how long it takes and common questions.', G1)
    + hero('LPG guide', 'How to fill a car LPG tank from a gas cylinder.',
           'A step-by-step guide for drivers who fill their own LPG car from a gas cylinder, using a 12V pump that runs from the car battery.',
           '/assets/use-car-filling.jpg', 'Illustration: a 12V LPG pump filling a car tank from an upside-down gas cylinder')
    + block('What you need', items=[
        'A car with an LPG (autogas) tank and filler valve.',
        'A full LPG or propane gas cylinder.',
        'A 12V LPG transfer pump. It runs from the car battery, so you can use it anywhere. The <a href="/products#dc12">YAM 12V DC pump</a> comes with its hoses, valves and battery clamps.',
        'The connector that fits the car filler and the cylinder valve used in your country. Fittings are different in every country, so most people buy this locally.',
        'An open space outdoors, away from flames, sparks and drains.'])
    + steps('Step by step', [
        ('Park outdoors and switch off', 'Turn off the engine. No smoking, no flames, and keep mobile phones and anything that can spark away from the pump while it works.'),
        ('Turn the cylinder upside down', 'LPG is moved as a liquid. In an upright cylinder the top is gas; upside down, the liquid sits at the outlet and the transfer goes quickly. Stand it securely so it cannot fall.'),
        ('Connect the hoses', 'Connect the inlet hose from the cylinder valve to the pump, and the outlet hose from the pump to the car filler with your connector. Screw every thread in tightly before you open any valve.'),
        ('Connect the battery', 'Clip the battery clamps straight onto the car battery terminals. The 0.5 HP pump draws about 30 to 40 amps at full load, so do not use the cigarette-lighter socket.'),
        ('Open the valves and start the pump', 'Open the cylinder valve, then the outlet valve, and switch the pump on. It moves about 2 kg of gas a minute: a 15 kg cylinder takes 7 to 8 minutes.'),
        ('Stop and close everything', 'Car LPG tanks have an automatic fill-stop valve that stops filling when the tank is full, at about 80%. When the flow stops or the cylinder is empty, switch the pump off, close all valves and only then disconnect the hoses.'),
        ('Check for leaks', 'Before you drive, check every joint for the smell of gas. Brushing soapy water on a joint shows a leak as bubbles.')])
    + warn('Check the law in your country.', LAW)
    + faq('Common questions', [
        ('How long does it take to fill a car from a cylinder?', 'About 7 to 8 minutes for a 15 kg cylinder with a 12V or 220V pump, or 12 to 14 minutes with a manual pump.'),
        ('Will the pump empty the cylinder completely?', 'Nearly. When the last liquid leaves, a little turns into gas and stays at the top, so about 2 to 3% remains in the cylinder.'),
        ('Can I power the pump from the cigarette-lighter socket?', 'No. The pump needs about 30 to 40 amps at full load, so it is connected directly to the battery terminals with the clamps supplied.'),
        ('Which connector do I need?', 'The one that fits the LPG filler on cars in your country and the valve on your cylinders. The pump comes with hoses and valves; you add the local connector.'),
        ('What if a part wears out?', 'The diaphragm is the part that wears. Spare diaphragms are in the box and it is easy to replace, and the pump has a one-year guarantee.')])
    + cta('Need a pump for your car?', 'The YAM 12V DC pump is 6 kg packed and ships from India to your door, ready to use. Message us for the price to your country.', '/products#dc12', 'See the 12V DC pump')
    + related('More guides', others(G1)) + '\n' + FOOT)

pages[G2] = (
    head('How to Transfer LPG from a Big Cylinder to a Small One | YAM Guide',
         'How to fill small LPG or propane cylinders from a big cylinder with a transfer pump: equipment, step by step, filling by weight, safety and common questions.', G2)
    + hero('LPG guide', 'How to transfer LPG from a big cylinder to a small one.',
           'How to fill small gas cylinders from a large one with a transfer pump, safely and without overfilling.',
           '/assets/use-cylinder-to-cylinder.jpg', 'Illustration: a 220V LPG pump filling a small cylinder from an upside-down large cylinder')
    + block('What you need', items=[
        'A full large cylinder and the small cylinders you want to fill.',
        'A transfer pump. The <a href="/products#ac220">220V AC pump</a> plugs into a normal socket; in 110V countries use the <a href="/products#dc12">12V DC pump</a> on a car battery, or the <a href="/products#manual">manual pump</a> where there is no electricity.',
        'The valve connectors used on cylinders in your country.',
        'A scale to weigh the small cylinder while it fills.',
        'An open, well-ventilated space away from flames and sparks.'])
    + steps('Step by step', [
        ('Only from big to small', 'These pumps move gas from a larger cylinder into a smaller one. Filling a bigger cylinder from a smaller one needs a higher-pressure pump.'),
        ('Turn the big cylinder upside down', 'This brings the liquid to the outlet. Keep the small cylinder upright on the scale.'),
        ('Note the weight to stop at', 'Most cylinders are stamped with their empty (tare) weight and the weight of gas they hold. Add the two: that is the full weight. Never fill beyond it.'),
        ('Connect and tighten', 'Connect the big cylinder to the pump inlet and the pump outlet to the small cylinder. Tighten every thread before opening a valve.'),
        ('Open the valves and pump', 'Open the valves and start the pump. It moves about 2 kg a minute. Watch the scale.'),
        ('Stop at the full weight', 'Switch off and close the valves when the scale reaches the full weight. Disconnect only after the valves are closed, then check the joints for leaks with soapy water.')])
    + warn('Do not overfill.', 'A cylinder needs space for the gas to expand when it warms up, so fill by weight and never past the full weight stamped on the cylinder. ' + LAW)
    + faq('Common questions', [
        ('Can I fill a big cylinder from a small one?', 'Not with these pumps. They move gas from a larger cylinder to a smaller one; the other way round needs a higher-pressure pump.'),
        ('How fast is it?', 'About 2 kg of gas per minute with the 12V or 220V pump.'),
        ('Which pump should I choose for refilling all day?', 'For a business filling cylinders all day, the 1 HP commercial pump or the 1 HP belt-drive pump is made for heavy use.'),
        ('Why turn the big cylinder upside down?', 'LPG is moved as a liquid. Upside down, the liquid reaches the outlet, so the transfer is fast and complete.')])
    + cta('Choose a pump for cylinder filling.', 'The 220V AC pump is 7 kg packed and plugs into any 220V socket. Message us for one total price, pump and shipping together.', '/products#ac220', 'See the 220V AC pump')
    + related('More guides', others(G2)) + '\n' + FOOT)

ROW = lambda cells, th=False: '<tr>' + ''.join((f'<th scope="col" style="text-align: left; padding: 12px 14px; border-bottom: 2px solid #0F1419; font-family: \'Archivo\', sans-serif">{c}</th>' if th else f'<td style="padding: 12px 14px; border-bottom: 1px solid #D5DAD4; vertical-align: top">{c}</td>') for c in cells) + '</tr>'
TABLE = ('<section style="max-width: 1240px; margin: 0 auto; padding: 40px 32px 0"><div style="overflow-x: auto; max-width: 1000px"><table style="border-collapse: collapse; width: 100%; min-width: 640px; font-size: 16px; background: #FFFFFF; border: 1px solid #D5DAD4; border-radius: 10px">'
         + ROW(['Pump', 'Power', 'Packed weight', '15 kg cylinder', 'Best for'], th=True)
         + ROW(['<a href="/products#dc12">12V DC, 0.5 HP</a>', '12V car battery', '6 kg', '7 to 8 minutes', 'Filling a car anywhere; 110V countries'])
         + ROW(['<a href="/products#ac220">220V AC, 0.5 HP</a>', '220V socket', '7 kg', '7 to 8 minutes', 'Cylinders at home or in a shop'])
         + ROW(['<a href="/products#commercial">1 HP commercial</a>', '220V', '18 kg', 'On request', 'A business filling all day'])
         + ROW(['<a href="/products#belt">1 HP belt drive</a>', '220V, with or without motor', '22 kg (10 kg without motor)', 'On request', 'Heavy use; if you already have a motor'])
         + ROW(['<a href="/products#manual">Manual</a>', 'None, by hand', '5 kg', '12 to 14 minutes', 'Places without electricity'])
         + '</table></div></section>')

pages[G3] = (
    head('Which LPG Transfer Pump Do You Need? 12V vs 220V vs 1 HP vs Manual | YAM',
         'Compare 12V DC, 220V AC, 1 HP commercial, belt-drive and manual LPG transfer pumps: power, weight, speed and which one suits filling cars or cylinders.', G3)
    + hero('LPG guide', 'Which LPG transfer pump do you need?',
           'A plain comparison of the five YAM pumps, so you can choose by what you fill, the power you have and how often you use it.',
           '/assets/pump-12v-dc.jpg', 'YAM 12V DC LPG transfer pump with hoses and valves')
    + block('Start with three questions', items=[
        '<strong>What do you fill?</strong> A car tank, or small cylinders from a big one.',
        '<strong>What power do you have?</strong> A car battery, a 220V socket, a 110V socket, or no electricity.',
        '<strong>How often?</strong> Now and then for yourself, or all day as a business.'])
    + TABLE
    + block('Our advice', items=[
        '<strong>Filling your own car:</strong> the 12V DC pump. It runs from the car battery, is the lightest to ship and works in every country.',
        '<strong>Your country uses 110V:</strong> choose the 12V DC pump. The 220V pumps are only for 220V mains.',
        '<strong>Filling small cylinders at home or in a shop:</strong> the 220V AC pump.',
        '<strong>A business filling all day:</strong> the 1 HP commercial pump, or the 1 HP belt-drive pump if you want to use a motor you already have.',
        '<strong>No electricity:</strong> the manual pump. Speed depends on the person pumping.'])
    + block('What every pump includes', 'Every YAM pump handles up to 22 kg/cm² (21.5 bar) and arrives ready to use, with hoses, valves and spare parts in the box. The diaphragm is the part that wears; spares are included and it is easy to replace yourself. All pumps have a one-year guarantee.')
    + warn('Check the law in your country.', LAW)
    + cta('Not sure which one?', 'Tell us your country, what you want to fill and the power you have. We reply with the right pump and one total price, pump and shipping together.', '/products#compare', 'Compare all pumps')
    + related('More guides', others(G3)) + '\n' + FOOT)

for slug, h in pages.items():
    open(f'{R}/pages/{slug}.html', 'w', encoding='utf-8').write(h)
print('wrote', len(pages), 'guides')

# hub page
cards = ''.join(
    f'<a href="{u}" style="flex: 1 1 300px; min-width: 0; background: #FFFFFF; border: 1px solid #D5DAD4; border-radius: 10px; padding: 26px; display: flex; flex-direction: column; gap: 10px; color: #0F1419; text-decoration: none">'
    f'<img src="{img}" alt="" style="display: block; width: 100%; height: auto; aspect-ratio: 3 / 2; object-fit: contain; border-radius: 6px">'
    f'<strong style="font-family: \'Archivo\', sans-serif; font-size: 22px; line-height: 1.2">{esc(t)}</strong><span style="color: #3A444D">{esc(d)}</span></a>'
    for (u, t), img, d in zip(ALL, ['/assets/use-car-filling.jpg', '/assets/use-cylinder-to-cylinder.jpg', '/assets/pump-12v-dc.jpg'],
                              ['What you need, step by step, safety and how long it takes.', 'Filling small cylinders by weight, without overfilling.', 'Compare the five pumps by power, weight and use.']))
hub = (head('LPG Transfer Pump Guides | YAM LPG Pumps', 'Practical guides to filling a car LPG tank from a cylinder, filling small cylinders from a big one, and choosing the right LPG transfer pump.', 'guides')
       + f'\n<section style="max-width: 1240px; margin: 0 auto; padding: 64px 32px 24px; display: flex; flex-direction: column; gap: 18px"><div style="{EYEBROW}">LPG guides</div>'
       + '<h1 style="margin: 0; font-family: \'Archivo\', sans-serif; font-weight: 800; font-size: clamp(34px, 4.4vw, 56px); line-height: 1.06; letter-spacing: -0.02em">Guides to filling with LPG.</h1>'
       + '<p style="margin: 0; font-size: 20px; color: #3A444D; max-width: 34em">Practical answers for people who fill their own car or cylinders. Written by the team that has made YAM pumps since 2003.</p></section>'
       + f'<section style="max-width: 1240px; margin: 0 auto; padding: 16px 32px 88px; display: flex; flex-wrap: wrap; gap: 20px">{cards}</section>\n' + FOOT)
open(f'{R}/pages/guides.html', 'w', encoding='utf-8').write(hub)
print('wrote hub')
