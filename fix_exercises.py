#!/usr/bin/env python3
"""
Clean up exercises.json:
1. Remove LaTeX spacing artifacts (9mm, 0mm, etc.)
2. Remove section/page markers (fancy empty, Index, M.E.P., etc.)
3. Remove exam-section anchor labels (Asie1, Polynesie, etc.)
4. Remove figure coordinate artifacts
5. Clean code blocks (remove |l| specs, fix $..$ in Python code)
6. Update figure onerror class: placeholder → fig-placeholder
"""
import re, json

with open('exercises.json', encoding='utf-8') as f:
    data = json.load(f)

EXAM_LABELS = [
    'Asie1','Asie2','Asie3',
    'Polynesie','Polynesia','Polynesie1','Polynesie2','Polynesie3',
    'AmeriqueNord1','AmeriqueNord2','AmeriqueNord3',
    'AmeriqueLatine1','AmeriqueLatine2',
    'AmeriqueSud1','AmeriqueSud2',
    'LaReunion','LaReunion1','LaReunion2',
    'Madagascar','Madagascar1',
    'Metropole','Metropole1','Metropole2','Metropole3','Metropole4',
    'Centres','Centresetrangers1','Centresetrangers2',
    'Liban','Antilles','France','Suede',
]

def clean(c):
    if not c:
        return c

    # 1. Remove spacing values before/after lists (9mm <ul> → <ul>)
    c = re.sub(r'\d+(?:\.\d+)?(?:mm|cm|pt|em)\s+(<(?:ul|ol)[\s>])', r'\1', c)
    c = re.sub(r'</(ul|ol)>\s*\d+(?:\.\d+)?(?:mm|cm|pt|em)', r'</\1>', c)
    # Also inside <p> when the measurement is alone before a closing </p>
    c = re.sub(r'<p>\s*\d+(?:\.\d+)?(?:mm|cm|pt|em)\s*</p>', '', c, flags=re.IGNORECASE)

    # 2. fancy empty, empty Xmm variants
    c = re.sub(r'<p>[^<]{0,30}fancy\s+empty[^<]{0,30}</p>', '', c, flags=re.IGNORECASE)
    c = re.sub(r'<p>\s*empty\s*\d*(?:mm|cm|pt|em)?\s*</p>', '', c, flags=re.IGNORECASE)

    # 3. M.E.P. / A.P.M.E.P. markers (various forms with 90A. prefix etc.)
    c = re.sub(r'<p>[^<]{0,40}(?:M\.\s*E\.\s*P\.|A\.\s*P\.\s*M\.\s*E\.\s*P\.)[^<]{0,60}</p>',
               '', c, flags=re.IGNORECASE)

    # 4. Index / Sommaire markers
    c = re.sub(r'<p>\s*(?:SommaireSommaire\s*)?(?:IndexIndex|Index)\s*</p>', '', c, flags=re.IGNORECASE)
    c = re.sub(r'<p>\s*SommaireSommaire\s*</p>', '', c, flags=re.IGNORECASE)

    # 5. Exam section label markers (anchor words, possibly doubled, with trailing %)
    for lbl in EXAM_LABELS:
        c = re.sub(r'<p>\s*(?:' + re.escape(lbl) + r'\s*){1,3}%?\s*</p>', '', c, flags=re.IGNORECASE)

    # 6. LaTeX comment lines (%%% fin ..., %...)
    c = re.sub(r'<p>\s*%%+[^<]{0,120}</p>', '', c)
    # Trailing comment text appended to real content before </p>
    c = re.sub(r'\s*%%%+[^\n<]{0,120}(?=\s*(?:<p>|</p>|\Z))', '', c)

    # 7. Figure coordinate artifacts (floating-point number sequences)
    c = re.sub(r'<p>\s*-?\d+(?:\.\d+)?(?:\s+-?\d+(?:\.\d+)?){1,6}\s*</p>', '', c)
    c = re.sub(r'<p>\s*\d+\.\d+\s*</p>', '', c)  # single float

    # 8. Clean code blocks
    def clean_code(m):
        code = m.group(1)
        # Remove tabular column specs at start: |l|, |>l >l| | l l |, 8cmc|X|, etc.
        code = re.sub(r'^[\s|>lcr@m\d]*\|[lcr>\s|@m\d]*[\s\n]*', '', code)
        # Remove l% prefix and trailing %
        code = re.sub(r'^l%\s*', '', code)
        code = re.sub(r'\s*%$', '', code)
        # Remove line-number+& prefix ("1 & ", " 2&", etc.)
        code = re.sub(r'(?m)^\s*\d+\s*&\s*', '', code)
        # Remove bare & (tabular column separators)
        code = re.sub(r'\s*&\s*', ' ', code)
        # Remove $ math delimiters around Python expressions
        code = re.sub(r'\$([A-Za-z_][A-Za-z0-9_ .=<>+\-*/(),]{0,40}?)\$', r'\1', code)
        # Remove \\$ escaped dollar signs
        code = re.sub(r'\\\$([^\\\n$]{1,60})\\\$', r'\1', code)
        # Fix [Xcm] [Xmm] LaTeX spacing artifacts (code blanks for student)
        code = re.sub(r'\[\d+(?:\.\d+)?(?:mm|cm|pt|em)\]', '...', code)
        # Fix French decimal comma → Python decimal dot in numeric literals
        code = re.sub(r'\b(\d+),(\d+)\b', r'\1.\2', code)
        # Remove leading import * artifact
        code = re.sub(r'(?m)^\s*\*\s*$', '', code)
        code = code.strip()
        if not code:
            return '<span class="placeholder">[Algorithme Python]</span>'
        return f'<pre><code>{code}</code></pre>'

    c = re.sub(r'<pre><code>(.*?)</code></pre>', clean_code, c, flags=re.DOTALL)

    # 9. Update figure placeholder class: placeholder → fig-placeholder
    c = c.replace(
        'class=\\"placeholder\\">[Figure – voir sujet original]',
        'class=\\"fig-placeholder\\">Figure – voir le sujet original'
    )

    # 10. Remove empty <p> left by removals
    c = re.sub(r'<p>\s*</p>', '', c)
    # Collapse 3+ newlines
    c = re.sub(r'\n{3,}', '\n\n', c)

    return c.strip()

for ex in data['exercises']:
    ex['content'] = clean(ex['content'])

with open('exercises.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Done. {len(data['exercises'])} exercises written.")

# Verify
with open('exercises.json', encoding='utf-8') as f:
    check = json.load(f)
print(f"Validation: {len(check['exercises'])} exercises (JSON valid)")
