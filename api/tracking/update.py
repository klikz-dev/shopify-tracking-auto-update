from http.server import BaseHTTPRequestHandler
import json

from utils import shopify


class handler(BaseHTTPRequestHandler):

    def do_POST(self):

        try:
            # Validate content length
            content_length = self.headers.get('content-length')
            if not content_length:
                self._send_response(411, "Length Required")
                print("Webhook content error")
                return

            # Read Data
            data = self.rfile.read(int(content_length))

            # Check Customer
            webhook_data = json.loads(data)
            tracking_data = webhook_data['body']['resource']

            print(json.dumps(tracking_data, indent=4))

            shopify.update_order_tracking(
                tracking_data=tracking_data,
                test="timothymccarthy@bedjet.com"
            )

            self._send_response(200, "OK")

            return

        except Exception as e:
            print(e)
            self._send_response(400, f"{str(e)}")

    def do_GET(self):
        self._send_response(200, 'Shipwire tracking integration endpoint')

    def do_HEAD(self):
        self._send_response(200, '')

    def _send_response(self, status_code, message):
        """Helper method to send HTTP response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if message:
            self.wfile.write(message.encode('utf-8'))
