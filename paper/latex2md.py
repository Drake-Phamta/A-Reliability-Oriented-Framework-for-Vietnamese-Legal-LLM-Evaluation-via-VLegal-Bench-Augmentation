#!/usr/bin/env python3
"""Convert main.tex to markdown for review — improved version with table rendering."""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('main.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove comments
lines = content.split('\n')
lines = [l for l in lines if not l.strip().startswith('%')]
content = '\n'.join(lines)

# Remove preamble
if r'\begin{document}' in content:
    content = content.split(r'\begin{document}', 1)[1]
if r'\end{document}' in content:
    content = content.split(r'\end{document}', 1)[0]


def clean_latex(s):
    """Clean LaTeX commands from a string."""
    s = re.sub(r'\\textbf\{([^}]*)\}', r'**\1**', s)
    s = re.sub(r'\\textit\{([^}]*)\}', r'*\1*', s)
    s = re.sub(r'\\emph\{([^}]*)\}', r'*\1*', s)
    s = re.sub(r'\\texttt\{([^}]*)\}', r'`\1`', s)
    s = re.sub(r'\\citacc', 'CitAcc', s)
    s = re.sub(r'\\ras', 'RAS', s)
    s = re.sub(r'\\rar', 'RAR', s)
    s = re.sub(r'\\esr', 'ESR', s)
    s = re.sub(r'\\ucr', 'UCR', s)
    s = re.sub(r'\\absacc', 'AbsAcc', s)
    s = re.sub(r'\\rougel\{\}', 'ROUGE-L', s)
    s = re.sub(r'\\system\{\}', 'VLegal-Bench', s)
    s = re.sub(r'\\model\{\}', 'Gemma 4 E4B', s)
    s = re.sub(r'\\multirow\{\d+\}\{[^}]*\}\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\multicolumn\{\d+\}\{[^}]*\}\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\[a-zA-Z]+', '', s)
    s = s.replace('{', '').replace('}', '')
    s = s.strip()
    return s


def parse_table(table_text):
    """Parse a LaTeX tabular environment into a markdown table."""
    # Extract caption
    cap_match = re.search(r'\\caption\{(.+?)\}', table_text, re.DOTALL)
    caption = clean_latex(cap_match.group(1)) if cap_match else ''

    # Find tabular content
    tab_match = re.search(r'\\begin\{tabular\}\{[^}]*\}(.*?)\\end\{tabular\}', table_text, re.DOTALL)
    if not tab_match:
        return f'\n> **[TABLE]** {caption}\n'

    tab_content = tab_match.group(1)

    # Remove \toprule, \midrule, \bottomrule, \cmidrule
    tab_content = re.sub(r'\\toprule', '', tab_content)
    tab_content = re.sub(r'\\midrule', '', tab_content)
    tab_content = re.sub(r'\\bottomrule', '', tab_content)
    tab_content = re.sub(r'\\cmidrule\([^)]*\)\{[^}]*\}', '', tab_content)

    # Split into rows
    rows = []
    for line in tab_content.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('%'):
            continue
        # Split by &
        cells = [clean_latex(c.strip()) for c in line.split('&')]
        # Remove trailing \\ from last cell
        if cells and cells[-1].endswith('\\\\'):
            cells[-1] = cells[-1].rstrip('\\\\').strip()
        if cells and cells[-1] == '\\\\':
            cells = cells[:-1]
        if any(c.strip() for c in cells):
            rows.append(cells)

    if not rows:
        return f'\n> **[TABLE]** {caption}\n'

    # Determine number of columns
    max_cols = max(len(r) for r in rows)

    # Pad rows to same length
    for r in rows:
        while len(r) < max_cols:
            r.append('')

    # Build markdown table
    md_lines = []
    md_lines.append('| ' + ' | '.join(rows[0]) + ' |')
    md_lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
    for row in rows[1:]:
        md_lines.append('| ' + ' | '.join(row) + ' |')

    table_md = '\n'.join(md_lines)
    return f'\n**Table:** {caption}\n\n{table_md}\n'


def parse_figure(fig_text):
    """Parse a LaTeX figure environment."""
    cap_match = re.search(r'\\caption\{(.+?)\}', fig_text, re.DOTALL)
    caption = clean_latex(cap_match.group(1)) if cap_match else 'Figure'
    return f'\n**Figure:** {caption}\n\n[Figure: {caption}]\n'


# Process tables
content = re.sub(r'\\begin\{table\}.*?\\end\{table\}', lambda m: parse_table(m.group(0)), content, flags=re.DOTALL)

# Process figures
content = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', lambda m: parse_figure(m.group(0)), content, flags=re.DOTALL)

# Abstract
content = re.sub(r'\\begin\{abstract\}', '\n## Abstract\n', content)
content = re.sub(r'\\end\{abstract\}', '\n', content)

# Sections
content = re.sub(r'\\section\{(.+?)\}', r'\n## \1\n', content)
content = re.sub(r'\\subsection\{(.+?)\}', r'\n### \1\n', content)
content = re.sub(r'\\subsubsection\{(.+?)\}', r'\n#### \1\n', content)
content = re.sub(r'\\paragraph\{(.+?)\}', r'\n**\1.** ', content)

# Text formatting
content = re.sub(r'\\textbf\{(.+?)\}', r'**\1**', content)
content = re.sub(r'\\textit\{(.+?)\}', r'*\1*', content)
content = re.sub(r'\\emph\{(.+?)\}', r'*\1*', content)
content = re.sub(r'\\texttt\{(.+?)\}', r'`\1`', content)
content = re.sub(r'\\textsuperscript\{(.+?)\}', r'^\1^', content)

# Citations
content = re.sub(r'~?\\citep\{([^}]+)\}', lambda m: ' [' + m.group(1).replace(',', ', ') + ']', content)
content = re.sub(r'~?\\citet\{([^}]+)\}', lambda m: ' [' + m.group(1).replace(',', ', ') + ']', content)

# Custom commands
content = content.replace(r'\system{}', 'VLegal-Bench')
content = content.replace(r'\model{}', 'Gemma 4 E4B')
content = content.replace(r'\citacc', 'CitAcc')
content = content.replace(r'\ras', 'RAS')
content = content.replace(r'\rar', 'RAR')
content = content.replace(r'\esr', 'ESR')
content = content.replace(r'\ucr', 'UCR')
content = content.replace(r'\absacc', 'AbsAcc')
content = content.replace(r'\rougel{}', 'ROUGE-L')
content = content.replace(r'\rougel', 'ROUGE-L')

# Lists
content = re.sub(r'\\begin\{enumerate\}\[[^\]]*\]', '', content)
content = re.sub(r'\\begin\{itemize\}\[[^\]]*\]', '', content)
content = content.replace(r'\begin{enumerate}', '')
content = content.replace(r'\begin{itemize}', '')
content = content.replace(r'\end{enumerate}', '')
content = content.replace(r'\end{itemize}', '')
content = re.sub(r'\\item\s+', '\n- ', content)

# Math — convert to readable form
def convert_math(m):
    expr = m.group(1)
    # Simple conversions
    expr = expr.replace(r'\pi_\theta', 'pi_theta')
    expr = expr.replace(r'\pi_{\text{ref}}', 'pi_ref')
    expr = expr.replace(r'\mathcal{L}', 'L')
    expr = expr.replace(r'\text{DPO}', 'DPO')
    expr = expr.replace(r'\mathbb{E}', 'E')
    expr = expr.replace(r'\log', 'log')
    expr = expr.replace(r'\sigma', 'sigma')
    expr = expr.replace(r'\beta', 'beta')
    expr = expr.replace(r'\rightarrow', '->')
    expr = expr.replace(r'\leftarrow', '<-')
    expr = expr.replace(r'\leq', '<=')
    expr = expr.replace(r'\geq', '>=')
    expr = expr.replace(r'\neq', '!=')
    expr = expr.replace(r'\times', 'x')
    expr = expr.replace(r'\cdot', '.')
    expr = expr.replace(r'\ldots', '...')
    expr = expr.replace(r'\quad', ' ')
    expr = expr.replace(r'\,', ' ')
    expr = expr.replace(r'\;', ' ')
    expr = expr.replace(r'\left', '')
    expr = expr.replace(r'\right', '')
    expr = re.sub(r'\\text\{([^}]*)\}', r'\1', expr)
    expr = re.sub(r'\\mathrm\{([^}]*)\}', r'\1', expr)
    expr = re.sub(r'\\mathbf\{([^}]*)\}', r'\1', expr)
    expr = expr.strip()
    return f'`{expr}`'

content = re.sub(r'\$([^$]+?)\$', convert_math, content)

# Display math (equation environments)
content = re.sub(r'\\begin\{equation\}', '\n```\n', content)
content = re.sub(r'\\end\{equation\}', '\n```\n', content)

# Labels and refs
content = re.sub(r'\\label\{[^}]+\}', '', content)
content = re.sub(r'\\ref\{[^}]+\}', '[ref]', content)

# URLs
content = re.sub(r'\\url\{([^}]+)\}', r'[\1](\1)', content)
content = re.sub(r'\\footnote\{\\url\{([^}]+)\}\}', r' ([\1](\1))', content)

# Vietnamese diacritics
vn_map = {
    r"\'{a}": 'á', r"\'{e}": 'é', r"\'{i}": 'í', r"\'{o}": 'ó', r"\'{u}": 'ú',
    r"\'{A}": 'Á', r"\'{E}": 'É', r"\'{I}": 'Í', r"\'{O}": 'Ó', r"\'{U}": 'Ú',
    r"\`{a}": 'à', r"\`{e}": 'è', r"\`{i}": 'ì', r"\`{o}": 'ò', r"\`{u}": 'ù',
    r"\~{a}": 'ã', r"\~{e}": 'ẽ', r"\~{i}": 'ĩ', r"\~{o}": 'õ', r"\~{u}": 'ũ',
    r"\.{a}": 'ạ', r"\.{e}": 'ẹ', r"\.{i}": 'ị', r"\.{o}": 'ọ', r"\.{u}": 'ụ',
    r"\^{a}": 'â', r"\^{e}": 'ê', r"\^{i}": 'î', r"\^{o}": 'ô', r"\^{u}": 'û',
    r'\^{o}': 'ô', r'\^{e}': 'ê', r'\^{a}': 'â',
    r"\'{o}": 'ó', r"\'{a}": 'á',
    r'\v{D}': 'Đ', r'\v{d}': 'đ',
    r'\u{o}': 'ơ', r'\u{u}': 'ư',
    r'\h{o}': 'ơ', r'\h{u}': 'ư',
    r'\d{a}': 'ạ', r'\d{e}': 'ẹ', r'\d{o}': 'ọ',
}
for k, v in vn_map.items():
    content = content.replace(k, v)

# Remaining common commands
content = content.replace(r'\noindent', '')
content = content.replace(r'\balance', '')
content = content.replace(r'\newpage', '')
content = re.sub(r'\\vspace\{[^}]*\}', '', content)
content = re.sub(r'\\hspace\{[^}]*\}', '', content)

# Clean remaining LaTeX commands
content = re.sub(r'\\label\{[^}]*\}', '', content)
content = re.sub(r'\\ref\{[^}]*\}', '[ref]', content)
content = re.sub(r'\\[a-zA-Z]+\*?\{', '', content)
content = re.sub(r'\\[a-zA-Z]+\*?', '', content)

# Braces
content = content.replace('{', '').replace('}', '')

# Special chars
content = content.replace(r'\%', '%')
content = content.replace(r'\&', '&')
content = content.replace(r'\#', '#')
content = content.replace(r'\$', '$')
content = content.replace(r'---', '---')
content = content.replace(r'--', '–')
content = content.replace(r"``", '"')
content = content.replace(r"''", '"')
content = content.replace(r'\,', ' ')

# Fix common artifacts
content = content.replace('~pp', ' pp')
content = content.replace(r'\~pp', ' pp')
content = re.sub(r'vs\.\\', 'vs.', content)
content = content.replace('" ', ' → ')
content = content.replace('"', ' → ')

# Fix double-bold artifacts
content = content.replace('****', '**')

# Fix paragraph artifacts
content = re.sub(r'Ablation rationale\.\.', '**Ablation rationale.**', content)
content = re.sub(r'Finding (\d+): (.+?)\.\.', r'**Finding \1: \2.**', content)
content = re.sub(r'Direct Preference Optimization \(DPO\)\.\.', '**Direct Preference Optimization (DPO).**', content)
content = re.sub(r'Theoretical Grounding: (.+?)\.\.', r'**Theoretical Grounding: \1.**', content)
content = re.sub(r'Confidence-Calibrated Abstention\.\.', '**Confidence-Calibrated Abstention.**', content)
content = re.sub(r'Problem Formulation\.\.', '**Problem Formulation.**', content)
content = re.sub(r'RAFT-AT Data Construction\.\.', '**RAFT-AT Data Construction.**', content)

# Clean up whitespace
content = re.sub(r'\n{3,}', '\n\n', content)
content = re.sub(r' +', ' ', content)
content = content.strip()

with open('REVIEW.md', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Written {len(content)} chars to REVIEW.md')
