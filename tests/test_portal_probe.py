"""Tests for portal-probe.py (local server only, no network). Run: python3 -m unittest discover tests"""
import http.server
import importlib.util
import json
import os
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("portal_probe", os.path.join(HERE, "..", "portal-probe.py"))
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)

ROUTES = {}   # path -> (code, content_type, body)
HITS = []


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        HITS.append(path)
        code, ctype, body = ROUTES.get(path, (404, "text/plain", "nope"))
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def js(obj, code=200):
    return (code, "application/json", json.dumps(obj))


class ProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        ROUTES.clear()
        del HITS[:]

    def test_ok_portal(self):
        ROUTES["/api/3/action/status_show"] = js({"success": True, "result": {"ckan_version": "2.10.1"}})
        ROUTES["/api/3/action/package_search"] = js({"success": True, "result": {"count": 42}})
        r = pp.probe(self.base, timeout=5)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["datasets"], 42)
        self.assertEqual(r["ckan_version"], "2.10.1")
        self.assertEqual(r["api_base"], self.base)

    def test_no_search(self):
        ROUTES["/api/3/action/status_show"] = js({"success": True, "result": {"ckan_version": "2.9"}})
        ROUTES["/api/3/action/package_search"] = js({"success": False}, 403)
        r = pp.probe(self.base, timeout=5)
        self.assertEqual(r["status"], "no_search")
        self.assertEqual(r["ckan_version"], "2.9")

    def test_not_ckan_html_answer(self):
        html = (200, "text/html", "<html>hello</html>")
        ROUTES["/api/3/action/status_show"] = html
        ROUTES["/api/3/action/package_search"] = html
        r = pp.probe(self.base, timeout=5)
        self.assertEqual(r["status"], "not_ckan")
        self.assertEqual(r["datasets"], "")

    def test_fallback_to_host_root_on_404(self):
        # The sub-path answers 404; the host root works.
        ROUTES["/api/3/action/status_show"] = js({"success": True, "result": {"ckan_version": "2.9"}})
        ROUTES["/api/3/action/package_search"] = js({"success": True, "result": {"count": 7}})
        r = pp.probe(self.base + "/ckan", timeout=5)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["api_base"], self.base)
        self.assertEqual(r["datasets"], 7)
        self.assertIn("/ckan/api/3/action/status_show", HITS)

    def test_http_error_no_retry_on_4xx(self):
        ROUTES["/api/3/action/status_show"] = (403, "text/plain", "no")
        ROUTES["/api/3/action/package_search"] = (403, "text/plain", "no")
        r = pp.probe(self.base, timeout=5)
        self.assertEqual(r["status"], "http_error")
        self.assertEqual(r["http_status"], 403)
        self.assertEqual(HITS.count("/api/3/action/status_show"), 1)
        self.assertEqual(HITS.count("/api/3/action/package_search"), 1)

    def test_5xx_retried_once(self):
        ROUTES["/api/3/action/status_show"] = (503, "text/plain", "no")
        ROUTES["/api/3/action/package_search"] = (503, "text/plain", "no")
        r = pp.probe(self.base, timeout=5)
        self.assertEqual(r["status"], "http_error")
        self.assertEqual(HITS.count("/api/3/action/status_show"), 2)

    def test_output_sorted(self):
        ROUTES["/api/3/action/status_show"] = js({"success": True, "result": {"ckan_version": "2.9"}})
        ROUTES["/api/3/action/package_search"] = js({"success": True, "result": {"count": 1}})
        urls = [self.base + "/b", self.base + "/a", self.base]
        rows = pp.run(urls, timeout=5, today="2026-10-27")
        keys = [(r["host"], r["url"]) for r in rows]
        self.assertEqual(keys, sorted(keys))
        self.assertTrue(all(r["checked_on"] == "2026-10-27" for r in rows))


if __name__ == "__main__":
    unittest.main()
