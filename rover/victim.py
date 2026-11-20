"""victim script.

Serves up two web pages, one to emulate the victim running a public service, and one to show the request log. This also
starts a tcpdump on eth1 for a wireshark demo.
"""

import collections
import html
import pathlib
import socket
import subprocess  # noqa
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# handle the threading nonsense for the logs, keep the most recent 40 requests
log = collections.deque(maxlen=40)


class Server(ThreadingHTTPServer):
    """just a basic webserver listening on v6."""

    address_family = socket.AF_INET6


class VictimWebServer(BaseHTTPRequestHandler):
    """emulates a public service on the victim machine and logs every request.

    for HTTP GETs it returns a greeting string
    """

    def do_GET(self):
        """Answer any GET."""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"hello from the victim\n")

    def log_request(self, code="-", size="-"):
        """Log one line per request, with the source address and port."""
        host, port = self.client_address[:2]
        line = f"{time.strftime('%T', time.gmtime())} {host} port {port} {self.command} {self.path} {code}"
        log.append(line)


class LogWebServer(BaseHTTPRequestHandler):
    """plain ole HTML page showing the requests making it to the victim."""

    def do_GET(self):
        """Render the log."""
        body = f'<meta http-equiv="refresh" content="1"><h1>HTTP Request Log</h1><pre>{time.strftime("Current UTC Time: %T", time.gmtime())}\n'  # noqa
        body += html.escape("\n".join(reversed(log)))
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        """Don't log anything related to the log viewer."""


# start the log web server in the background
threading.Thread(target=Server(("::", 8080), LogWebServer).serve_forever, daemon=True).start()

# wait until eth1 is added by containerlab and then run a tcpdump
while not pathlib.Path("/sys/class/net/eth1").exists():
    time.sleep(1)
subprocess.Popen(
    ["/usr/bin/tcpdump", "-U", "-n", "-i", "eth1", "-w", "/captures/victim.pcap"], stderr=subprocess.DEVNULL
)

# finally, start the victim web server
Server(("::", 80), VictimWebServer).serve_forever()
