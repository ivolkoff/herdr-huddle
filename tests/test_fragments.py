import json
import os
import subprocess
import sys
import tempfile
import unittest

HUDDLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "huddle")

# runs as $BROWSER: webbrowser.open() hands it the page URL
FAKE_BROWSER = r"""
import json, re, sys, urllib.error, urllib.request

url, out = sys.argv[1], sys.argv[2]

def get(path):
    try:
        with urllib.request.urlopen(url + path) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, ""

_, page = get("")
gen = int(re.search(r"HD_GEN=(\d+)", page).group(1))
seen = {p: get("f/" + p) for p in ("status.html", "status.html?x=1", "missing.html", "../secret.html")}
body = json.dumps({"status": "dismissed", "gen": gen}).encode()
urllib.request.urlopen(urllib.request.Request(url + "answer", body))
with open(out, "w") as f:
    json.dump(seen, f)
"""


class Fragments(unittest.TestCase):
    def run_huddle(self, d, spec):
        spec_path, browser, out = (os.path.join(d, n) for n in ("spec.json", "browser.py", "out.json"))
        with open(spec_path, "w") as f:
            json.dump(spec, f)
        with open(browser, "w") as f:
            f.write(FAKE_BROWSER)
        env = {**os.environ, "BROWSER": f"{sys.executable} {browser} %s {out}"}
        r = subprocess.run([sys.executable, HUDDLE, spec_path, "--browser", "--timeout", "10"],
                           env=env, capture_output=True, text=True, timeout=30)
        with open(out) as f:
            return r, json.load(f)

    def test_served_from_the_directory_only(self):
        with tempfile.TemporaryDirectory() as d:
            os.mkdir(os.path.join(d, "live"))
            with open(os.path.join(d, "live", "status.html"), "w") as f:
                f.write("<b>ok</b>")
            with open(os.path.join(d, "secret.html"), "w") as f:
                f.write("secret")
            _, seen = self.run_huddle(d, {"prompt": "p", "fragments": "live"})
        self.assertEqual(seen["status.html"], [200, "<b>ok</b>"])
        self.assertEqual(seen["status.html?x=1"], [200, "<b>ok</b>"])
        self.assertEqual(seen["missing.html"][0], 404)
        self.assertEqual(seen["../secret.html"][0], 404)

    def test_polling_keeps_the_dismissal_working(self):
        with tempfile.TemporaryDirectory() as d:
            os.mkdir(os.path.join(d, "live"))
            r, _ = self.run_huddle(d, {"prompt": "p", "fragments": "live"})
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_no_directory_no_fragments(self):
        with tempfile.TemporaryDirectory() as d:
            _, seen = self.run_huddle(d, {"prompt": "p"})
        self.assertEqual(seen["status.html"][0], 404)


if __name__ == "__main__":
    unittest.main()
