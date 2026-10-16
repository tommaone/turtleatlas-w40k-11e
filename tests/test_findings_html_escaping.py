"""Tests for HTML/JS escaping in findings generation.

`findings/*/findings.html` embeds unit names, expert prose and mission keys into
a `<script>` element and then into `innerHTML` at render time. Both are injection
sinks: a raw '<' can close the `<script>` element early, and an unescaped name
can smuggle markup into the page. `_js_safe` guards the JSON literal; `esc`/
`escObj` guard the DOM writes. These tests pin both, and prove the value
round-trips unchanged through the escape so the page still shows the real text.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import scripts.gen_findings_html as gen  # noqa: E402


BREAKOUT = '</script><img src=x onerror=alert(1)>'


def _blob(html_out, name):
    """Pull the `const NAME={json}` literal out of a generated page.

    Anchored on the next `const` declaration so a nested '}' in the data can't
    truncate the match.
    """
    match = re.search(rf'const {name}=(.*?);\nconst ', html_out, re.S)
    assert match, f'const {name}= blob not found'
    return match.group(1)


def test_js_safe_escapes_angle_and_line_separators():
    assert gen._js_safe('a</script>b') == 'a\\u003c/script>b'
    assert gen._js_safe('x\u2028y\u2029z') == 'x\\u2028y\\u2029z'
    assert '</script>' not in gen._js_safe(BREAKOUT)


def test_gen_html_escapes_script_breakout_in_data():
    data = {'meta': {'competitive': {'Take and Hold': [
        {'name': BREAKOUT, 'pts': 100}]}}, 'meta_info': []}
    out = gen.gen_html('Faction', data, 1, fid=None)

    # Only the page's own closing tag survives -- the injected one is escaped.
    assert out.count('</script>') == 1, 'injected </script> must be neutralised'
    assert '<img' not in out, 'raw markup must not reach the page source'

    # The escape is transparent: the browser parses \u003c back to '<'.
    parsed = json.loads(_blob(out, 'DATA'))
    assert parsed['meta']['competitive']['Take and Hold'][0]['name'] == BREAKOUT


def test_gen_html_escapes_expert_prose(monkeypatch):
    """The EXPERT blob is the same sink; a note can contain '<' or a breakout."""
    prose = 'Army rule: <7 YPs, then mode switch. </script>'
    monkeypatch.setattr(gen, 'parse_expert_assessment',
                        lambda fid: {'army_rule': prose, 'play_pattern': ''})
    out = gen.gen_html('Faction', {'meta': {}, 'meta_info': []}, 0, fid='x')

    assert out.count('</script>') == 1, 'injected </script> must be neutralised'
    assert json.loads(_blob(out, 'EXPERT'))['army_rule'] == prose


def test_gen_html_escapes_faction_name_in_title_and_heading():
    out = gen.gen_html('<b>Grey Knights</b>', {'meta': {}, 'meta_info': []}, 0,
                       fid=None)
    assert '<title>&lt;b&gt;Grey Knights&lt;/b&gt; — Findings</title>' in out
    assert '<h1>&lt;b&gt;Grey Knights&lt;/b&gt;</h1>' in out


def test_gen_html_ships_dom_escaping_helpers():
    """innerHTML writes rely on esc/escObj running at load; pin their presence."""
    out = gen.gen_html('Faction', {'meta': {}, 'meta_info': []}, 0, fid=None)
    assert 'function esc(' in out
    assert 'function escObj(' in out
    assert 'escObj(DATA);escObj(EXPERT);escObj(FACTORS);' in out


def test_gen_html_escapes_mission_key_and_array_values():
    """Mission names are object KEYS (escObj only touches values) and weapon
    lists are arrays of strings -- both must survive the escape unchanged."""
    key = '</script>x<script>'
    data = {'meta': {'competitive': {key: [
        {'name': 'U', 'weapons': ['<b>w</b>']}]}}, 'meta_info': []}
    out = gen.gen_html('Faction', data, 1, fid=None)

    assert out.count('</script>') == 1, 'injected </script> in a key must be neutralised'
    blob = json.loads(_blob(out, 'DATA'))
    assert list(blob['meta']['competitive'])[0] == key
    assert blob['meta']['competitive'][key][0]['weapons'] == ['<b>w</b>']


def test_index_escapes_tiers_payload(monkeypatch):
    """The landing page embeds the tier list (incl. expert-derived h_army) into
    a <script>; it must go through the same _js_safe as the faction pages."""
    monkeypatch.setattr(gen, 'parse_expert_assessment',
                        lambda fid: {'army_rule': '- uses <7 YPs to switch',
                                     'army_rule_rating': '', 'detachments': []})
    tiers = {'fake': {'name': 'Fake', 'overall': 50.0, 'n_units': 1,
                      'missions': {m: 50.0 for m in gen.MISSIONS}}}
    out = gen.render_tier_section(tiers)

    assert out.count('</script>') == 1, 'injected </script> must be neutralised'
    blob = re.search(r'var TIERS=(.*?);\n', out, re.S).group(1)
    assert json.loads(blob)[0]['h_army'] == 'uses <7 YPs to switch'


def test_index_esc_escapes_all_entity_chars():
    """The tier-card tooltip is written into a title="..." attribute, so the
    landing-page esc must cover '>' and '"', not just '&' and '<'."""
    assert 'replace(/"/g,"&quot;")' in gen.INDEX_SCRIPT
    assert 'replace(/>/g,"&gt;")' in gen.INDEX_SCRIPT
