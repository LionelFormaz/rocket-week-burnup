# Fabrique les 4 cases photo de la page d'accueil Rocket Week (titre écrit sur la photo).
import io, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 720
INK, BEIGE, RED = (15, 15, 15), (245, 245, 220), (200, 16, 46)
FONTS = {
    'bebas': 'https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf',
    'dm': 'https://raw.githubusercontent.com/google/fonts/main/ofl/dmsans/DMSans%5Bopsz,wght%5D.ttf',
}
CASES = [
    ('objectifs', '01', 'Objectifs\n& burn-up', 'Nos 3 objectifs, les résultats clés et la courbe', '1629721671030-a83edbb11211'),
    ('crm', '02', 'CRM', 'Établissements vaudois, fournisseurs et sponsors', '1752159684779-0639174cdfac'),
    ('debriefs', '03', 'Débriefs\ndu jour', 'Réussites, échecs et apprentissages de chacun', '1758691736934-e5d6d0c7f875'),
    ('fichiers', '04', 'Fichiers', 'Visuels, offres, devis et documents partagés', '1583521214690-73421a1829a9'),
]

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=60).read()

def font(key, size, weight=None):
    path = f'{key}.ttf'
    if not os.path.exists(path):
        open(path, 'wb').write(get(FONTS[key]))
    f = ImageFont.truetype(path, size)
    if weight:
        try: f.set_variation_by_axes([14, weight])
        except Exception: pass
    return f

def photo(pid):
    if os.environ.get('PLACEHOLDER'):
        img = Image.new('RGB', (W, H), (120, 110, 90))
        ImageDraw.Draw(img).ellipse((700, 100, 1100, 500), fill=(180, 60, 60))
        return img
    raw = get(f'https://images.unsplash.com/photo-{pid}?w={W}&h={H}&fit=crop&auto=format&fm=jpg&q=85')
    return Image.open(io.BytesIO(raw)).convert('RGB').resize((W, H))

def card(slug, num, title, sub, pid):
    img = photo(pid)
    # Voile sombre, plus dense en bas pour que le texte reste lisible.
    shade = Image.new('L', (W, H))
    d = ImageDraw.Draw(shade)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=int(255 * (0.30 + 0.58 * t ** 1.4)))
    img = Image.composite(Image.new('RGB', (W, H), INK), img, shade)
    d = ImageDraw.Draw(img)
    m = 64
    # Numéro et étiquette en haut.
    d.rectangle((m, m, m + 14, m + 54), fill=RED)
    d.text((m + 34, m - 6), num, font=font('bebas', 64), fill=BEIGE)
    eyebrow = font('dm', 26, 700)
    lab = 'ROCKET WEEK'
    lw = d.textlength(lab, font=eyebrow) + 2 * len(lab)
    x = W - m - lw
    for ch in lab:
        d.text((x, m + 10), ch, font=eyebrow, fill=BEIGE)
        x += d.textlength(ch, font=eyebrow) + 2
    # Titre et sous-titre en bas.
    big = font('bebas', 160)
    small = font('dm', 40, 500)
    lines = title.upper().split('\n')
    lh = 140
    y_sub = H - m - 46
    y = y_sub - 62 - lh * len(lines)
    for line in lines:
        d.text((m - 4, y), line, font=big, fill=BEIGE)
        y += lh
    d.rectangle((m, y_sub - 22, m + 90, y_sub - 15), fill=RED)
    d.text((m, y_sub), sub, font=small, fill=(235, 235, 215))
    os.makedirs('cases', exist_ok=True)
    img.save(f'cases/{slug}.jpg', quality=86, optimize=True, progressive=True)
    print('cases/' + slug + '.jpg')

for c in CASES:
    card(*c)
