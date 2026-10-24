"""Screenshot UI routes for visual checks: python scripts/shot.py "#/runs/ID/requirements" out.png"""

import sys

from playwright.sync_api import sync_playwright

base = "http://127.0.0.1:8765/"
routes = sys.argv[1::2]
outs = sys.argv[2::2]
with sync_playwright() as p:
    b = p.chromium.launch()
    for route, out in zip(routes, outs):
        pg = b.new_page(viewport={"width": 1500, "height": 900})
        pg.goto(base + route)
        pg.wait_for_timeout(2500)
        pg.screenshot(path=out)
    b.close()
