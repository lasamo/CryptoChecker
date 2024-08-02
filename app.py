from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for session management

@app.route('/')
def index():
    if 'api_key' not in session:
        return redirect(url_for('setup'))
    return render_template('index.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        session['api_key'] = request.form['api_key']
        print("METHOD WAS POST, API KEY IS : {}".format(session['api_key']))
        return redirect(url_for('index'))
    return render_template('setup.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'api_key' not in session:
        return redirect(url_for('setup'))

    api_key = session['api_key']
    address = request.form.get('address', '')
    
    # Placeholder for your API request
    # Replace this with your actual API call
    try:
        response = requests.get('https://public.chainalysis.com/api/v1/address/{}'.format(address), headers={'X-API-KEY': f'{api_key}'})
        response.raise_for_status()
        data = response.json()
        # Add address or other relevant data to the response
        return render_template('index.html', data=data, address=address)
    except requests.RequestException as e:
        return render_template('index.html', error="Error fetching data: " + str(e))

if __name__ == "__main__":
    app.run(debug=True)
