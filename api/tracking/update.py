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
                print("Webhook content error".encode())
                return

            # Read Data
            data = self.rfile.read(int(content_length))

            # Check Customer
            webhook_data = json.loads(data)
            tracking_data = webhook_data['resource']

            shopify.update_order_tracking(tracking_data)

            self._send_response(200, "OK")

            return

        except Exception as e:
            print(f"Webhook error: {str(e)}".encode())
            self._send_response(400, f"Bad Request: {str(e)}")

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
