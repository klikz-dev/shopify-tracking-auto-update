from http.server import BaseHTTPRequestHandler
import os
import json
import hmac
import hashlib
import base64

from utils import recharge

SHOPIFY_SECRET = os.environ.get('SHOPIFY_SECRET', 'default_secret')


def verify_webhook(data, hmac_header):
    digest = hmac.new(SHOPIFY_SECRET.encode('utf-8'),
                      data.encode('utf-8'), hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))


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

            # Validate Token
            verified = verify_webhook(data.decode(
                'utf-8'), self.headers.get('X-Shopify-Hmac-SHA256', ''))
            if not verified:
                self.send_response(403)
                self.end_headers()
                print("Webhook verification error".encode())
                return

            # Check Customer
            orderData = json.loads(data)
            customerData = orderData['customer']
            addressData = orderData['shipping_address']

            email = customerData["email"]
            customerExists = recharge.check_customer(email=email)

            # Process Data
            if customerExists:
                print(f"Customer {email} already exists")
            else:
                customerId = recharge.create_customer(customer={
                    "email": email,
                    "first_name": customerData["first_name"],
                    "last_name": customerData["last_name"],
                    "phone": customerData["phone"],
                    "tax_exempt": customerData["tax_exempt"],
                })
                print(f"Customer {email} ({customerId}) created successfully")

                addressId = recharge.create_address(address={
                    "customer_id": customerId,
                    "address1": addressData["address1"],
                    "address2": addressData["address2"],
                    "city": addressData["city"],
                    "company": addressData["company"],
                    "country_code": addressData["country_code"],
                    "country": addressData["country"],
                    "first_name": addressData["first_name"],
                    "last_name": addressData["last_name"],
                    "phone": addressData["phone"],
                    "province": addressData["province"],
                    "zip": addressData["zip"],
                })
                print(f"Address {addressId} created successfully")

            # Handle Response
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()

        except Exception as e:
            print(f"Webhook error: {str(e)}".encode())
            return
