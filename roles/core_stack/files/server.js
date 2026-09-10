const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
// Mounted as a Docker volume so data survives container rebuilds/updates.
const DATA_FILE = process.env.DATA_FILE || path.join(__dirname, 'data', 'db.json');

app.use(express.json({ limit: '2mb' }));
app.use(express.static(path.join(__dirname, 'public')));

function ensureDataFile() {
  const dir = path.dirname(DATA_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  if (!fs.existsSync(DATA_FILE)) fs.writeFileSync(DATA_FILE, '{}');
}

// Whole dataset is a small object keyed by "YYYY-MM" -> array of entries.
app.get('/api/data', (req, res) => {
  ensureDataFile();
  try {
    const raw = fs.readFileSync(DATA_FILE, 'utf8');
    res.json(JSON.parse(raw || '{}'));
  } catch (e) {
    res.status(500).json({ error: 'read failed' });
  }
});

app.put('/api/data', (req, res) => {
  ensureDataFile();
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(req.body ?? {}, null, 2));
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: 'write failed' });
  }
});

app.get('/healthz', (req, res) => res.send('ok'));

app.listen(PORT, () => console.log(`Hifth tracker listening on :${PORT}`));
