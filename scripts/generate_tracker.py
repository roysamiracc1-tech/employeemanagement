#!/usr/bin/env python3
"""Generate the programme tracker spreadsheet FROM `BACKLOG.md`.

    python3 scripts/generate_tracker.py

Writes `docs/project-management/PROGRAMME_TRACKER.xlsx`.

⚠ **THE SPREADSHEET IS AN OUTPUT, NOT A SOURCE.** It is generated, never
hand-edited, and regenerating overwrites it.

That is the whole design, and it is not pedantry. `BACKLOG.md` is the source of
truth by project rule (`CLAUDE.md` — documentation lives in git). A hand-kept
spreadsheet beside it becomes a second source that disagrees within a fortnight,
and then nobody knows which one is right — which is a worse problem than the one
it was meant to solve. So: edit the markdown, re-run this, and the two cannot
drift.

Why a spreadsheet at all, then? Because 1,500 lines of markdown is the wrong tool
for *"what is the status of everything?"* — it is excellent for the reasoning
behind each story and hopeless for the overview. This gives the overview and
links back to the reasoning.

Sheets produced:
  Overview   — one row per epic: story counts, done/total, status
  Stories    — one row per story: epic, wave, status, priority, title, summary
  Delivered  — what has actually shipped, with its evidence
  Decisions  — the owner decisions and their effect
  Defects    — the defect register with current state
  Questions  — open questions and who owes the answer
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKLOG = os.path.join(ROOT, 'docs', 'project-management', 'BACKLOG.md')
OUT = os.path.join(ROOT, 'docs', 'project-management', 'PROGRAMME_TRACKER.xlsx')

# ── Styling ───────────────────────────────────────────────────────────────────
NAVY = '0F2044'
HEAD = Font(bold=True, color='FFFFFF', size=10)
HEAD_FILL = PatternFill('solid', fgColor=NAVY)
TITLE = Font(bold=True, size=14, color=NAVY)
NOTE = Font(italic=True, size=9, color='64748B')
WRAP = Alignment(wrap_text=True, vertical='top')
TOP = Alignment(vertical='top')
THIN = Border(bottom=Side('thin', color='E2E8F0'))

STATUS_FILL = {
    'Done':        PatternFill('solid', fgColor='D1FAE5'),
    'In progress': PatternFill('solid', fgColor='FEF3C7'),
    'Planned':     PatternFill('solid', fgColor='F1F5F9'),
    'Blocked':     PatternFill('solid', fgColor='FEE2E2'),
    'Accepted':    PatternFill('solid', fgColor='E0E7FF'),
}


def status_of(marker):
    """Map the markdown's status glyph onto a word."""
    if '✅' in marker:
        return 'Done'
    if '🟡' in marker:
        return 'In progress'
    if '⏸' in marker or '⛔' in marker:
        return 'Blocked'
    if '⬜' in marker:
        return 'Planned'
    return 'Unknown'


def clean(text, limit=None):
    """Markdown → readable plain text.

    Deliberately lossy: the spreadsheet is the overview, and the full reasoning
    stays in `BACKLOG.md` where it belongs. Every row keeps its story id so the
    detail is one search away.
    """
    t = text or ''
    t = re.sub(r'`([^`]*)`', r'\1', t)
    t = re.sub(r'\*\*([^*]*)\*\*', r'\1', t)
    t = re.sub(r'\*([^*]*)\*', r'\1', t)
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = t.replace('⚠️', '⚠').replace('|', '/')
    t = ' '.join(t.split())
    if limit and len(t) > limit:
        t = t[:limit - 1].rsplit(' ', 1)[0] + '…'
    return t


def first_sentence(text, limit=220):
    """The user-story line, which is the one sentence worth putting in a cell."""
    t = clean(text)
    m = re.match(r'(As (?:a|an|the) .*?, I want .*?, so .*?\.)', t)
    if m:
        return clean(m.group(1), limit)
    return clean(t, limit)


def read():
    with open(BACKLOG, encoding='utf-8') as f:
        return f.read()


def split_row(line):
    """Cells of a markdown table row, without the leading/trailing pipes."""
    return [c.strip() for c in line.strip().strip('|').split('|')]


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_epics(src):
    """The epic summary table near the top: | EP42 | Name | stories | status |."""
    out = []
    for line in src.splitlines():
        if not re.match(r'^\|\s*EP\d+\s*\|', line):
            continue
        cells = split_row(line)
        if len(cells) < 4:
            continue
        epic, name, stories, status = cells[0], cells[1], cells[2], cells[3]
        ids = re.findall(r'KAN-\d+', stories)
        out.append({
            'epic': clean(epic),
            'name': clean(name),
            'story_count': len(set(ids)),
            'stories': ' '.join(sorted(set(ids), key=lambda s: int(s.split('-')[1]))),
            'status': status_of(status),
            'note': clean(status, 400),
        })
    return out


def parse_epic_ids(src):
    """The Epic Summary table, which is the only place each epic's own KAN id lives."""
    out = {}
    for line in src.splitlines():
        m = re.match(r'^\|\s*(KAN-\d+)\s*\|\s*(EP\d+)\s*—', line)
        if m:
            out[m.group(2)] = m.group(1)
    return out


def story_to_epic(src):
    """{KAN-id: 'EPn — Name'} from every table that lists an epic's stories.

    Belt and braces for the Epic column: the `## EPnn —` headings only cover the
    epics written up in full, and a story with no epic in an overview sheet is
    exactly what makes such a sheet useless.
    """
    out = {}
    for line in src.splitlines():
        m = (re.match(r'^\|\s*KAN-\d+\s*\|\s*(EP\d+)\s*—\s*([^|]*)\|([^|]*)\|', line)
             or re.match(r'^\|\s*(EP\d+)\s*\|\s*([^|]*)\|([^|]*)\|', line))
        if not m:
            continue
        label = f'{m.group(1)} — {clean(m.group(2), 60)}'
        for sid in re.findall(r'KAN-\d+', m.group(3)):
            out.setdefault(sid, label)
    return out


def parse_stories(src):
    """Story rows: | <glyph> KAN-### | user story | acceptance criteria | priority |

    Also captures the wave heading each story sits under, and the epic from the
    nearest `## EPnn` heading above it — so a story's context comes from the
    document structure rather than from a second list that could disagree.
    """
    out = []
    epic = wave = ''
    for line in src.splitlines():
        h = re.match(r'^##\s+EPIC\s+(\d+)\s*—\s*(.*)$', line) or \
            re.match(r'^##\s+EP(\d+)\s*—\s*(.*)$', line)
        if h:
            # Both heading forms occur: `## EP42 — …` and `## EPIC 11 — …`.
            # Matching only one left sixteen stories with no epic at all.
            name = re.split(r'\s+—\s+', clean(h.group(2)))[0]
            epic = f'EP{h.group(1)} — {clean(name, 60)}'
            wave = ''
            continue
        w = re.match(r'^###\s+(.*)$', line)
        if w:
            wave = clean(w.group(1), 70)
            continue
        m = re.match(r'^\|\s*(✅|⬜|🟡|⏸|⛔)?\s*(KAN-\d+)\s*\|(.*)$', line)
        if not m:
            continue
        cells = split_row(line)
        # ⚠ The "Epic Summary" table gives each EPIC its own KAN id
        # (`| KAN-2 | EP1 — Authentication … |`), so those rows match this
        # pattern while not being stories. Excluded by their second cell, which
        # names an epic — otherwise ten epics appear in the Stories sheet with
        # every column shifted one to the left.
        if len(cells) > 1 and re.match(r'^EP\d+\s*—', clean(cells[1])):
            continue
        story = cells[0]
        out.append({
            'id': m.group(2),
            'num': int(m.group(2).split('-')[1]),
            'status': status_of(story),
            'epic': epic,
            'wave': wave,
            'title': first_sentence(cells[1] if len(cells) > 1 else ''),
            'priority': clean(cells[-1], 40) if len(cells) >= 4 else '',
            'detail': clean(cells[2] if len(cells) > 2 else '', 700),
        })
    # A story can appear in more than one place (an epic table and a wave table).
    # Keep the richest row per id, preferring one that carries a wave.
    best = {}
    for s in out:
        cur = best.get(s['id'])
        if cur is None or (not cur['wave'] and s['wave']) or len(s['detail']) > len(cur['detail']):
            best[s['id']] = s
    return sorted(best.values(), key=lambda s: s['num'])


def parse_delivered(src):
    """The `| | **✅ KAN-nnn DONE (date).** …` continuation rows.

    These are the evidence rows written when a story lands, so they carry the
    date, the test counts and the caveats — the things somebody asking "is it
    really done?" actually wants.
    """
    out = []
    last_story = None
    for line in src.splitlines():
        # Remember the story row above, so an evidence row that omits its own id
        # is attributed rather than silently dropped from the sheet.
        sm = re.match(r'^\|\s*(?:✅|⬜|🟡|⏸|⛔)?\s*(KAN-\d+)\s*\|', line)
        if sm:
            last_story = sm.group(1)
        m = re.match(r'^\|\s*\|\s*\*\*✅\s*(?:(KAN-\d+)\s+)?DONE\s*\(([^)]*)\)[^*]*\*\*(.*)$', line)
        if not m:
            continue
        story_id = m.group(1) or last_story
        if not story_id:
            continue
        body = clean(m.group(3))
        ev = re.search(r'([\d,]+)\s*pytest.*?browser\s*(\d+/\d+).*?vacation\s*(\d+/\d+)', body)
        out.append({
            'id': story_id,
            'num': int(story_id.split('-')[1]),
            'date': clean(m.group(2)),
            'evidence': (f'pytest {ev.group(1)} · browser {ev.group(2)} · vacation {ev.group(3)}'
                         if ev else ''),
            'caveats': 'YES — see notes' if ('⚠' in m.group(3)) else '',
            'summary': body,
        })
    return sorted(out, key=lambda s: s['num'])


def parse_decisions(src):
    """`> **Decision D-00n — date — …` blocks, plus the resolved option papers."""
    out = []
    seen = set()
    for m in re.finditer(r'>\s*\*\*(?:✅\s*)?(?:Decision\s+)?(D-\d{3})(?!-\d)\s*[—-]\s*([^*]*?)\*\*(.*?)(?=\n\n|\n>\s*\*\*D-|\Z)',
                         src, re.S):
        did = m.group(1)
        if did in seen:
            continue
        seen.add(did)
        body = clean(m.group(3), 900)
        # `clean()` collapses newlines, which drags the next line's `>` marker
        # into the quote. Strip them before matching.
        body = re.sub(r'\s*>\s*', ' ', body).strip()
        body = ' '.join(body.split())
        quote = re.search(r'His words:?\s*[“"\']?(.*?)[”"\']?\s*(?:—|\.|$)', body)
        out.append({
            'id': did,
            'headline': clean(m.group(2), 160),
            'owner_words': clean(quote.group(1), 200) if quote else '',
            'detail': body,
        })
    # Decisions referenced but without a formal block still deserve a row, so the
    # sheet does not silently omit one.
    # Same exclusion for the fallback sweep — `D-185-1` is DEF-185-1's sibling,
    # not a decision, and listing it would invent a decision that never happened.
    for did in sorted(set(re.findall(r'\bD-\d{3}\b(?!-\d)', src))):
        if did not in seen:
            # Prefer the mention that DEFINES it — a line introducing the
            # decision — over the first incidental cross-reference.
            best = ''
            for m2 in re.finditer(rf'[^\n]*\b{did}\b[^\n]*', src):
                line = clean(m2.group(0), 300)
                if re.search(r'decision|ruling|re-sequenc|deferred', line, re.I):
                    best = line
                    break
                if len(line) > len(best):
                    best = line
            out.append({'id': did, 'headline': clean(best, 200),
                        'owner_words': '',
                        'detail': 'No verbatim block — see BACKLOG.md for context.'})
    return sorted(out, key=lambda d: d['id'])


def parse_defects(src):
    """`| **DEF-nnn** | description | severity | evidence | owner |` rows."""
    out = []
    for line in src.splitlines():
        m = re.match(r'^\|\s*\*\*(DEF-[\w-]+)\*\*\s*(✅)?\s*\|(.*)$', line)
        if not m:
            continue
        cells = split_row(line)
        body = cells[1] if len(cells) > 1 else ''
        fixed = bool(m.group(2)) or 'FIXED' in body.upper()
        out.append({
            'id': m.group(1),
            'status': 'Fixed' if fixed else ('Accepted' if 'ACCEPTED' in body.upper() else 'Open'),
            'severity': clean(cells[2], 30) if len(cells) > 2 else '',
            'description': clean(body, 600),
            'owner_route': clean(cells[-1], 400) if len(cells) >= 5 else '',
        })
    return out


def parse_questions(src):
    """Open questions — the `OQ-n` items and who owes the answer."""
    out = []
    for oq in sorted(set(re.findall(r'OQ-\d+', src)), key=lambda s: int(s.split('-')[1])):
        # The most informative mention: prefer one that says ANSWERED/CLOSED.
        best = ''
        for m in re.finditer(rf'[^\n]*{oq}[^\n]*', src):
            line = clean(m.group(0), 400)
            if re.search(r'answered|closed|✅', line, re.I):
                best = line
                break
            if len(line) > len(best):
                best = line
        answered = bool(re.search(r'answered|closed|✅', best, re.I))
        out.append({'id': oq, 'status': 'Answered' if answered else 'Open', 'context': best})
    return out


# ── Sheet writing ─────────────────────────────────────────────────────────────

def sheet(wb, name, title, subtitle, columns, rows, status_col=None):
    ws = wb.create_sheet(name)
    ws['A1'] = title
    ws['A1'].font = TITLE
    ws['A2'] = subtitle
    ws['A2'].font = NOTE
    ws.freeze_panes = 'A5'

    for i, (head, width, _key) in enumerate(columns, start=1):
        c = ws.cell(row=4, column=i, value=head)
        c.font, c.fill, c.alignment = HEAD, HEAD_FILL, WRAP
        ws.column_dimensions[get_column_letter(i)].width = width

    for r, row in enumerate(rows, start=5):
        for i, (_head, _w, key) in enumerate(columns, start=1):
            c = ws.cell(row=r, column=i, value=row.get(key, ''))
            c.alignment = WRAP if _w > 30 else TOP
            c.border = THIN
            c.font = Font(size=10)
        if status_col:
            sc = [i for i, (_h, _w, k) in enumerate(columns, start=1) if k == status_col]
            if sc:
                val = row.get(status_col, '')
                fill = STATUS_FILL.get(val)
                if fill:
                    ws.cell(row=r, column=sc[0]).fill = fill
    ws.auto_filter.ref = (f'A4:{get_column_letter(len(columns))}'
                          f'{max(4, 4 + len(rows))}')
    return ws


def main():
    src = read()
    epics = parse_epics(src)
    epic_ids = parse_epic_ids(src)
    for e in epics:
        e['epic_kan'] = epic_ids.get(e['epic'], '')
    stories = parse_stories(src)
    fallback_epic = story_to_epic(src)
    for st in stories:
        if not st['epic']:
            st['epic'] = fallback_epic.get(st['id'], '')
    delivered = parse_delivered(src)
    decisions = parse_decisions(src)
    defects = parse_defects(src)
    questions = parse_questions(src)

    done = sum(1 for s in stories if s['status'] == 'Done')
    prog = sum(1 for s in stories if s['status'] == 'In progress')

    wb = Workbook()
    wb.remove(wb.active)

    # ── Read me first ─────────────────────────────────────────────────────────
    ws = wb.create_sheet('Read me')
    ws['A1'] = 'Programme tracker'
    ws['A1'].font = TITLE
    ws.column_dimensions['A'].width = 118
    lines = [
        '',
        '⚠  GENERATED FILE — DO NOT EDIT. Regenerating overwrites everything here.',
        '',
        '    python3 scripts/generate_tracker.py',
        '',
        'Why it is generated rather than maintained:',
        '',
        '    BACKLOG.md is the source of truth (project rule: documentation lives in git). A',
        '    hand-kept spreadsheet beside it becomes a second source that disagrees within a',
        '    fortnight — and then nobody knows which is right, which is worse than the problem',
        '    it was meant to solve. Edit the markdown, re-run the script, and they cannot drift.',
        '',
        '    What this fixes is a real complaint: 1,500 lines of markdown is the right tool for',
        '    the REASONING behind a story and the wrong one for "what is the status of',
        '    everything?". This gives the overview. The reasoning stays where it is — every row',
        '    carries its story id, so the detail is one search away in BACKLOG.md.',
        '',
        'Counted right now:',
        '',
        f'    Epics           {len(epics)}',
        f'    Stories         {len(stories)}   ({done} done, {prog} in progress, '
        f'{len(stories) - done - prog} planned)',
        f'    Delivered rows  {len(delivered)}  (a story is only here if it has evidence)',
        f'    Decisions       {len(decisions)}',
        f'    Defects         {len(defects)}',
        f'    Open questions  {sum(1 for q in questions if q["status"] == "Open")} of {len(questions)}',
        '',
        'Sheets:',
        '',
        '    Overview    one row per epic — story counts and status',
        '    Stories     one row per story — epic, wave, status, priority, the user story',
        '    Delivered   what has actually shipped, with its test evidence and caveats',
        '    Decisions   owner decisions, in his own words where they were recorded verbatim',
        '    Defects     the register, with what is fixed, accepted and still open',
        '    Questions   open questions and whether they have been answered',
        '',
        'A caution about the Status column: it reflects what BACKLOG.md SAYS. That is a',
        'deliberate limitation — this script reports the record, it does not audit it. If a',
        'status is wrong here, the backlog is wrong, and that is the thing to fix.',
    ]
    for i, line in enumerate(lines, start=2):
        c = ws.cell(row=i, column=1, value=line)
        c.font = Font(size=10, bold=line.startswith('⚠'),
                      name='Menlo' if line.startswith('    ') else 'Calibri')

    sheet(wb, 'Overview', 'Epics', 'One row per epic. Story counts are distinct KAN ids.',
          [('Epic', 10, 'epic'), ('Epic KAN id', 13, 'epic_kan'),
           ('Name', 46, 'name'), ('Status', 14, 'status'),
           ('Stories', 10, 'story_count'), ('Story ids', 52, 'stories'),
           ('Notes from the backlog', 80, 'note')],
          epics, status_col='status')

    sheet(wb, 'Stories', 'Stories',
          'One row per story. "Wave" and "Epic" come from the document structure, not a second list.',
          [('ID', 11, 'id'), ('Status', 14, 'status'), ('Epic', 34, 'epic'),
           ('Wave / section', 34, 'wave'), ('Priority', 26, 'priority'),
           ('User story', 78, 'title'), ('Acceptance criteria (abridged)', 96, 'detail')],
          stories, status_col='status')

    sheet(wb, 'Delivered', 'Delivered',
          'Only stories with a recorded evidence row. If it is not here, it has not been evidenced.',
          [('ID', 11, 'id'), ('Date', 16, 'date'), ('Test evidence', 40, 'evidence'),
           ('Caveats?', 16, 'caveats'), ('What landed', 118, 'summary')],
          delivered)

    sheet(wb, 'Decisions', 'Decisions',
          'Owner decisions. "In his own words" is filled where the decision was recorded verbatim.',
          [('ID', 10, 'id'), ('Headline', 58, 'headline'),
           ('In his own words', 46, 'owner_words'), ('Detail', 110, 'detail')],
          decisions)

    sheet(wb, 'Defects', 'Defects',
          'The register. "Accepted" means a known behaviour the owner chose to keep, not an open bug.',
          [('ID', 14, 'id'), ('State', 13, 'status'), ('Severity', 16, 'severity'),
           ('Description', 96, 'description'), ('Owner / route', 70, 'owner_route')],
          defects, status_col='status')

    sheet(wb, 'Questions', 'Open questions',
          'Whether each has been answered. An answered question keeps its row so the trail survives.',
          [('ID', 10, 'id'), ('State', 13, 'status'), ('Context from the backlog', 130, 'context')],
          questions)

    wb.save(OUT)
    print(f'Wrote {os.path.relpath(OUT, ROOT)}')
    print(f'  {len(epics)} epics · {len(stories)} stories ({done} done, {prog} in progress) · '
          f'{len(delivered)} delivered · {len(decisions)} decisions · {len(defects)} defects · '
          f'{len(questions)} questions')
    return 0


if __name__ == '__main__':
    sys.exit(main())
