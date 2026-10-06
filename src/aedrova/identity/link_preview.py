"""Bounded HTTPS metadata previews. Pin the connection to a checked public address.

No cookies, authentication, images, redirects or downloads. HTML is parsed as data.
"""

import http.client
import ipaddress
import socket
import ssl
from html.parser import HTMLParser
from urllib.parse import urlsplit


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            name = attrs.get("property") or attrs.get("name")
            content = attrs.get("content", "")
            if name == "og:title":
                self.title = content[:180]
            elif name in ("description", "og:description"):
                self.description = content[:300]

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title and not self.title:
            self.title = data.strip()[:180]


def public_address(host):
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Preview target must use public addresses.")
    return addresses[0][4][0]


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host, timeout=4, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def fetch_preview(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or len(url) > 2000
    ):
        raise ValueError("Only public HTTPS pages can be previewed.")
    connection = PinnedHTTPS(parsed.hostname, public_address(parsed.hostname))
    try:
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        connection.request(
            "GET",
            path,
            headers={
                "User-Agent": "Aedrova-LinkPreview/1.0",
                "Accept": "text/html",
                "Accept-Encoding": "identity",
            },
        )
        response = connection.getresponse()
        if response.status != 200 or "text/html" not in response.getheader("content-type", ""):
            raise ValueError("Preview unavailable.")
        raw = response.read(100001)
        if len(raw) > 100000:
            # Only inspect a bounded prefix; OG metadata normally lives in the head.
            raw = raw[:100000]
        metadata = Metadata()
        metadata.feed(raw.decode("utf-8", errors="replace"))
        return {
            "url": url,
            "title": metadata.title or parsed.hostname,
            "description": metadata.description,
        }
    finally:
        connection.close()
