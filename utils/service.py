from . import shipwire, shopify


def get_shipwire_data(shipwire_order_id):
    shipwire_order = shipwire.get_order(shipwire_order_id)
    shipwire_order_trackings = shipwire.get_order_trackings(shipwire_order_id)

    order_number = shipwire_order['orderNo'].split(".")[0]
    trackings = []

    for shipwire_order_tracking in shipwire_order_trackings:
        piece_id = shipwire_order_tracking['resource']['pieceId']
        shipwire_order_piece = shipwire.get_order_piece(
            shipwire_order_id, piece_id)

        sku = shipwire_order_piece['sku']
        quantity = shipwire_order_piece['quantity']

        carrier = shipwire_order_tracking['resource']['carrier']
        number = shipwire_order_tracking['resource']['number']

        trackings.append({
            'sku': sku,
            'quantity': quantity,
            'carrier': carrier,
            'number': number,
        })

    return {
        'order_number': order_number,
        'trackings': trackings,
    }


def get_shopify_data(order_number):
    shopify_order = shopify.get_order(order_number)
    fulfillment_orders = shopify.get_fulfillment_orders(shopify_order.id)

    fulfillable_line_items = []

    if len(fulfillment_orders) > 0:
        line_items = fulfillment_orders[0]['line_items']

        for line_item in line_items:
            variant = shopify.get_variant(line_item['variant_id'])

            fulfillable_line_items.append({
                'id': line_item['id'],
                'fulfillment_order_id': line_item['fulfillment_order_id'],
                'variant_id': line_item['variant_id'],
                'sku': variant.sku
            })

    return shopify_order.email, fulfillable_line_items


def generate_fulfillment_lines(trackings, fulfillable_line_items):
    fulfillments = []

    for fl in fulfillable_line_items:
        kit_skus = shipwire.get_kits(fl['sku'])

        if len(kit_skus) > 0:
            company = None
            tracking_numbers = []
            for tracking in trackings:
                company = tracking['carrier']
                tracking_numbers.append(tracking['number'])

            if company and len(tracking_numbers) > 0:
                fulfillments.append({
                    "fulfillment": {
                        "lineItemsByFulfillmentOrder": {
                            "fulfillmentOrderId": f"gid://shopify/FulfillmentOrder/{fl['fulfillment_order_id']}",
                            "fulfillmentOrderLineItems": [{
                                'id': f"gid://shopify/FulfillmentOrderLineItem/{fl['id']}",
                                'quantity': tracking['quantity']
                            }]
                        },
                        "trackingInfo": {
                            "company": company,
                            "numbers": tracking_numbers,
                        },
                        "notifyCustomer": False,
                    }
                })

        else:
            for tracking in trackings:
                if fl['sku'] == tracking['sku']:
                    fulfillments.append({
                        "fulfillment": {
                            "lineItemsByFulfillmentOrder": {
                                "fulfillmentOrderId": f"gid://shopify/FulfillmentOrder/{fl['fulfillment_order_id']}",
                                "fulfillmentOrderLineItems": [{
                                    'id': f"gid://shopify/FulfillmentOrderLineItem/{fl['id']}",
                                    'quantity': tracking['quantity']
                                }]
                            },
                            "trackingInfo": {
                                "company": tracking['carrier'],
                                "number": tracking['number'],
                            },
                            "notifyCustomer": False,
                        }
                    })

    # Regroup fulfillments for line items to resolve fulfillmentOrderId is changed issue.
    if len(fulfillments) > 1:
        fulfillmentOrderLineItems = []
        company = None
        numbers = []
        for fulfillment in fulfillments:
            fulfillmentOrderLineItems.append(
                fulfillment['fulfillment']['lineItemsByFulfillmentOrder']['fulfillmentOrderLineItems'][0])
            company = fulfillment['fulfillment']['trackingInfo']['company']
            numbers.append(fulfillment['fulfillment']
                           ['trackingInfo']['number'])

        fulfillments = [{
            "fulfillment": {
                "lineItemsByFulfillmentOrder": {
                    "fulfillmentOrderId": f"gid://shopify/FulfillmentOrder/{fl['fulfillment_order_id']}",
                    "fulfillmentOrderLineItems": fulfillmentOrderLineItems
                },
                "trackingInfo": {
                    "company": company,
                    "numbers": numbers,
                },
                "notifyCustomer": False,
            }
        }]

    return fulfillments


def create_fulfillment(fulfillment):
    mutation = """
        mutation fulfillmentCreateV2($fulfillment: FulfillmentV2Input!) {
            fulfillmentCreateV2(fulfillment: $fulfillment) {
                fulfillment {
                    id
                    status
                }
                userErrors {
                    field
                    message
                }
            }
        }
    """

    variables = fulfillment

    return shopify.create_fulfillment(mutation, variables)
