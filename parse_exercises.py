#!/usr/bin/env python3
"""
Parse annales_maths_2021_2025.tex and extract exercises classified by notion.
- Outputs exercises.json
- Extracts PSTricks figures as standalone .tex files in figures/
  Run compile_figures.sh after installing MacTeX to render them as PNG.
"""

import re
import json
import os

TEX_FILE    = '/Users/petrinolann/Downloads/annales_maths_2021_2025.tex'
OUTPUT_FILE = '/Users/petrinolann/maths_shuffle/exercises.json'
FIGURES_DIR = '/Users/petrinolann/maths_shuffle/figures'

os.makedirs(FIGURES_DIR, exist_ok=True)


# ============================================================
# CLASSIFICATION
# ============================================================

NOTION_KEYWORDS = {
    'probabilites': [
        'probabilit', 'variable aléatoire', 'loi de bernoulli', 'loi binomiale',
        'loi normale', 'espérance', 'variance', 'écart-type', 'fluctuation',
        'arbre pondéré', 'arbre de probabilité', 'p(x', 'p(a|', 'p(b|', 'p(a )',
        'probabilité conditionnelle', 'événement ', 'loi suivie',
        'échantillonnage', 'p(t) =', 'loi géométrique', 'loi de poisson',
        'covariance', 'test positif', 'test négatif', 'test anti-',
        'est dopé', 'est infecté', 'est malade',
    ],
    'suites': [
        'la suite ', 'les suites', 'une suite', 'suite (', 'suite $',
        'u_n', 'u_{n', 'v_n', 'v_{n', 'w_n', 'u_0', 'u_1', 'u_2',
        'récurrence', 'suite arithmétique', 'suite géométrique',
        'terme général', 'suite convergente', 'suite divergente',
        'suite croissante', 'suite décroissante', 'suite est',
        'par récurrence', 'limite de la suite', 'u_{n+1}',
    ],
    'fonctions': [
        'la fonction f', 'la fonction $f', 'fonction f est', 'courbe représentative',
        'tableau de variation', 'dérivée', "f'(x)", "f''(x)", 'primitive de',
        'une primitive', 'intégrale', 'asymptote', 'tangente à',
        'logarithme', 'exponentielle', 'ln(', 'e^{',
        'équation différentielle', 'convexe', "point d'inflexion",
        'extremum', 'maximum de f', 'minimum de f', 'étude de f',
        'f est croissante', 'f est décroissante', 'f est définie',
        r'la courbe $\mathcal{c}', 'représentative de f',
    ],
    'geometrie': [
        "dans l'espace", 'dans le plan', r'\vect{', 'overrightarrow',
        'coplanaire', 'vecteurs ', 'vecteur $', 'produit scalaire',
        'équation cartésienne', 'équation paramétrique', 'repère orthonormé',
        'repère $', 'distance entre', 'projection', 'vecteur normal',
        'cube ', 'pyramide', 'tétraèdre', 'sphère', 'boule ',
        r'plan $\mathcal', 'droite $d', 'droite (', 'le plan (',
        'parallèle', 'perpendiculaire', 'milieu du segment',
        'parallélépipède', 'solide', 'repère orthonormé',
    ],
}

THEME_NOTION_MAP = {
    'probabilit': 'probabilites', 'variable aléatoire': 'probabilites',
    'loi de': 'probabilites',     'statistique': 'probabilites',
    'suite':    'suites',
    'fonction': 'fonctions',      'logarithme':  'fonctions',
    'exponentielle': 'fonctions', 'primitive':   'fonctions',
    'intégrale': 'fonctions',     'numérique':   'fonctions',
    'étude de': 'fonctions',      'différentielle': 'fonctions',
    'géométrie': 'geometrie',     'geometrie':   'geometrie',
    'espace': 'geometrie',        'plan et dans': 'geometrie',
    'vecteur': 'geometrie',
}


def classify_from_theme(theme_str):
    theme_lower = theme_str.lower()
    return list({notion for kw, notion in THEME_NOTION_MAP.items() if kw in theme_lower})


def classify_from_content(text):
    text_lower = text.lower()
    notions = {n for n, kws in NOTION_KEYWORDS.items() if any(kw in text_lower for kw in kws)}
    return list(notions) if notions else ['fonctions']


def classify_exercise(header_line, content_text):
    # 1. Explicit Thème: tag
    theme_match = re.search(
        r'[Tt]hèm[es]*\s*[:\s]+([^\\}{%\n]+?)(?=\\hfill|\\index|\}%?$|\n|\\\\)',
        header_line)
    if theme_match:
        raw = re.sub(r'\\[a-zA-Z]+|[{}]', '', theme_match.group(1)).strip()
        notions = classify_from_theme(raw)
        if notions:
            return notions

    # 2. Notion keyword after \hfill without "Thème:"
    hfill_match = re.search(r'\\hfill\s+([a-zA-Zéèàêîôûùàç ,]+)(?=\}|%|$)', header_line)
    if hfill_match:
        after = hfill_match.group(1).strip()
        if 5 < len(after) < 80:
            notions = classify_from_theme(after)
            if notions:
                return notions

    # 3. Notion in exercise label: "Exercice 1 Probabilités"
    label_match = re.search(r'Exercice\s+\w+\s+([A-ZÉÀÊ][a-zA-Zéèàêîôûùàç, ]+?)(?=\\|$|\})',
                            header_line)
    if label_match:
        notions = classify_from_theme(label_match.group(1).strip())
        if notions:
            return notions

    # 4. Domain table inside content
    domain_match = re.search(r'Principaux domaines abordés.*?(?=\\end\{tabular)',
                             content_text, re.DOTALL | re.IGNORECASE)
    if domain_match:
        notions = classify_from_theme(domain_match.group(0))
        if notions:
            return notions

    # 5. Full content keyword scan
    return classify_from_content(header_line + '\n' + content_text)


# ============================================================
# PREAMBLE FOR STANDALONE FIGURE FILES
# ============================================================

FIGURE_PREAMBLE = r"""\documentclass[12pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,mathrsfs}
\usepackage{pst-all,pst-func,pst-3dplot,pst-eucl}
\usepackage{multido,color}
\newcommand{\R}{\mathbb{R}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\D}{\mathbb{D}}
\newcommand{\Z}{\mathbb{Z}}
\newcommand{\Q}{\mathbb{Q}}
\newcommand{\C}{\mathbb{C}}
\newcommand{\vect}[1]{\overrightarrow{\,\mathstrut#1\,}}
\newcommand{\barre}[1]{\overline{\,\mathstrut#1\,}}
\newcommand{\pg}{\geqslant}
\newcommand{\pp}{\leqslant}
\newcommand{\e}{\,\text{e}\,}
\renewcommand{\d}{\,\text{d}}
\newcommand{\Cg}{\texttt{]}}
\newcommand{\Cd}{\texttt{[}}
\def\Oij{$\left(\text{O}\,;\,\vec{\imath},\,\vec{\jmath}\right)$}
\def\Oijk{$\left(\text{O}\,;\,\vec{\imath},\,\vec{\jmath},\,\vec{k}\right)$}
\pagestyle{empty}
\begin{document}
"""


# ============================================================
# FIGURE EXTRACTION
# ============================================================

FIGURE_BLOCK_RE = re.compile(
    r'(?:(?:\\psset\{[^}]*\}|\\def\\f[^\n]*)\s*)*'
    r'\\begin\{pspicture\*?\}.*?\\end\{pspicture\*?\}',
    re.DOTALL
)

CENTER_FIGURE_RE = re.compile(
    r'\\begin\{center\}\s*'
    r'(?:(?:\\psset\{[^}]*\}|\\def\\f[^\n]*|%[^\n]*\n)\s*)*'
    r'\\begin\{pspicture\*?\}.*?\\end\{pspicture\*?\}'
    r'\s*\\end\{center\}',
    re.DOTALL
)


def extract_and_replace_figures(raw_latex, exercise_id):
    fig_idx = [0]

    def replace_figure(match_text, is_center_wrapped):
        n = fig_idx[0]
        fig_idx[0] += 1
        stem = f'ex_{exercise_id:03d}_fig_{n}'
        tex_path = os.path.join(FIGURES_DIR, stem + '.tex')

        body = match_text if is_center_wrapped else f'\\begin{{center}}\n{match_text}\n\\end{{center}}'
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(FIGURE_PREAMBLE)
            f.write(body)
            f.write('\n\\end{document}\n')

        return f'\n__FIGURE_{stem}__\n'

    modified = raw_latex
    for m in list(CENTER_FIGURE_RE.finditer(raw_latex)):
        repl = replace_figure(m.group(0), is_center_wrapped=True)
        modified = modified.replace(m.group(0), repl, 1)

    for m in list(FIGURE_BLOCK_RE.finditer(modified)):
        if '\\begin{pspicture' in m.group(0):
            repl = replace_figure(m.group(0), is_center_wrapped=False)
            modified = modified.replace(m.group(0), repl, 1)

    return modified


# ============================================================
# LATEX → HTML CONVERSION
# ============================================================

def latex_to_html(text, exercise_id):

    # ── Protect math ─────────────────────────────────────────
    math_blocks = []

    def protect(match):
        idx = len(math_blocks)
        math_blocks.append(match.group(0))
        return f'__M{idx}__'

    for env in ['align', 'align*', 'gather', 'gather*', 'equation', 'equation*',
                'eqnarray', 'eqnarray*', 'multline', 'multline*', 'flalign', 'flalign*']:
        safe = re.escape(env)
        text = re.sub(rf'\\begin\{{{safe}\}}[\s\S]*?\\end\{{{safe}\}}', protect, text)

    text = re.sub(r'\\\[[\s\S]*?\\\]', protect, text)
    text = re.sub(r'\$\$[\s\S]*?\$\$', protect, text)
    text = re.sub(r'\$[^\$\n]{1,300}\$', protect, text)

    # ── Strip LaTeX comments (% to end of line) outside math ──
    text = re.sub(r'(?m)%[^\n]*$', '', text)

    # ── Remove page/layout/navigation commands ────────────────
    text = re.sub(r'\\index\{[^}]*\}', '', text)
    text = re.sub(r'\\(?:lhead|rhead|chead|lfoot|rfoot|fancyhead|fancyfoot)\{[^}]*\}', '', text)
    text = re.sub(r'\\(?:newpage|clearpage|cleardoublepage|pagebreak)\b', '', text)
    text = re.sub(r'\\(?:setlength|setcounter)\{[^}]*\}\{[^}]*\}', '', text)
    # \setlength\cmd{val} form (no braces around first arg)
    text = re.sub(r'\\(?:setlength|addtolength)\\[a-zA-Z@]+\{[^}]*\}', '', text)
    # Page style commands
    text = re.sub(r'\\(?:pagestyle|thispagestyle)\{[^}]*\}', '', text)
    # Hyperref / label / cross-reference commands
    text = re.sub(r'\\(?:hypertarget|hyperlink)\{[^}]*\}\{[^}]*\}', '', text)
    text = re.sub(r'\\(?:label|ref|pageref|autoref|eqref|nameref)\{[^}]*\}', '', text)

    # ── Remaining PSTricks ────────────────────────────────────
    text = re.sub(r'\\begin\{pspicture\*?\}[\s\S]*?\\end\{pspicture\*?\}',
                  '<span class="placeholder">[Figure géométrique]</span>', text)
    text = re.sub(r'\\psset\{[^}]*\}', '', text)
    text = re.sub(r'\\ps[a-zA-Z]+[^%\n]*', '', text)
    text = re.sub(r'\\uput[^%\n]*', '', text)
    text = re.sub(r'\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}',
                  '<span class="placeholder">[Figure]</span>', text)

    # ── Code listings ─────────────────────────────────────────
    text = re.sub(r'\\begin\{lstlisting\}([\s\S]*?)\\end\{lstlisting\}',
                  lambda m: '<pre><code>' + m.group(1).strip() + '</code></pre>', text)
    text = re.sub(r'\\begin\{verbatim\}([\s\S]*?)\\end\{verbatim\}',
                  lambda m: '<pre><code>' + m.group(1).strip() + '</code></pre>', text)

    # ── Tables ────────────────────────────────────────────────
    def maybe_code_table(m):
        content = m.group(0)
        if not re.search(r'\bdef\b|\breturn\b|\bwhile\b|\bfor\b|\bif\b', content):
            return '<span class="placeholder">[Tableau]</span>'

        # Strip LaTeX comments before splitting
        content = re.sub(r'%[^\n]*', '', content)

        lines = re.split(r'\\\\', content)
        code_lines = []
        for line in lines:
            # Indentation: \quad → 4 spaces, \qquad → 8 spaces, \hspace{xcm} → 4 spaces
            line = re.sub(r'\\qquad\s*', '        ', line)
            line = re.sub(r'\\(?:quad|hspace\{[^}]*\})\s*', '    ', line)
            # Resolve \np{number} → number before generic strip
            line = re.sub(r'\\np\{([^}]+)\}', lambda x: re.sub(r'\s', '', x.group(1)), line)
            # Strip begin/end/hline explicitly
            line = re.sub(r'\\(?:begin|end)\{[^}]*\}(?:\[[^\]]*\]|\{[^}]*\})*', '', line)
            line = re.sub(r'\\hline\b', '', line)
            # Strip remaining LaTeX commands
            line = re.sub(r'\\[a-zA-Z]+\*?(?:\{[^}]*\})?', '', line)
            # Strip braces and pipe chars (column spec artifacts)
            line = re.sub(r'[{}|]', '', line).strip()
            # Fix Python decimal commas (French notation → Python)
            line = re.sub(r'(\d),(\d)', r'\1.\2', line)
            # Skip empty lines, column specs, begin/end artifacts
            if line and not re.match(r'^[lcr@\s]+$', line):
                code_lines.append(line)

        if code_lines:
            return '<pre><code>' + '\n'.join(code_lines) + '</code></pre>'
        return '<span class="placeholder">[Tableau]</span>'

    text = re.sub(r'\\begin\{tabular[x]?\}(?:[^{]*\{[^}]*\}|\s)([\s\S]*?)\\end\{tabular[x]?\}',
                  maybe_code_table, text)

    # ── Lists ─────────────────────────────────────────────────
    for _ in range(4):
        def conv_enum(m):
            items = [i.strip() for i in re.split(r'\\item(?:\[[^\]]*\])?\s*', m.group(1)) if i.strip()]
            # Collapse double newlines within items to prevent <p> nesting later
            items = [re.sub(r'\s*\n\n+\s*', '\n', item) for item in items]
            return '<ol>' + ''.join(f'<li>{i}</li>' for i in items) + '</ol>'

        def conv_item(m):
            items = [i.strip() for i in re.split(r'\\item(?:\[[^\]]*\])?\s*', m.group(1)) if i.strip()]
            items = [re.sub(r'\s*\n\n+\s*', '\n', item) for item in items]
            return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'

        text = re.sub(r'\\begin\{enumerate\}(?:\[[^\]]*\])?([\s\S]*?)\\end\{enumerate\}', conv_enum, text)
        text = re.sub(r'\\begin\{itemize\}(?:\[[^\]]*\])?([\s\S]*?)\\end\{itemize\}', conv_item, text)

    # ── Text formatting ───────────────────────────────────────
    for _ in range(5):
        text = re.sub(r'\\textbf\{([^{}]*)\}',   r'<strong>\1</strong>', text)
        text = re.sub(r'\\textit\{([^{}]*)\}',   r'<em>\1</em>', text)
        text = re.sub(r'\\emph\{([^{}]*)\}',      r'<em>\1</em>', text)
        text = re.sub(r'\\textsc\{([^{}]*)\}',   r'\1', text)
        text = re.sub(r'\\textrm\{([^{}]*)\}',   r'\1', text)
        text = re.sub(r'\\text[a-z]{0,2}\{([^{}]*)\}', r'\1', text)
        text = re.sub(r'\\underline\{([^{}]*)\}', r'<u>\1</u>', text)
        text = re.sub(r'\\mbox\{([^{}]*)\}',      r'\1', text)
        text = re.sub(r'\\fbox\{([^{}]*)\}',      r'<span class="fbox">\1</span>', text)
        text = re.sub(r'\\footnote\{[^{}]*\}',    '', text)

    # ── Environments ─────────────────────────────────────────
    text = re.sub(r'\\begin\{center\}([\s\S]*?)\\end\{center\}', r'\n\n\1\n\n', text)
    text = re.sub(r'\\begin\{minipage\}(?:\[[^\]]*\])?\{[^}]*\}([\s\S]*?)\\end\{minipage\}', r'\1', text)
    text = re.sub(r'\\begin\{[a-zA-Z*]+\}(?:\[[^\]]*\])?(?:\{[^}]*\})?', '', text)
    text = re.sub(r'\\end\{[a-zA-Z*]+\}', '', text)

    # ── Custom commands ───────────────────────────────────────
    text = re.sub(r'\\np\{([\d\s,. ]+)\}',  lambda m: re.sub(r'\s', '', m.group(1)), text)
    text = re.sub(r'\\no\b', 'n°', text)
    text = re.sub(r'\\No\b', 'N°', text)
    text = re.sub(r'\\euro\{\}?', '€', text)
    text = re.sub(r'\\og\s*', '« ', text)
    text = re.sub(r'\\fg(?:\{\})?', ' »', text)
    text = re.sub(r'\\dots\b|\\ldots\b', '…', text)

    # ── Spacing ───────────────────────────────────────────────
    text = re.sub(r'\\(?:vspace|hspace|kern)\*?\{[^}]*\}', ' ', text)
    text = re.sub(r'\\(?:medskip|bigskip|smallskip|vskip|hskip)\b[^\n]*\n?', '\n\n', text)
    text = re.sub(r'\\(?:noindent|indent|centering|raggedright|raggedleft)\b', '', text)
    text = re.sub(r'\\hfill\b', ' ', text)
    text = re.sub(r'\\(?:quad|qquad)[^a-zA-Z]', ' ', text)
    text = re.sub(r'\\newline\b', '<br>', text)
    text = re.sub(r'\\par\b', '\n\n', text)
    text = re.sub(r'~', ' ', text)
    text = re.sub(r'\\\\(?:\[[^\]]*\])?', '<br>', text)
    text = re.sub(r'---', '—', text); text = re.sub(r'--', '–', text)

    # ── Strip remaining LaTeX ─────────────────────────────────
    for _ in range(6):
        prev = text
        text = re.sub(r'\\[a-zA-Z]+\*?\{([^{}]*)\}', r'\1', text)
        if text == prev:
            break
    text = re.sub(r'\\[a-zA-Z@]+\*?(?:\[[^\]]*\])*', '', text)
    text = re.sub(r'[{}]', '', text)

    # ── Paragraphs ────────────────────────────────────────────
    text = re.sub(r'\n{3,}', '\n\n', text.strip())
    text = re.sub(r'[ \t]+', ' ', text)

    blocks = re.split(r'\n\n+', text)
    result_parts = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if re.match(r'^<(ol|ul|pre|li|span class="placeholder")', block):
            result_parts.append(block)
        elif block.startswith('__FIGURE_'):
            result_parts.append(block)
        else:
            result_parts.append(f'<p>{block.replace(chr(10), " ").strip()}</p>')

    text = '\n'.join(result_parts)

    # ── Restore math ─────────────────────────────────────────
    for idx, block in enumerate(math_blocks):
        text = text.replace(f'__M{idx}__', block)

    # ── Convert figure tokens to HTML ────────────────────────
    def fig_token_to_html(m):
        stem = m.group(1)
        return (
            f'<figure class="exercise-fig">'
            f'<img src="figures/{stem}.png" alt="Figure" '
            f'onerror="this.parentElement.innerHTML=\'<span class=\\\"placeholder\\\">'
            f'[Figure – voir sujet original]</span>\'">'
            f'</figure>'
        )
    text = re.sub(r'__FIGURE_(ex_\d+_fig_\d+)__', fig_token_to_html, text)

    return text


# ============================================================
# PARSING
# ============================================================

EXAM_LINE_RE = re.compile(
    r'\\begin\{center\}.*?(?:\\Large|\\huge).*?Baccalauréat|'
    r'\\(?:Large|huge).*?Baccalauréat',
    re.IGNORECASE
)

EXERCISE_HEADER_RE = re.compile(
    r'\\textbf\{[^}]*?Exercice\s+([0-9]+|[AB])\b',
    re.IGNORECASE
)

POINTS_RE = re.compile(r'(\d+)\s*points?', re.IGNORECASE)


def extract_exam_name(line):
    m = re.search(r'\\decofourleft~?\s*(.*?)\s*~?\\decofourright', line, re.IGNORECASE)
    if m:
        name = m.group(1)
    else:
        m2 = re.search(r'Baccalauréat\s*(.+?)(?=\}|\\\\|\n)', line)
        name = 'Baccalauréat ' + (m2.group(1) if m2 else '')
    name = re.sub(r'\\[a-zA-Z]+\*?(?:\{[^}]*\}|\[[^\]]*\])?', ' ', name)
    name = re.sub(r'[\\\{\}~\[\]]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip()[:120]


def parse_tex(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    exercises        = []
    current_exam     = 'Baccalauréat'
    current_meta     = None
    current_lines    = []
    exercise_id      = 0

    def flush():
        nonlocal current_meta
        if current_meta is None:
            return
        raw = ''.join(current_lines).strip()
        if len(raw) < 30:
            current_meta = None; current_lines.clear(); return

        raw_with_tokens = extract_and_replace_figures(raw, current_meta['id'])
        notions = classify_exercise(current_meta['header'], raw)
        html    = latex_to_html(raw_with_tokens, current_meta['id'])

        exercises.append({
            'id':       current_meta['id'],
            'exam':     current_meta['exam'],
            'exercise': current_meta['label'],
            'points':   current_meta['points'],
            'notions':  sorted(set(notions)),
            'content':  html,
        })
        current_meta = None
        current_lines.clear()

    for line in lines:
        if EXAM_LINE_RE.search(line) and 'Baccalauréat' in line:
            flush()
            current_exam = extract_exam_name(line)
            continue

        ex_match = EXERCISE_HEADER_RE.search(line)
        if ex_match:
            flush()
            exercise_id += 1
            ex_num = ex_match.group(1).upper()
            pts_m  = POINTS_RE.search(line)
            current_meta = {
                'id':     exercise_id,
                'exam':   current_exam,
                'label':  f'Exercice {ex_num}',
                'points': int(pts_m.group(1)) if pts_m else 0,
                'header': line,
            }
            continue

        if current_meta is not None:
            current_lines.append(line)

    flush()
    return exercises


# ============================================================
# MAIN
# ============================================================

def main():
    print(f'Parsing {TEX_FILE} ...')
    exercises = parse_tex(TEX_FILE)
    print(f'Found {len(exercises)} exercises')

    counts = {'fonctions': 0, 'suites': 0, 'geometrie': 0, 'probabilites': 0}
    for ex in exercises:
        for n in ex['notions']:
            if n in counts:
                counts[n] += 1

    print('Distribution:')
    for notion, count in counts.items():
        print(f'  {notion}: {count}')

    fig_tex = [f for f in os.listdir(FIGURES_DIR) if f.endswith('.tex')]
    print(f'\nFigure .tex files written: {len(fig_tex)}')

    output = {'version': 2, 'total': len(exercises), 'exercises': exercises}
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(OUTPUT_FILE) // 1024
    print(f'Saved → {OUTPUT_FILE} ({size_kb} KB)')


if __name__ == '__main__':
    main()
