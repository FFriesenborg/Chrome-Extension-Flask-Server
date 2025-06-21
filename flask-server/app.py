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
    invoicenumber = request.args.get("invoicenumber")
    LSnumber = request.args.get("LSnumber")
    LSdate = request.args.get("LSdate")
    WEnumber = request.args.get("WEnumber")


    if not all([invoicenumber, LSnumber, LSdate, WEnumber]):
        return jsonify({'error': 'Missing one or more required parameters'}), 400

    try:
        # Convert LSdate string to datetime object
        LSdate_obj = datetime.strptime(LSdate, "%d.%m.%Y")
        Leistungdate = (LSdate_obj + timedelta(days=1)).strftime("%d.%m.%Y")
        LSdate = LSdate_obj.strftime("%d.%m.%Y")
    except ValueError:
        return jsonify({'error': 'Invalid date format for LSdate, expected dd.mm.yyyy'}), 400

    # Get invoice
    #get invoice ID
    url = f"https://{API_BRANCH_NAME}.xentral.biz/api/v1/invoices?filter[0][key]=invoice&filter[0][op]=equals&filter[0][value]={invoicenumber}"
    response = requests.get(url, headers=headers).json()
    invoiceID = response['data'][0]['id']

    #get invoice and sales order ID
    url = f"https://{API_BRANCH_NAME}.xentral.biz/api/v1/invoices/{invoiceID}"
    invoice_response = requests.get(url, headers=headers_long).json()
    invoice_data = invoice_response['data']
    orderid = invoice_data['salesOrder']['id']

    # Get full sales order details
    url = f"https://{API_BRANCH_NAME}.xentral.biz/api/v1/salesOrders/{orderid}"
    sales_data = requests.get(url, headers=headers_long).json()["data"]


    # Build the response dict
    Markant_information = {
        'Belegnummer': invoice_data['documentNumber'],
        'Belegdatum': datetime.fromisoformat(invoice_data['documentDate']).strftime("%d.%m.%Y"), 
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


#only use the following part when run locally
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))  # Default to 8000 if not set (for local testing)
    app.run(host='0.0.0.0', port=port)
'''