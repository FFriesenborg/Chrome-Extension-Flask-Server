from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from flask_cors import CORS  # import CORS
from dotenv import load_dotenv
import os
import requests

app = Flask(__name__)

# Apply CORS to the entire app or a specific route
CORS(app, resources={r"/data": {"origins": "*"}})  # This will allow cross-origin requests to the /data route from any origin.

load_dotenv()

#to protect the API credentials
API_TOKEN = os.getenv("API_TOKEN")
API_BRANCH_NAME = os.getenv("API_BRANCH_NAME")

headers = {
    "accept": "application/vnd.xentral.minimal+json",
    "authorization": f"Bearer {API_TOKEN}"
}

headers_long = {
    "accept": "application/json",
    "authorization": f"Bearer {API_TOKEN}"
}

@app.route('/data')
def get_data():
    # Get query parameters
    ordernumber = request.args.get("ordernumber")
    LSnumber = request.args.get("LSnumber")
    LSdate = request.args.get("LSdate")
    WEnumber = request.args.get("WEnumber")


    if not all([ordernumber, LSnumber, LSdate, WEnumber]):
        return jsonify({'error': 'Missing one or more required parameters'}), 400

    try:
        # Convert LSdate string to datetime object
        LSdate_obj = datetime.strptime(LSdate, "%d.%m.%Y")
        Leistungdate = (LSdate_obj + timedelta(days=1)).strftime("%d.%m.%Y")
        LSdate = LSdate_obj.strftime("%d.%m.%Y")
    except ValueError:
        return jsonify({'error': 'Invalid date format for LSdate, expected dd.mm.yyyy'}), 400

    # Get sales order
    url = f"https://{API_BRANCH_NAME}.xentral.biz/api/v1/salesOrders?filter[0][key]=documentNumber&filter[0][op]=equals&filter[0][value]={ordernumber}"
    response = requests.get(url, headers=headers).json()

    if not response["data"]:
        return jsonify({"error": "Order not found"}), 404

    orderid = response["data"][0]["id"]

    # Get full sales order details
    url = f"https://{API_BRANCH_NAME}.xentral.biz/api/v1/salesOrders/{orderid}"
    sales_data = requests.get(url, headers=headers_long).json()["data"]

    # Get invoice
    url = f"https://{API_BRANCH_NAME}.xentral.biz/api/v1/invoices?filter[0][key]=salesOrder&filter[0][op]=equals&filter[0][value]={orderid}"
    invoice_response = requests.get(url, headers=headers).json()
    invoice_data = invoice_response["data"][0]

    # Build the response dict
    Markant_information = {
        'Belegnummer': invoice_data['number'],
        'Belegdatum': datetime.fromisoformat(invoice_data['date']).strftime("%d.%m.%Y"), 
        'Bestellnummer': sales_data['customerOrderNumber'],
        'Bestelldatum': datetime.strptime(sales_data['date'], "%Y-%m-%d").strftime("%d.%m.%Y"),
        'Lieferscheinnummer': LSnumber,
        'Lieferscheindatum': LSdate,
        'Liefer-Leistungsdatum': Leistungdate,
        'Waehrung': 'EUR',
        'Valutadatum': '',
        'Wareneingangsnummer': WEnumber,
        'Wareneingangdatum': LSdate,
        'Rechnungsreferenz-Nr.': sales_data['customerOrderNumber'],
        'Rechnungsreferenzdatum': Leistungdate,
        'Auftragsnummer': '',
        'Zahlfrist': '29',
        'GLN': sales_data['financials']['billingAddress']['gln']
    }

    return jsonify(Markant_information)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))  # Default to 8000 if not set (for local testing)
    app.run(host='0.0.0.0', port=port)
