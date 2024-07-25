from http.server import BaseHTTPRequestHandler
import json

from utils import shopify


class handler(BaseHTTPRequestHandler):

    def do_POST(self):

        # try:
        if True:
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
            tracking_data = webhook_data['resource']

            if shopify.update_order_tracking(tracking_data):
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                return
            else:
                self.send_response(411)
                self.end_headers()
                print("Webhook content error".encode())
                return

        # except Exception as e:
        #     print(f"Webhook error: {str(e)}".encode())
        #     self.send_response(400)
        #     self.end_headers()
        #     return
