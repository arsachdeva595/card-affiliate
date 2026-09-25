#!/usr/bin/env python3
"""Submit every URL in dist/urls.txt to IndexNow (Bing, Yandex, Seznam...).

Most of this site's search traffic comes from Bing-powered engines (Bing, Yahoo,
DuckDuckGo, Ecosia, ChatGPT search), so getting indexed there quickly matters most.
Run after each deploy:  python3 generator/indexnow.py
"""
import json
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "site.config.json").read_text())
key = cfg.get("indexnow_key")
if not key:
    raise SystemExit("Set indexnow_key in site.config.json first (any 8-128 char hex string).")
urls = (ROOT / "dist" / "urls.txt").read_text().split()
host = urlparse(cfg["base_url"]).netloc
payload = json.dumps({"host": host, "key": key, "keyLocation": f"{cfg['base_url'].rstrip('/')}/{key}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=payload,
                             headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req) as r:
    print(f"IndexNow: HTTP {r.status} for {len(urls)} URLs")
