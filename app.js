/* ══════════════════════════════════════════════════════════════
   Maths Bac – app.js
══════════════════════════════════════════════════════════════ */

const NOTION_LABELS = {
  fonctions:    'Fonctions',
  suites:       'Suites',
  geometrie:    'Géométrie',
  probabilites: 'Probabilités',
};

// ── State ──────────────────────────────────────────────────────
let allExercises   = [];
let currentNotion  = null;
let currentPool    = [];   // exercises for current notion
let seenIndices    = [];   // indices already shown this session

// ── DOM refs ───────────────────────────────────────────────────
const homeView     = document.getElementById('home-view');
const exerciseView = document.getElementById('exercise-view');
const exContent    = document.getElementById('exercise-content');
const exName       = document.getElementById('exam-name');
const exNum        = document.getElementById('exercise-num');
const notionBadge  = document.getElementById('notion-badge');
const pointsBadge  = document.getElementById('points-badge');
const progressText = document.getElementById('progress-text');
const counterHint  = document.getElementById('counter-hint');

// ── Bootstrap ──────────────────────────────────────────────────
fetch('exercises.json')
  .then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then(data => {
    allExercises = data.exercises;
    updateCounts();
  })
  .catch(err => {
    console.error('Failed to load exercises.json:', err);
    document.querySelector('.subtitle').textContent =
      '⚠ Impossible de charger exercises.json. Lance le site via un serveur local (voir README).';
  });

function updateCounts() {
  const notions = ['fonctions', 'suites', 'geometrie', 'probabilites'];
  notions.forEach(n => {
    const count = allExercises.filter(e => e.notions.includes(n)).length;
    const el = document.getElementById(`count-${n}`);
    if (el) el.textContent = `${count} exercices`;
  });
  const total = document.getElementById('total-count');
  if (total) total.textContent = `${allExercises.length} exercices au total · Sujets 2021–2025`;
}

// ── Navigation ─────────────────────────────────────────────────
function selectNotion(notion) {
  currentNotion = notion;
  currentPool   = allExercises.filter(e => e.notions.includes(notion));
  seenIndices   = [];

  if (currentPool.length === 0) {
    alert('Aucun exercice trouvé pour cette notion.');
    return;
  }

  homeView.classList.add('hidden');
  exerciseView.classList.remove('hidden');
  showRandomExercise();
}

function goHome() {
  exerciseView.classList.add('hidden');
  homeView.classList.remove('hidden');
  currentNotion = null;
  currentPool   = [];
  seenIndices   = [];
}

function nextExercise() {
  showRandomExercise();
}

// ── Exercise display ───────────────────────────────────────────
function showRandomExercise() {
  if (currentPool.length === 0) return;

  // Refill seen pool when exhausted
  if (seenIndices.length >= currentPool.length) {
    seenIndices = [];
  }

  // Pick a random index not yet seen
  const remaining = currentPool
    .map((_, i) => i)
    .filter(i => !seenIndices.includes(i));

  const pick = remaining[Math.floor(Math.random() * remaining.length)];
  seenIndices.push(pick);

  renderExercise(currentPool[pick]);
}

function renderExercise(ex) {
  // Badge
  notionBadge.textContent = NOTION_LABELS[currentNotion] || currentNotion;
  notionBadge.className   = `badge notion-badge ${currentNotion}`;

  pointsBadge.textContent = ex.points > 0 ? `${ex.points} points` : '';
  pointsBadge.style.display = ex.points > 0 ? '' : 'none';

  // Header
  exName.textContent = ex.exam;
  exNum.textContent  = ex.exercise;

  // Progress
  const seen  = seenIndices.length;
  const total = currentPool.length;
  progressText.textContent = `${seen} / ${total} vus`;
  counterHint.textContent  = `${total - seen} exercice${total - seen > 1 ? 's' : ''} restant${total - seen > 1 ? 's' : ''}`;

  // Content
  exContent.innerHTML = ex.content;

  // Re-run MathJax on the new content
  if (window.MathJax && MathJax.typesetPromise) {
    MathJax.typesetPromise([exContent]).catch(err => console.warn('MathJax error:', err));
  }

  // Scroll to top of exercise card
  exerciseView.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
