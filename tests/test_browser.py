"""Testes de interface e acessibilidade básica em Chromium real."""
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def run():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    for width in (320, 390, 600, 768, 1440):
                        page = browser.new_page(viewport={"width": width, "height": 900})
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        page.route("https://fonts.googleapis.com/**", lambda route: route.abort())
                        page.route("https://fonts.gstatic.com/**", lambda route: route.abort())
                        page.goto(f"http://127.0.0.1:{server.server_port}/index.html")
                        assert page.locator("html").get_attribute("lang") == "pt-BR"
                        assert page.locator(".right-login").count() == 1
                        assert page.locator(".right-login").evaluate("(el) => getComputedStyle(el).display") == "flex"
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow em {width}px"
                        assert page.get_by_label("Usuário").count() == 1
                        assert page.get_by_label("Senha").count() == 1
                        page.get_by_label("Usuário").fill("usuario-ficticio")
                        page.get_by_label("Senha").fill("senha-ficticia")
                        assert page.get_by_label("Senha").get_attribute("type") == "password"
                        assert page.get_by_role("button", name="Login").get_attribute("type") == "button"
                        assert not errors, errors
                        print(f"PASS: Login {width}px, labels, campos e layout")
                        page.close()
                finally:
                    browser.close()
        finally:
            server.shutdown()


if __name__ == "__main__":
    run()
