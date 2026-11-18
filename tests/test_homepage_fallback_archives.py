"""Couple real Python fallback links to the actual JavaScript archive rule."""
import copy
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_homepage_fallback as fallback

class Links(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.entity = None; self.anchor = None; self.links = {}; self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr': self.entity = attrs.get('data-entity-id')
        if tag == 'a' and self.entity: self.anchor = [attrs.get('href'), '']
    def handle_data(self, text):
        if self.anchor is not None: self.anchor[1] += text
    def handle_endtag(self, tag):
        if tag == 'a' and self.anchor is not None:
            self.links[(self.entity, self.anchor[1].strip())] = self.anchor[0]; self.anchor = None
        if tag == 'tr': self.entity = None

class FallbackArchiveTests(unittest.TestCase):
    def test_archive_decisions_match_actual_javascript_renderer(self):
        base = {'id': 'old', 'label': 'Old build', 'status': 'available', 'url': 'https://example.com/live/', 'archive_url': 'https://example.com/v/old/?a=1&b=2', 'archive_kind': 'app'}
        cases = [{'release': copy.deepcopy(base), 'operative': flag} for flag in (False, True)]
        for changes in ({'archive_kind': 'manifest'}, {'archive_url': 'https://github.com/owner/repo/blob/main/manifest.json'}, {'archive_url': None}, {'status': 'candidate'}):
            cases.append({'release': {**base, **changes}, 'operative': False})
        javascript = (ROOT / 'assets/versioned-homepage.js').read_text(encoding='utf8')
        functions = []
        for name in ('safeUrl', 'appUrl', 'releaseRow'):
            match = re.search(r'  function ' + name + r'\([^\n]*\) \{.*?\n  \}', javascript, re.S)
            self.assertIsNotNone(match, name); functions.append(match.group(0))
        program = """const fs=require('node:fs'),vm=require('node:vm');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const context={URL,node:(tag,text,className)=>({tag,text,className,children:[],append(...nodes){this.children.push(...nodes);}}),link:(text,href)=>({text,href})};
vm.createContext(context);vm.runInContext(input.functions.join('\\n'),context);
process.stdout.write(JSON.stringify(input.cases.map(c=>context.releaseRow(c.release,c.operative).children[1].href)));
"""
        result = subprocess.run(['node', '-e', program], input=json.dumps({'functions': functions, 'cases': cases}), text=True, capture_output=True, check=True)
        actual = [unescape(fallback.release_app_url(c['release'], c['operative'])) for c in cases]
        self.assertEqual(actual, json.loads(result.stdout))
        self.assertEqual(actual[0], base['archive_url']); self.assertEqual(actual[1], base['url'])

    def test_real_v191_archive_and_all_other_navigation_remain_correct(self):
        data = json.loads((ROOT / 'data/homepage.json').read_text(encoding='utf8'))
        original_data = json.dumps(data, sort_keys=True)
        before = Links((ROOT / 'index.html').read_text(encoding='utf8')).links
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'data').mkdir()
            for name in ('homepage.json', 'entity-types.json', 'presentation.json'):
                shutil.copyfile(ROOT / 'data' / name, root / 'data' / name)
            shutil.copyfile(ROOT / 'index.html', root / 'index.html')
            fallback.build(root)
            first = (root / 'index.html').read_bytes(); after = Links(first.decode()).links
            atlas = next(e for e in data['entities'] if e['id'] == 'gridatlas')
            old = next(r for r in atlas['releases'] if r['id'] == '202611161720')
            self.assertEqual(after[('gridatlas', old['label'])], 'https://ventusltd.github.io/gridatlas/atlas/v/202611161720/')
            for entity in data['entities']:
                operative = next(r for r in entity['releases'] if r['id'] == entity['operative_release_id'])
                if (entity['id'], entity['title']) in after:
                    self.assertEqual(after[(entity['id'], entity['title'])], operative['url'])
                for release in entity['releases']:
                    key = (entity['id'], release['label'])
                    if key not in after: continue
                    if entity['id'] != 'gridatlas': self.assertEqual(after[key], before[key])
                    if release['id'] == entity['operative_release_id']: self.assertEqual(after[key], release['url'])
            self.assertEqual(json.dumps(json.loads((root / 'data/homepage.json').read_text(encoding='utf8')), sort_keys=True), original_data)
            fallback.build(root); self.assertEqual((root / 'index.html').read_bytes(), first)

if __name__ == '__main__': unittest.main()
