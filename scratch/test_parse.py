import json, re

with open('scratch/chrome_dom.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

def parse_metrics(elements):
    metrics = {
        'likes': None,
        'comments': None,
        'saves': None,
        'shares': None
    }

    # 1. First pass: look for explicit non-zero digit counts
    for el in elements:
        e2e = (el.get('e2e') or '').lower()
        aria = (el.get('aria') or '').strip()
        text = (el.get('text') or '').strip()

        # Check likes
        if not metrics['likes']:
            if 'like-count' in e2e or 'browse-like-count' in e2e:
                m = re.search(r'([0-9]+[0-9.,]*[KMBkmb]?)', text)
                if m: metrics['likes'] = m.group(1)
            if not metrics['likes'] and aria and 'like' in aria.lower():
                m = re.search(r'([0-9]+[0-9.,]*[KMBkmb]?)\s*likes?', aria, re.I)
                if m: metrics['likes'] = m.group(1)

        # Check comments
        if not metrics['comments']:
            if 'comment-count' in e2e or 'browse-comment-count' in e2e:
                m = re.search(r'([0-9]+[0-9.,]*[KMBkmb]?)', text)
                if m: metrics['comments'] = m.group(1)
            if not metrics['comments'] and aria and 'comment' in aria.lower():
                m = re.search(r'([0-9]+[0-9.,]*[KMBkmb]?)\s*comments?', aria, re.I)
                if m: metrics['comments'] = m.group(1)

        # Check saves/favorites
        if not metrics['saves']:
            if 'favorite-count' in e2e or 'undefined-count' in e2e:
                m = re.search(r'([0-9]+[0-9.,]*[KMBkmb]?)', text)
                if m: metrics['saves'] = m.group(1)
            if not metrics['saves'] and aria and any(x in aria.lower() for x in ['favorite', 'save', 'bookmark']):
                m = re.search(r'([0-9]+[0-9.,]*[KMBkmb]?)\s*(?:added to\s*)?(?:favorites?|saves?)', aria, re.I)
                if m: metrics['saves'] = m.group(1)

        # Check shares
        if not metrics['shares']:
            if 'share-count' in e2e:
                m = re.search(r'([0-9]+[0-9.,]*[KMBkmb]?)', text)
                if m: metrics['shares'] = m.group(1)
            if not metrics['shares'] and aria and 'share' in aria.lower():
                m = re.search(r'([0-9]+[0-9.,]*[KMBkmb]?)\s*shares?', aria, re.I)
                if m: metrics['shares'] = m.group(1)

    # 2. Second pass: If elements exist on screen with placeholder labels, it means 0!
    has_action_bar = any('like' in (el.get('e2e') or '') or 'like' in (el.get('aria') or '').lower() for el in elements)
    if has_action_bar:
        if metrics['likes'] is None: metrics['likes'] = '0'
        if metrics['comments'] is None: metrics['comments'] = '0'
        if metrics['saves'] is None: metrics['saves'] = '0'
        if metrics['shares'] is None: metrics['shares'] = '0'

    return metrics

res = parse_metrics(items)
print("Parsed result:", res)
