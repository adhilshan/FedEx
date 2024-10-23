from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client

app = Flask(_name_)

account_sid = 'YOUR_ACCOUNT_SID'
auth_token = 'YOUR_AUTH_TOKEN'
client = Client(account_sid, auth_token)

predefined_message = 'Hello! This is an automated call. Please press 1 to connect to customer care. Press 0 to repeat the message.'

@app.route('/make-call', methods=['POST'])
def make_call():
    to = request.form['to']
    from_number = 'YOUR_TWILIO_NUMBER'  # Twilio number

    try:
        call = client.calls.create(
            url='https://your-domain.com/voice-response',  # URL to handle call flow
            to=to,
            from_=from_number
        )
        print(f'Call initiated: {call.sid}')
        return {'message': 'Call is being placed', 'call_sid': call.sid}, 200
    except Exception as e:
        print(f'Error: {e}')
        return {'message': 'Error making call', 'error': str(e)}, 500

@app.route('/voice-response', methods=['POST'])
def voice_response():
    response = VoiceResponse()

    # Gather input (keypress) with a 10-second timeout
    gather = Gather(num_digits=1, action='/gather-response', method='POST', timeout=10)
    gather.say(predefined_message)
    response.append(gather)

    # If no input is received within the timeout, hang up the call
    response.say('No input received. Goodbye.')
    response.hangup()

    return str(response)

@app.route('/gather-response', methods=['POST'])
def gather_response():
    digits = request.form.get('Digits')
    response = VoiceResponse()

    if digits == '1':
        # Forward the call to customer care
        response.dial('+CUSTOMER_CARE_NUMBER')
    elif digits == '0':
        # Repeat the message by redirecting to the original route
        response.redirect('/voice-response')
    else:
        # If an invalid key is pressed, say goodbye and hang up
        response.say('Invalid input. Goodbye.')
        response.hangup()

    return str(response)

if _name_ == '_main_':
    app.run(port=3000)