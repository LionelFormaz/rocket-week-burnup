// Lit les bases Notion de la Rocket Week et écrit data.json pour le graphique.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';

const TOKEN = process.env.NOTION_TOKEN;
if (!TOKEN) { console.error('Secret NOTION_TOKEN manquant'); process.exit(1); }

const DB = {
  burnup: '68365e00883341eba43acc068146c6f9',
  krs: '30136a793db349d9b1b3d5a1ac75934c',
  objectifs: '9f409c0ad26a4d828cb90895cadb55a4',
};

async function query(id) {
  const rows = [];
  let cursor;
  do {
    const res = await fetch(`https://api.notion.com/v1/databases/${id}/query`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${TOKEN}`,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(cursor ? { start_cursor: cursor, page_size: 100 } : { page_size: 100 }),
    });
    if (!res.ok) throw new Error(`Notion ${res.status} : ${await res.text()}`);
    const json = await res.json();
    rows.push(...json.results);
    cursor = json.has_more ? json.next_cursor : null;
  } while (cursor);
  return rows;
}

function val(p) {
  if (!p) return null;
  switch (p.type) {
    case 'title': return p.title.map(t => t.plain_text).join('');
    case 'rich_text': return p.rich_text.map(t => t.plain_text).join('');
    case 'number': return p.number;
    case 'select': return p.select ? p.select.name : null;
    case 'date': return p.date ? p.date.start : null;
    case 'checkbox': return p.checkbox;
    case 'relation': return p.relation.map(r => r.id);
    case 'formula': return p.formula[p.formula.type] ?? null;
    default: return null;
  }
}

const [burnup, krs, objectifs] = await Promise.all([query(DB.burnup), query(DB.krs), query(DB.objectifs)]);

const objNames = Object.fromEntries(objectifs.map(o => [o.id, { nom: val(o.properties['Objectif']), n: val(o.properties['N°']) ?? 0 }]));

const days = {};
for (const r of burnup) {
  const p = r.properties;
  const n = val(p['N°']);
  const d = days[n] ??= { n, jour: (val(p['Jour']) || '').replace(/^\d+\s*·\s*/, ''), date: val(p['Date']) };
  const serie = val(p['Série']);
  const v = Number(val(p['KR atteints'])) || 0;
  if (serie === 'Réalisé') d.realise = v;
  else if (serie === 'Rythme idéal') d.ideal = v;
  else if (serie === 'Total à atteindre') d.total = v;
}

const payload = {
  dbg: objectifs.map(o => [val(o.properties['Objectif']), val(o.properties['Traces texte'])]),
  days: Object.values(days).sort((a, b) => a.n - b.n),
  krs: krs.map(k => {
    const p = k.properties;
    const obj = objNames[(val(p['Objectif']) || [])[0]] || { nom: 'Sans objectif', n: 9 };
    return {
      label: val(p['Résultat clé']),
      objectif: obj.nom,
      ordre: obj.n,
      realise: Number(val(p['Réalisé'])) || 0,
      cible: Number(val(p['Cible'])) || 0,
      unite: val(p['Unité']) || '',
      progression: Number(val(p['Progression (%)'])) || 0,
      debug: val(p['Debug']),
      valeurs: val(p['Valeurs']),
    };
  }).sort((a, b) => a.ordre - b.ordre || a.label.localeCompare(b.label, 'fr')),
};

// On ne réécrit le fichier que si les chiffres ont changé.
let previous = null;
if (existsSync('data.json')) {
  try { const old = JSON.parse(readFileSync('data.json', 'utf8')); delete old.updated; previous = JSON.stringify(old); } catch {}
}
if (previous === JSON.stringify(payload)) {
  console.log('Aucun changement.');
} else {
  writeFileSync('data.json', JSON.stringify({ updated: new Date().toISOString(), ...payload }, null, 2));
  console.log('data.json mis à jour.');
}
