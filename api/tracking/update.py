from http.server import BaseHTTPRequestHandler
import json

from utils import service


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
            print(json.dumps(tracking_data, indent=2))

            # Get Shipwire Data
            shipwire_order_id = tracking_data['orderId']
            shipwire_data = service.get_shipwire_data(shipwire_order_id)
            print(json.dumps(shipwire_data, indent=2))

            # Get Shopify Data
            email, fulfillable_line_items = service.get_shopify_data(
                shipwire_data['order_number'])
            print(json.dumps(fulfillable_line_items, indent=2))

            if email != "timothymccarthy@bedjet.com":
                self._send_response(403, "Test mode")
                return

            # Generate fulfillment lines based on Shipwire and Shoify Data
            fulfillment_lines = service.generate_fulfillment_lines(
                shipwire_data['trackings'], fulfillable_line_items)
            print(json.dumps(fulfillment_lines, indent=2))

            # Update to Shpoify
            for fulfillment in fulfillment_lines:
                response = service.create_fulfillment(fulfillment)

                try:
                    fulfillment_data = response['data']['fulfillmentCreateV2']['fulfillment']
                    if fulfillment_data and fulfillment_data['status'] == "SUCCESS":
                        print(
                            f"Tracking information for Order {shipwire_data['order_number']} updated successfully.")
                    else:
                        print(response)
                except:
                    raise Exception(
                        f"Failed to update tracking information to Shopify. Response: {response}")

            # Response
            self._send_response(200, "OK")
            return

        except Exception as e:
            print(str(e))
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
