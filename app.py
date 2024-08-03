from flask import Flask, render_template, request, redirect, url_for, session
import requests
import json

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
        return redirect(url_for('index'))
    return render_template('setup.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'api_key' not in session:
        return redirect(url_for('setup'))

    api_key = session['api_key']
    addresses = request.form.get('address', '')
    address_list = [address.strip() for address in addresses.split(',')]

    results = []
    for address in address_list:
        try:
            response = requests.get(f'https://public.chainalysis.com/api/v1/address/{address}', headers={'X-API-KEY': api_key})
            response.raise_for_status()
            data = response.json()["identifications"]
            if data:
                for entry in data:
                    if entry["category"] == "sanctions":
                        results.append({
                            'address': address,
                            'name': entry["name"],
                            'description': entry["description"],
                            'url': entry.get("url", ""),
                            'raw': entry
                        })
        except requests.RequestException as e:
            results.append({'address': address, 'error': f"Error fetching data: {str(e)}"})

    return render_template('index.html', results=results)

if __name__ == "__main__":
    app.run(debug=True)
