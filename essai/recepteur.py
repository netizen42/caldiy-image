"""Récepteur de webhooks de l'essai : écrit chaque requête (en-têtes et corps) dans /recu/<n>.json."""
import http.server, json, itertools

n = itertools.count(1)


class R(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        corps = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()
        with open(f"/recu/{next(n)}.json", "w") as f:
            json.dump({"en_tetes": dict(self.headers), "corps": corps}, f)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


http.server.HTTPServer(("0.0.0.0", 8080), R).serve_forever()
