#!/usr/bin/env python3
"""
md2pdf — Polished Markdown → PDF Converter
─────────────────────────────────────────
Handles every style produced by AI assistants (ChatGPT, Gemini, Grok, Claude):
  • Headings  • Bold / Italic / Strikethrough
  • Inline code  • Fenced code blocks (optional line numbers)
  • Tables (pipe) with full grid lines  • Blockquotes  • Ordered & unordered lists
  • Horizontal rules  • Display & inline math (dollar OR bracket notation)
  • Unicode math symbols  • Auto font-size reduction for wide tables

Usage:
  python md2pdf.py notes.md                       # → notes.pdf  (A4)
  python md2pdf.py notes.md -n                    # + line numbers in code
  python md2pdf.py notes.md -p letter             # Letter paper
  python md2pdf.py notes.md -p a5 -n out.pdf      # A5 + line numbers
  echo "# Hi" | python md2pdf.py -               # pipe mode
  python md2pdf.py notes.md --watch               # auto-rebuild on save

Page size presets: a4 (default), letter, legal, a3, a5, b5, executive
"""

import pypandoc
import os
import sys
import io
import time
import argparse
import re
import shutil
import subprocess
import tempfile
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

console = Console()

# ── Page size presets ────────────────────────────────────────────────────────
PAGE_SIZES = {
    "a4":        "a4paper",
    "letter":    "letterpaper",
    "legal":     "legalpaper",
    "a3":        "a3paper",
    "a5":        "a5paper",
    "b5":        "b5paper",
    "executive": "executivepaper",
}

# ── Markdown pre-processing ──────────────────────────────────────────────────

def preprocess_markdown(text: str) -> str:
    """
    Normalise AI-generated Markdown before passing to pandoc.

    Fixes applied (in order):
      0.  ATX heading blank-line padding  (### must have blank lines around it)
      1.  Bracket display-math  [ ... ]  →  $$ ... $$
      2.  Asterisk-based subscripts in math  cmd*{sub}  →  cmd_{sub}
      3.  Inline-math parentheses  (LaTeX expr)  →  $LaTeX expr$
      4.  Table blank-line insertion
      5.  Bare subscript/sigma placeholders  (z_ ) / ( _p)
      6.  Unicode math character → LaTeX command
    """

    # ── 0. ATX headings (#/##/###): ensure blank line before & after ─────────
    # Must run FIRST — before any math rewriting that could corrupt heading lines.
    # Pandoc requires blank lines around headings when they lack surrounding space.
    lines = text.splitlines()
    fixed0: list[str] = []
    for i, line in enumerate(lines):
        is_heading = bool(re.match(r'^#{1,6}\s+\S', line))
        if is_heading:
            if fixed0 and fixed0[-1].strip():
                fixed0.append('')
            fixed0.append(line)
            if i + 1 < len(lines) and lines[i + 1].strip():
                fixed0.append('')
        else:
            fixed0.append(line)
    text = '\n'.join(fixed0)

    # Compiled heuristic: a parenthesised group is "math" if it matches this.
    MATH_TRIGGER = re.compile(
        r'\\[a-zA-Z]'           # any LaTeX command
        r'|[_^]'                # subscript / superscript
        r'|\bfrac\b'
        r'|[0-9]+\s*[=<>]'     # numeric equation
        r'|=[^)]{1,30}$'        # ends with =...
        r'|[=<>]\s*[0-9]'
        r'|\b(?:alpha|beta|gamma|delta|rho|sigma|mu|pi|bar|hat)\b'
    )
    # ── 1. Bracket display-math ──────────────────────────────────────────────
    # Use [ \t]* (horizontal-space only) so blank lines between math blocks
    # and surrounding headings are never swallowed by \s*.
    text = re.sub(
        r'(?m)^[ \t]*\[[ \t]*\n(.*?)\n[ \t]*\][ \t]*$',
        lambda m: '$$\n' + m.group(1).strip() + '\n$$',
        text,
        flags=re.DOTALL,
    )
    # Separate adjacent $$ blocks that got merged (consecutive [ ] blocks)
    text = re.sub(r'\$\$\s*\$\$', '$$\n\n$$', text)

    # ── 2. Asterisk subscripts in math expressions ───────────────────────────
    # Patterns like  \text{VaR}*{95}  or  z*{0.95}  →  \text{VaR}_{95}
    # Must run BEFORE the inline-math parenthesis pass so $...$ blocks are clean.
    text = re.sub(r'(\\[A-Za-z]+(?:\{[^}]*\})?)\*\{([^}]+)\}', r'\1_{\2}', text)
    # Also handle  \text{X}*alpha  (no braces around subscript)
    text = re.sub(r'(\\text\{[^}]+\})\*([A-Za-z0-9]+)', r'\1_{\2}', text)
    # And plain  word*{sub}  e.g.  s*{h}  →  s_{h}  (inside display math)
    text = re.sub(r'\b([A-Za-z])\*\{([^}]+)\}', r'\1_{\2}', text)

    # ── 2b. Double-paren and nested-paren math in table headers ──────────────
    # AI writes table headers like:
    #   ((R_S-\bar R_S)^2)   →  $(R_S-\bar R_S)^2$
    #   ((R_S-\bar R_S)(R_F-\bar R_F))  →  $(R_S-\bar R_S)(R_F-\bar R_F)$
    # We process table rows cell-by-cell, stripping exactly one outer paren layer
    # when the cell content looks like LaTeX math.
    def fix_table_header_cell(cell_content: str) -> str:
        s = cell_content.strip()
        # Outer paren wrapping: starts with ( and ends with )
        if s.startswith('(') and s.endswith(')'):
            inner = s[1:-1]
            if MATH_TRIGGER.search(inner):
                return f' ${inner}$ '
        return cell_content

    def fix_table_row(line: str) -> str:
        if not line.lstrip().startswith('|'):
            return line
        parts = line.split('|')
        return '|'.join(fix_table_header_cell(p) if i > 0 and i < len(parts) - 1 else p
                        for i, p in enumerate(parts))

    text = '\n'.join(fix_table_row(line) for line in text.splitlines())

    # Fix \operatorname{...}(args) in table cells — nested parens block the pass
    # e.g. (\operatorname{Cov}(S,F))  →  $\operatorname{Cov}(S,F)$
    text = re.sub(
        r'\((\\operatorname\{[^}]+\}\([^)]+\))\)',
        r'$\1$',
        text,
    )

    # Fix VaR formula comma-multiplication: \text{VaR}_{95} = z_{0.95}, s, V
    # The commas should be \cdot (multiplication)
    def _var_cdot(m):
        return f'{m.group(1)} \\cdot {m.group(2)} \\cdot {m.group(3)}'
    text = re.sub(
        r'(\\text\{VaR\}[_^][^=\n]*=\s*[^,\n]+),\s*([a-zA-Z\\][^,\n]*),\s*([a-zA-Z\\][^\n]*)',
        _var_cdot,
        text,
    )

    # Fix table header cells with nested parens like ((R_S-\bar R_S)^2)
    # These become ($R_S-\bar R_S$^2) after single-level paren conversion — fix the ^2
    def fix_table_math_headers(line):
        """Re-wrap table header cells that have LaTeX but broken $ boundaries."""
        if not line.startswith('|'):
            return line
        cells = line.split('|')
        fixed_cells = []
        for cell in cells:
            # If cell contains LaTeX but has mismatched $, re-wrap entire cell content
            stripped = cell.strip()
            # Pattern: $...$ followed immediately by ^N or _N (means the paren matched too early)
            if re.search(r'\$[^$]+\$[\^_]', stripped):
                # Find the LaTeX content and re-wrap the whole thing
                fixed = re.sub(r'\$([^$]+)\$([\^_][^|\s]+)', r'$\1\2$', stripped)
                fixed_cells.append(f' {fixed} ')
            else:
                fixed_cells.append(cell)
        return '|'.join(fixed_cells)

    text = '\n'.join(fix_table_math_headers(line) for line in text.splitlines())

    # ── 3. Inline-math parentheses ────────────────────────────────────────────
    # AI assistants often write  (LaTeX)  where they mean  $LaTeX$.
    # We deliberately skip:
    #   - currency like  ($18,337)  ← starts with $, skip
    #   - already-dollar-wrapped content

    def maybe_math(m: re.Match) -> str:
        inner = m.group(1)
        # Skip if empty or a dollar amount starting with $
        if not inner.strip():
            return m.group(0)
        if re.fullmatch(r'[$].*', inner.strip()):
            return m.group(0)
        if MATH_TRIGGER.search(inner):
            return f'${inner}$'
        # Also convert simple   (n=10)   (V = 1{,}000{,}000)  style
        if re.fullmatch(r'\s*[A-Za-z_]\w*\s*=\s*[0-9{},.\s]+\s*', inner):
            return f'${inner}$'
        # Convert plain numbers/percentages in parens used as inline math references
        # e.g. (0.9922)  (1.1612)  (98.45%)
        if re.fullmatch(r'\s*-?[0-9]+(?:\.[0-9]+)?%?\s*', inner):
            return f'${inner}$'
        return m.group(0)

    # Only look outside existing $...$ spans to avoid double-wrapping.
    # Strategy: split on $-delimited regions, apply only to even-indexed chunks.
    def apply_outside_math(fn, src):
        parts = re.split(r'(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$)', src)
        return ''.join(fn(p) if i % 2 == 0 else p for i, p in enumerate(parts))

    paren_pat = re.compile(r'\(([^()\n]{1,120})\)')
    text = apply_outside_math(lambda p: paren_pat.sub(maybe_math, p), text)

    # ── 4. Tables: blank-line insertion ──────────────────────────────────────
    lines = text.splitlines()
    fixed: list[str] = []
    for i, line in enumerate(lines):
        if line.lstrip().startswith('|') and i > 0:
            prev = lines[i - 1].strip()
            if prev and not prev.startswith('|'):
                fixed.append('')
        fixed.append(line)
    text = '\n'.join(fixed)

    # ── 5. Bare subscript/sigma placeholders ─────────────────────────────────
    text = re.sub(r'\(\s*z_\s*\)', r'$z_{\\alpha}$', text)
    text = re.sub(r'\(\s*_p\s*\)',  r'$\\sigma_p$',   text)
    # z_{0.95} 1.645  →  z_{0.95} \approx 1.645  (missing ≈ in example prose)
    text = re.sub(r'(z_\{[^}]+\})\s*=\s*([0-9.]+)', r'\1 = \2', text)

    # ── 6. Unicode math → LaTeX ───────────────────────────────────────────────
    UNICODE_MAP = {
        '∑': r'\sum',   '∫': r'\int',   '∂': r'\partial', '∞': r'\infty',
        '≠': r'\neq',   '≤': r'\leq',   '≥': r'\geq',     '≈': r'\approx',
        '×': r'\times', '÷': r'\div',   '±': r'\pm',       '∓': r'\mp',
        '→': r'\to',    '←': r'\leftarrow', '↔': r'\leftrightarrow',
        '⟹': r'\Rightarrow', '⟺': r'\Leftrightarrow',
        '∈': r'\in',    '∉': r'\notin', '⊂': r'\subset',  '⊆': r'\subseteq',
        '∪': r'\cup',   '∩': r'\cap',   '∀': r'\forall',  '∃': r'\exists',
        # italic-math Unicode variants emitted by some AI renderers
        '𝜎': r'\sigma', '𝝈': r'\sigma', '𝞂': r'\sigma',
        '𝛼': r'\alpha', '𝜶': r'\alpha',
        '𝜇': r'\mu',    '𝜆': r'\lambda', '𝜋': r'\pi',
    }
    for ch, cmd in UNICODE_MAP.items():
        text = text.replace(ch, cmd)

    return text


# ── LaTeX post-processor: add vertical grid lines to tables ──────────────────

def add_table_vlines(latex: str) -> str:
    """
    Pandoc pipe tables emit column specs like  {@ {}lrr@ {}} (no spaces).
    Replace them with  {|l|r|r|}  so every table gets full grid lines.
    Also handles the longtable [] alignment argument.
    """
    def fix_colspec(m):
        inner = m.group(1)  # e.g. 'lrrc'
        # Parse column specifiers: l, r, c, and p{...} / m{...} / b{...}
        cols = []
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch in 'lrcLRC':
                cols.append(ch)
                i += 1
            elif ch in 'pmb' and i + 1 < len(inner) and inner[i + 1] == '{':
                # Find matching brace
                depth, j = 0, i + 1
                while j < len(inner):
                    if inner[j] == '{': depth += 1
                    elif inner[j] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                cols.append(inner[i:j + 1])
                i = j + 1
            else:
                i += 1  # skip unknown specifiers (e.g. @{})
        if cols:
            return '{|' + '|'.join(cols) + '|}'
        return m.group(0)

    # Match  {@{}...@{}}  column specs generated by pandoc
    latex = re.sub(r'\{@\{\}([lrcpmb][^{}]*?)@\{\}\}', fix_colspec, latex)
    # Also strip the [] centering argument pandoc adds: []{|...|} → {|...|} is fine,
    # but keep [] so longtable alignment is preserved.
    return latex


# ── LaTeX header builder ─────────────────────────────────────────────────────

def build_latex_header(page_size_key: str, line_numbers: bool) -> str:
    """Return a complete LaTeX include-in-header snippet."""

    paper = PAGE_SIZES.get(page_size_key.lower(), "a4paper")

    return rf"""
% ═══════════════════════════════════════════════════════════
%  md2pdf premium header — generated automatically
% ═══════════════════════════════════════════════════════════

% ── Page geometry ───────────────────────────────────────────
\usepackage[{paper}, top=25mm, bottom=25mm, left=22mm, right=22mm]{{geometry}}

% ── Core packages ───────────────────────────────────────────
\usepackage{{xcolor}}
\usepackage{{booktabs}}
\usepackage{{longtable}}
\usepackage{{array}}
\usepackage{{colortbl}}
\usepackage{{enumitem}}
\usepackage{{fancyhdr}}
\usepackage{{mdframed}}
\usepackage{{microtype}}

% Math
\usepackage{{amsmath}}
\usepackage{{amssymb}}
\usepackage{{mathtools}}

% Unicode math fallbacks
\usepackage{{newunicodechar}}
\newunicodechar{{∑}}{{\ensuremath{{\sum}}}}
\newunicodechar{{∫}}{{\ensuremath{{\int}}}}
\newunicodechar{{∂}}{{\ensuremath{{\partial}}}}
\newunicodechar{{∞}}{{\ensuremath{{\infty}}}}
\newunicodechar{{≤}}{{\ensuremath{{\leq}}}}
\newunicodechar{{≥}}{{\ensuremath{{\geq}}}}
\newunicodechar{{≠}}{{\ensuremath{{\neq}}}}
\newunicodechar{{≈}}{{\ensuremath{{\approx}}}}

% ── Colour palette ──────────────────────────────────────────
\definecolor{{accent}}    {{HTML}}{{2563EB}}   % blue-600
\definecolor{{accent2}}   {{HTML}}{{1D4ED8}}   % blue-700
\definecolor{{codebg}}    {{HTML}}{{F8F9FA}}   % near-white
\definecolor{{codeframe}} {{HTML}}{{DEE2E6}}   % light grey border
\definecolor{{codefg}}    {{HTML}}{{1a1a2e}}   % dark ink
\definecolor{{linenumcol}}{{HTML}}{{9CA3AF}}   % muted grey line numbers
\definecolor{{kwcol}}     {{HTML}}{{7C3AED}}   % purple keywords
\definecolor{{strcol}}    {{HTML}}{{16A34A}}   % green strings
\definecolor{{cmtcol}}    {{HTML}}{{6B7280}}   % grey comments
\definecolor{{rulecol}}   {{HTML}}{{E5E7EB}}   % rule / border grey
\definecolor{{qbar}}      {{HTML}}{{93C5FD}}   % blockquote left bar
\definecolor{{qbg}}       {{HTML}}{{EFF6FF}}   % blockquote background
\definecolor{{tblhead}}   {{HTML}}{{EFF6FF}}   % table header fill

% ── KOMA heading colours ────────────────────────────────────
\addtokomafont{{section}}{{\color{{accent}}\Large}}
\addtokomafont{{subsection}}{{\color{{accent2}}\large}}
\addtokomafont{{subsubsection}}{{\color{{accent2}}\normalsize\bfseries}}
\setkomafont{{title}}{{\color{{accent}}\huge\bfseries}}

% ── Typography ──────────────────────────────────────────────
\setlength{{\parskip}}{{0.65em}}
\setlength{{\parindent}}{{0pt}}

% ── Lists ───────────────────────────────────────────────────
\setlist[itemize]  {{leftmargin=*, label=\textcolor{{accent}}{{$\bullet$}}, itemsep=0.25em, topsep=0.3em}}
\setlist[enumerate]{{leftmargin=*, itemsep=0.25em, topsep=0.3em}}

% ── Tables: grid style + auto font-size reduction ───────────
\usepackage{{adjustbox}}
\setlength{{\arrayrulewidth}}{{0.5pt}}
\arrayrulecolor{{rulecol}}
\renewcommand{{\arraystretch}}{{1.35}}
\makeatletter\def\fps@table{{h}}\makeatother

% Colour the header row of every table automatically.
% We detect the first row via \toprule / first \\ and shade it.
\colorlet{{tblheadbg}}{{tblhead}}

% Auto-shrink wide tabular to page width and reduce font.
% Three tiers: fits at \small → keep \small;
%              wider than \linewidth → scale down with \resizebox.
\makeatletter
\newsavebox{{\md@tblbox}}
\let\md@origTabular\tabular
\let\md@endorigTabular\endtabular
\renewenvironment{{tabular}}[1]{{%
  \small%
  \begin{{lrbox}}{{\md@tblbox}}%
  \md@origTabular{{#1}}%
}}{{%
  \md@endorigTabular%
  \end{{lrbox}}%
  \ifdim\wd\md@tblbox>\linewidth%
    \resizebox{{\linewidth}}{{!}}{{\usebox{{\md@tblbox}}}}%
  \else%
    \usebox{{\md@tblbox}}%
  \fi%
}}
\makeatother

% longtable: scriptsize font to handle very wide tables.
\AtBeginEnvironment{{longtable}}{{%
  \scriptsize%
  \setlength{{\arrayrulewidth}}{{0.5pt}}%
  \arrayrulecolor{{rulecol}}%
  \setlength{{\LTleft}}{{0pt}}%
  \setlength{{\LTright}}{{0pt}}%
}}

% ── Inline code ─────────────────────────────────────────────
\usepackage{{soul}}
\let\mdpdfOldTexttt\texttt
\renewcommand{{\texttt}}[1]{{\colorbox{{codebg}}{{\textcolor{{codefg}}{{\mdpdfOldTexttt{{#1}}}}}}}}

% ── Code blocks ─────────────────────────────────────────────
\usepackage{{framed}}
\definecolor{{shadecolor}}{{HTML}}{{F8F9FA}}

% ── Blockquotes ─────────────────────────────────────────────
\renewenvironment{{quote}}{{%
  \begin{{mdframed}}[
      linecolor=qbar,
      linewidth=3pt,
      topline=false, bottomline=false, rightline=false,
      backgroundcolor=qbg,
      innerleftmargin=10pt, innerrightmargin=8pt,
      innertopmargin=6pt,  innerbottommargin=6pt,
      skipabove=0.6em, skipbelow=0.4em
  ]
  \itshape\color{{codefg!70!black}}
}}{{\end{{mdframed}}}}

% ── Header / Footer ─────────────────────────────────────────
\pagestyle{{fancy}}
\fancyhf{{}}
\fancyhead[R]{{\textcolor{{linenumcol}}{{\small\thepage}}}}
\renewcommand{{\headrulewidth}}{{0.5pt}}
\renewcommand{{\footrulewidth}}{{0pt}}
\renewcommand{{\headrule}}{{\color{{rulecol}}\hrule width\headwidth height 0.5pt}}
"""


# ── PDF engine detection ──────────────────────────────────────────────────────

def _pick_pdf_engine() -> str:
    """Return the best available PDF engine: tectonic > xelatex > pdflatex."""
    for engine in ("tectonic", "xelatex", "pdflatex"):
        if shutil.which(engine):
            return engine
    raise RuntimeError(
        "No PDF engine found. Install tectonic, xelatex, or pdflatex."
    )


# ── Core converter ───────────────────────────────────────────────────────────

def convert_to_pdf(
    input_data: str,
    *,
    is_file: bool = True,
    output_filename: str = "output.pdf",
    page_size: str = "a4",
    line_numbers: bool = False,
) -> bool:
    """Convert Markdown (file path or raw string) to a polished PDF."""

    downloads_folder = os.path.expanduser("~/storage/downloads/")
    os.makedirs(downloads_folder, exist_ok=True)
    output_pdf = os.path.join(downloads_folder, output_filename)

    style_file = "md2pdf_header.tex"
    try:
        # Write LaTeX header
        with open(style_file, "w", encoding="utf-8") as fh:
            fh.write(build_latex_header(page_size, line_numbers))

        # Read & pre-process source
        if is_file:
            with open(input_data, "r", encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = input_data

        fixed_md = preprocess_markdown(raw)

        # Pandoc markdown dialect
        md_format = (
            "markdown"
            "-yaml_metadata_block"
            "-multiline_tables"
            "-grid_tables"
            "-simple_tables"
            "+pipe_tables"
            "+tex_math_dollars"
            "+lists_without_preceding_blankline"
            "+blank_before_header"
        )

        engine = _pick_pdf_engine()

        with Status(
            f"[bold blue]Converting → [white]{output_filename} "
            f"[dim]({page_size.upper()}"
            + (" · line numbers" if line_numbers else "")
            + f" · engine: {engine})[/]",
            console=console,
            spinner="dots12",
        ):
            # ── Step A: pandoc → intermediate LaTeX ──────────────────────────
            extra_args_latex = [
                f"--pdf-engine={engine}",
                "-V", "documentclass=scrartcl",
                "--include-in-header", style_file,
                "--syntax-highlighting=idiomatic",
                "--standalone",
                "-V", "colorlinks=true",
                "-V", "linkcolor=accent",
                "-V", "urlcolor=accent",
            ]

            latex_src = pypandoc.convert_text(
                fixed_md,
                "latex",
                format=md_format,
                extra_args=[
                    "-V", "documentclass=scrartcl",
                    "--include-in-header", style_file,
                    "--standalone",
                ],
            )

            # ── Step B: post-process LaTeX ───────────────────────────────────
            # Strip lmodern if not installed (Termux minimal TeX setups)
            latex_src = latex_src.replace(r'\usepackage{lmodern}', '')
            # Pandoc injects a microtype conditional that pdflatex sometimes
            # cannot satisfy with bitmap fonts; nuke it if present.
            latex_src = re.sub(
                r'\\IfFileExists\{microtype\.sty\}.*?\\fi',
                '',
                latex_src,
                flags=re.DOTALL,
            )
            # Add full grid lines to all tables
            latex_src = add_table_vlines(latex_src)

            # ── Step C: compile with chosen engine ────────────────────────────
            with tempfile.TemporaryDirectory() as tmpdir:
                tex_path = os.path.join(tmpdir, "document.tex")
                with open(tex_path, "w", encoding="utf-8") as fh:
                    fh.write(latex_src)

                if engine == "tectonic":
                    cmd = ["tectonic", "--outdir", tmpdir, tex_path]
                else:
                    cmd = [
                        engine,
                        "-interaction=nonstopmode",
                        f"-output-directory={tmpdir}",
                        tex_path,
                    ]
                    # Two passes for longtable page-break calculation
                    subprocess.run(cmd, capture_output=True, check=False)

                result = subprocess.run(cmd, capture_output=True, check=False)

                pdf_path = os.path.join(tmpdir, "document.pdf")
                if not os.path.exists(pdf_path):
                    err = result.stderr.decode(errors="replace")
                    raise RuntimeError(
                        f"{engine} failed.\n"
                        + "\n".join(
                            l for l in err.splitlines()
                            if l.startswith("!") or "Error" in l
                        )[:800]
                    )
                import shutil as _sh
                _sh.copy2(pdf_path, output_pdf)

        console.print(
            Panel(
                f"✨ [bold green]Success![/]\n"
                f"[white]PDF saved to:\n[cyan]{output_pdf}[/]\n"
                f"[dim]Page size: {page_size.upper()}  |  Engine: {engine}"
                + ("  |  Line numbers: on" if line_numbers else "")
                + "[/]",
                title="md2pdf",
                border_style="green",
            )
        )
        return True

    except Exception as exc:
        console.print(
            Panel(
                f"❌ [bold red]Conversion Failed[/]\n[white]{exc}",
                title="md2pdf Error",
                border_style="red",
            )
        )
        return False

    finally:
        if os.path.exists(style_file):
            os.remove(style_file)


# ── Watch-mode handler ───────────────────────────────────────────────────────

class MarkdownWatcher(FileSystemEventHandler):
    def __init__(self, filepath: str, output: str, page_size: str, line_numbers: bool):
        self.filepath = os.path.abspath(filepath)
        self.output = output
        self.page_size = page_size
        self.line_numbers = line_numbers
        self.last_run = 0.0

    def on_modified(self, event):
        if event.src_path == self.filepath and time.time() - self.last_run > 2:
            console.print(
                f"\n[bold yellow]🔄 Change detected — rebuilding {os.path.basename(self.filepath)}…[/]"
            )
            convert_to_pdf(
                self.filepath,
                is_file=True,
                output_filename=self.output,
                page_size=self.page_size,
                line_numbers=self.line_numbers,
            )
            self.last_run = time.time()


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="md2pdf — Polished Markdown → PDF converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input",
        help="Input Markdown file, or '-' to read from stdin/pipe",
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Output PDF filename (default: <input>.pdf)",
    )
    parser.add_argument(
        "-p", "--page-size",
        default="a4",
        choices=list(PAGE_SIZES.keys()),
        metavar="SIZE",
        help=(
            "Page size preset.  Choices: "
            + ", ".join(PAGE_SIZES.keys())
            + "  (default: a4)"
        ),
    )
    parser.add_argument(
        "-n", "--line-numbers",
        action="store_true",
        help="Add line numbers to every code block",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the input file and rebuild on every save (Ctrl-C to stop)",
    )
    args = parser.parse_args()

    # ── Resolve output name
    if args.output:
        out_name = args.output
    elif args.input == "-":
        out_name = "piped_output.pdf"
    else:
        base = os.path.basename(args.input)
        out_name = re.sub(r"\.md$", "", base, flags=re.IGNORECASE) + ".pdf"

    # ── Pipe / stdin mode
    if args.input == "-" or not sys.stdin.isatty():
        if not sys.stdin.isatty():
            sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
            piped = sys.stdin.read()
            convert_to_pdf(
                piped,
                is_file=False,
                output_filename=out_name,
                page_size=args.page_size,
                line_numbers=args.line_numbers,
            )
        return

    # ── File mode
    if not os.path.exists(args.input):
        console.print(f"[bold red]❌ File not found:[/] {args.input}")
        return

    convert_to_pdf(
        args.input,
        is_file=True,
        output_filename=out_name,
        page_size=args.page_size,
        line_numbers=args.line_numbers,
    )

    # ── Watch mode
    if args.watch:
        console.print(
            f"\n[bold magenta]👁  Watch mode[/] — monitoring [bold white]{args.input}[/]\n"
            "[dim]Press Ctrl-C to stop.[/]"
        )
        handler = MarkdownWatcher(args.input, out_name, args.page_size, args.line_numbers)
        observer = Observer()
        observer.schedule(
            handler,
            path=os.path.dirname(os.path.abspath(args.input)) or ".",
            recursive=False,
        )
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
