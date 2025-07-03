from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# AWS Configuration
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
user_table = dynamodb.Table('Users')
orders_table = dynamodb.Table('Orders')

# Email Configuration
EMAIL_ADDRESS = 'laharikessamsetty@gmail.com'
EMAIL_PASSWORD = 'iyxh zneg oyog tyui'  # Replace with your actual Gmail App Password

veg_items = [
    {"name": "Mango Pickle", "price": 150, "img": "mango-pickle.jpg"},
    {"name": "Lemon Pickle", "price": 120, "img": "lemon-pickle.jpg"},
    {"name": "Tomato Pickle", "price": 180, "img": "tomato-pickle.jpg"},
    {"name": "Gongura Pickle", "price": 160, "img": "gongura-pickle.jpg"},
]

non_veg_items = [
    {"name": "Chicken Pickle", "price": 300, "img": "chicken-pickle.jpg"},
    {"name": "Mutton Pickle", "price": 350, "img": "mutton-pickle.jpg"},
    {"name": "Fish Pickle", "price": 320, "img": "fish-pickle.jpg"},
    {"name": "Prawn Pickle", "price": 340, "img": "prawn-pickle.jpg"},
]

snack_items = [
    {"name": "Snack Combo", "price": 200, "img": "snacks-combo.jpg"},
    {"name": "Murukku", "price": 100, "img": "murukku.jpg"},
    {"name": "Mixture", "price": 120, "img": "mixture.jpg"},
    {"name": "Chakli", "price": 130, "img": "chakli.jpg"},
]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/veg-pickles')
def veg_pickles():
    return render_template('veg_pickles.html', items=veg_items)

@app.route('/non-veg-pickles')
def non_veg_pickles():
    return render_template('non_veg_pickles.html', items=non_veg_items)

@app.route('/snacks')
def snacks():
    return render_template('snacks.html', items=snack_items)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item = request.form.to_dict()
    cart = session.get('cart', [])
    cart.append(item)
    session['cart'] = cart
    return redirect(request.referrer)

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    index = int(request.form['index'])
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(int(i['price']) for i in cart_items)
    return render_template('cart.html', cart=cart_items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['fullname']
        email = request.form['email']
        address = request.form['address']
        phone = request.form['phone']
        payment = request.form['payment']
        cart_items = session.get('cart', [])
        total = sum(int(i['price']) for i in cart_items)
        order_id = str(uuid.uuid4())

        orders_table.put_item(Item={
            'order_id': order_id,
            'name': name,
            'email': email,
            'address': address,
            'phone': phone,
            'payment': payment,
            'total': total,
            'items': cart_items
        })

        send_email(email, "Order Confirmation", f"Thank you {name} for your order! Total: ₹{total}")

        session.pop('cart', None)
        return render_template('success.html', name=name, order_id=order_id)

    return render_template('checkout.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        return redirect(url_for('success'))
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = user_table.get_item(Key={'email': email}).get('Item')
        if user and user['password'] == password:
            session['user'] = email
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_table.put_item(Item={'email': email, 'password': password})
        send_email(email, "Welcome to Pickle Paradise", "Thank you for signing up!")
        flash("Signup successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# Email Sending Function
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == '__main__':
 app.run(debug=True, host='0.0.0.0', port=5001)
