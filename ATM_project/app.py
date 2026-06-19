from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)


account = {}

@app.route("/")
def Index():
    return render_template('index.html')


@app.route('/create', methods=['POST'])
def CreateAccount():
    name = request.form['name']
    acc_no = request.form['acc_no']
    balance = int(request.form['balance'])

    account[acc_no] = {
        'name': name,
        'balance': balance
    }

    return redirect(url_for('Dashboard', acc_no=acc_no))


@app.route('/dashboard/<acc_no>')
def Dashboard(acc_no):

    if acc_no not in account:
        return "Account Not Found"

    return render_template(
        'dashboard.html',
        acc_no=acc_no,
        name=account[acc_no]['name'],
        balance=account[acc_no]['balance']
    )


@app.route('/deposit/<acc_no>', methods=['POST'])
def Deposit(acc_no):

    amount = int(request.form['amount'])

    if amount > 0:
        account[acc_no]['balance'] += amount
        return redirect(url_for('Dashboard', acc_no=acc_no))

    return f"Invalid Amount <a href='/dashboard/{acc_no}'>Try Again</a>"


@app.route('/withdraw/<acc_no>', methods=['POST'])
def Withdraw(acc_no):

    amount = int(request.form['amount'])

    if amount > 0 and amount <= account[acc_no]['balance']:
        account[acc_no]['balance'] -= amount
        return redirect(url_for('Dashboard', acc_no=acc_no))

    return f"Insufficient Balance <a href='/dashboard/{acc_no}'>Try Again</a>"


@app.route('/delete/<acc_no>', methods=['POST'])
def DeleteAccount(acc_no):

    del account[acc_no]

    return redirect(url_for('Index'))


if __name__ == "__main__":
    app.run(debug=True)