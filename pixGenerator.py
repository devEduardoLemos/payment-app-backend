import qrcode
from typing import Optional
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from flask_cors import CORS
import base64
from io import BytesIO
import os
import re
from functools import wraps
from dotenv import load_dotenv


# Define a function to create a PIX payload
def create_pix_payload(
    pix_key: str,
    merchant_name: str,
    merchant_city: str,
    transaction_amount: Optional[float] = None,
    description: Optional[str] = None,
    expiration_minutes: Optional[int] = None
) -> str:
    # Constants
    ID_PAYLOAD_FORMAT_INDICATOR = "00"
    ID_MERCHANT_ACCOUNT_INFORMATION = "26"
    ID_MERCHANT_ACCOUNT_GUI = "00"
    ID_MERCHANT_ACCOUNT_KEY = "01"
    ID_MERCHANT_ACCOUNT_DESCRIPTION = "02"
    ID_MERCHANT_CATEGORY_CODE = "52"
    ID_TRANSACTION_CURRENCY = "53"
    ID_TRANSACTION_AMOUNT = "54"
    ID_COUNTRY_CODE = "58"
    ID_MERCHANT_NAME = "59"
    ID_MERCHANT_CITY = "60"
    ID_ADDITIONAL_DATA_FIELD_TEMPLATE = "62"
    ID_ADDITIONAL_DATA_TXID = "05"
    ID_CRC = "63"
    
    def format_value(tag: str, value: str) -> str:
        return f"{tag}{len(value):02}{value}"
    
    payload = []
    
    # Payload format indicator
    payload.append(format_value(ID_PAYLOAD_FORMAT_INDICATOR, "01"))
    
    # Merchant account information
    merchant_account_information = []
    merchant_account_information.append(format_value(ID_MERCHANT_ACCOUNT_GUI, "BR.GOV.BCB.PIX"))
    merchant_account_information.append(format_value(ID_MERCHANT_ACCOUNT_KEY, pix_key))
    if description:
        merchant_account_information.append(format_value(ID_MERCHANT_ACCOUNT_DESCRIPTION, description))
    
    merchant_account_info_value = "".join(merchant_account_information)
    payload.append(format_value(ID_MERCHANT_ACCOUNT_INFORMATION, merchant_account_info_value))
    
    # Merchant category code
    payload.append(format_value(ID_MERCHANT_CATEGORY_CODE, "0000"))
    
    # Transaction currency (BRL)
    payload.append(format_value(ID_TRANSACTION_CURRENCY, "986"))
    
    # Transaction amount
    if transaction_amount:
        payload.append(format_value(ID_TRANSACTION_AMOUNT, f"{transaction_amount:.2f}"))
    
    # Country code
    payload.append(format_value(ID_COUNTRY_CODE, "BR"))
    
    # Merchant name
    payload.append(format_value(ID_MERCHANT_NAME, merchant_name))
    
    # Merchant city
    payload.append(format_value(ID_MERCHANT_CITY, merchant_city))
    
    # Additional data field template
    additional_data_field_template = []
    additional_data_field_template.append(format_value(ID_ADDITIONAL_DATA_TXID, "TX12345"))  # Example TXID
    
    if expiration_minutes:
        expiration_time = (datetime.utcnow() + timedelta(minutes=expiration_minutes)).strftime('%Y%m%d%H%M%S')
        additional_data_field_template.append(format_value("50", expiration_time))
    
    additional_data_field_value = "".join(additional_data_field_template)
    payload.append(format_value(ID_ADDITIONAL_DATA_FIELD_TEMPLATE, additional_data_field_value))
    
    # CRC placeholder (will be calculated later)
    payload_str = "".join(payload)
    payload_str += ID_CRC + "04"
    
    return payload_str

# Function to generate the CRC16-CCITT checksum
def calculate_crc(payload: str) -> str:
    poly = 0x1021
    crc = 0xFFFF
    for byte in payload.encode():
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF
    return format(crc, '04X')

# Generate the QR code with the PIX payload
def generate_pix_qrcode(
    pix_key: str,
    merchant_name: str,
    merchant_city: str,
    amount: Optional[float] = None,
    description: Optional[str] = None,
    expiration_minutes: Optional[int] = None
):
    # Create the PIX payload
    payload = create_pix_payload(pix_key, merchant_name, merchant_city, amount, description, expiration_minutes)
    crc = calculate_crc(payload)
    payload += crc

    # Initialize the QRCode object
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)


    # Generate the QR code image and store it in-memory
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()  # In-memory byte stream
    img.save(buffer, format='PNG')
    buffer.seek(0)  # Move the cursor to the beginning of the stream

    # Encode the image in base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Close the buffer
    buffer.close()

    return [payload,img_base64]

def clean_string(input_string: str) -> str:
    """
    Removes blank spaces and special characters from the given string.
    Keeps only alphanumeric characters.
    """
    # Remove all non-alphanumeric characters using regex
    cleaned_string = re.sub(r'[^a-zA-Z0-9]', '', input_string)
    return cleaned_string.strip()  # Strip leading/trailing spaces (if any)


app = Flask(__name__)
CORS(app)
swagger = Swagger(app)

# Load environment variables from .env file
load_dotenv()

#Define or load API key
API_KEY = os.getenv("API_KEY","your-secret-api-key")

def require_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # Retrieve the API key from the request headers
        api_key = request.headers.get('x-api-key')
        
        # Check if the provided API key matches
        if api_key != API_KEY:
            return jsonify({"error": "Unauthorized access"}), 401  # Unauthorized

        return func(*args, **kwargs)
    
    return decorated_function

@app.route('/test', methods=['GET'])
@require_api_key
@swag_from({
    'responses': {
        200: {
            'description': 'Returns a simple "Hello" message',
            'examples': {
                'application/json': {
                    'message': 'Hello'
                }
            }
        }
    }
})
def hello_world():
    """Test endpoint to check if the API is running."""
    return jsonify({"message": "Hello"})

@app.route('/pay', methods=['POST'])
@require_api_key
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'amount': {'type': 'number'},
                    'description': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Returns the generated PIX payload and QR code path',
            'examples': {
                'application/json': {
                    'message': 'Payment request received',
                    'amount': 150.0,
                    'description': 'description passed by user',
                    'pix': '<PIX code>',
                    'qrcode': 'file name and path, ex:./src/qr_codes/pix_qrcode_20241027_153512.png'
                }
            }
        },
        400: {
            'description': "Missing 'amount' or 'description'."
        }
    }
})
def pay_with_qr():
    """Generates a PIX QR code and copy-paste code for payment."""
    try:
        data = request.get_json()
        amount = data.get('amount')
        description = data.get('description')
        pix_key = data.get('pixkey')

        if not amount or not description:
            return jsonify({"error": "Missing 'amount' or 'description'"}), 400

        pix = generate_pix_qrcode(
            pix_key=pix_key,
            merchant_name="SkipCreative",
            merchant_city="Aracaju/SE",
            amount=amount,
            description=clean_string(description),
            expiration_minutes=5
        )

        return jsonify({
            "message": "Payment request received",
            "amount": amount,
            "description": description,
            "pix": pix[0],
            "qrcode": pix[1]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
