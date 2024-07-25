from http.server import BaseHTTPRequestHandler
import json

from utils import shopify


class handler(BaseHTTPRequestHandler):

    def do_POST(self):

        try:
            # Validate content length
            content_length = self.headers.get('content-length')
            if not content_length:
                self.send_response(411)
                self.end_headers()
                print("Webhook content error".encode())
                return

            # Read Data
            data = self.rfile.read(int(content_length))

            # Check Customer
            webhook_data = json.loads(data)
            print(json.dumps(webhook_data, indent=2))

            tracking_data = webhook_data['resource']

            shopify.update_order_tracking(
                tracking_data, test="timothymccarthy@bedjet.com")

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()

            return

        except Exception as e:
            print(f"Webhook error: {str(e)}".encode())

            self.send_response(400)
            self.end_headers()

            return
