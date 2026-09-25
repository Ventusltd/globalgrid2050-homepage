"""Refresh the no-JavaScript nests and catalogue from the validated JSON source."""
from html import escape
from pathlib import Path
import re
from urllib.parse import urlparse
from releases import load

ROOT = Path(__file__).resolve().parents[1]


def app_url(value):
    parsed = urlparse(value)
    hostname = parsed.hostname or ''
    if parsed.scheme != 'https' or parsed.username or parsed.password or any(hostname == h or hostname.endswith('.' + h) for h in ['github.com', 'githubusercontent.com']):
        raise ValueError('Expected an HTTPS app URL')
    return escape(value, quote=True)


def build(root=ROOT):
    root = Path(root)
    data = load(root / 'data/homepage.json')
    by_id = {entity['id']: entity for entity in data['entities']}

    def current(entity):
        return next(release for release in entity['releases'] if release['id'] == entity['operative_release_id'])

    def nest(entity, position, opened=False):
        title = escape(entity['title'])
        subtitle = '<small>' + escape(entity['subtitle']) + '</small>' if entity.get('subtitle') else ''
        description = '<p>' + escape(entity['description']) + '</p>' if entity.get('description') else ''
        launch = escape(entity.get('launch_label') or 'Open ' + entity['title'])
        children = ''.join(nest(child, '&#8611;') for child in data['entities'] if child.get('parent_id') == entity['id'])
        return f'<details id="{escape(entity["id"], quote=True)}"' + (' open' if opened else '') + f'><summary><span class="number">{position}</span><span class="title">{title}{subtitle}</span></summary><div class="inside">{description}<a class="launch" href="{app_url(current(entity)["url"])}">{launch} &rarr;</a>{children}</div></details>'

    nests = '\n'.join(nest(by_id[item['entity_id']], f'{index + 1:02}', item.get('open', False)) for index, item in enumerate(data['view']['items']))
    rows = []
    for entity in data['entities']:
        release = current(entity)
        area = entity.get('subtitle') or by_id.get(entity.get('parent_id'), {}).get('title', '\u2014')
        rows.append(f'<tr data-entity-id="{escape(entity["id"], quote=True)}"><th scope="row"><a href="{app_url(release["url"])}">{escape(entity["title"])}</a></th><td>{escape(area)}</td><td>{escape(release["label"])}</td></tr>')
    path = root / 'index.html'
    html = path.read_text(encoding='utf-8')
    html, count = re.subn(r'(<section id="nests"[^>]*>).*?(</section>)', lambda m: m[1] + '\n' + nests + '\n' + m[2], html, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Missing nests mount')
    html, count = re.subn(r'(<tbody id="catalogueRows">).*?(</tbody>)', lambda m: m[1] + '\n' + '\n'.join(rows) + '\n' + m[2], html, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Missing catalogue mount')
    html = html.replace('aria-labelledby="catalogueHeading" hidden', 'aria-labelledby="catalogueHeading"')
    html, count = re.subn(r'(<a id="archiveLink" href=")[^"]*(")', lambda m: m[1] + app_url(data['view']['archive_url']) + m[2], html, count=1)
    if count != 1:
        raise ValueError('Missing archive link')
    path.write_text(html, encoding='utf-8')
    print(f'Built {len(data["view"]["items"])} pinned nests and {len(rows)} catalogue rows')


if __name__ == '__main__':
    build()
