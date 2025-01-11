from flask import Flask, render_template, redirect, url_for, session, request, jsonify
import paypalrestsdk
import stripe
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')  # Manejo seguro de la clave secreta

# Configuración de PayPal
paypalrestsdk.configure({
    "mode": os.getenv('PAYPAL_MODE', "sandbox"),  # Cambiar a "live" en producción
    "client_id": os.getenv('PAYPAL_CLIENT_ID', ""),
    "client_secret": os.getenv('PAYPAL_CLIENT_SECRET', "")
})

# Configuración de Stripe
stripe.api_key = os.getenv('STRIPE_API_KEY', "")  # Manejo seguro de la clave secreta de Stripe

# Datos de ejemplo de productos
PRODUCTS = [
    {"id": 1, "name": "Producto 1", "price": 10.00, "image": "producto1.jpg", "description": "Descripción del producto 1."},
    {"id": 2, "name": "Producto 2", "price": 15.00, "image": "producto2.jpg", "description": "Descripción del producto 2."},
    {"id": 3, "name": "Producto 3", "price": 20.00, "image": "producto3.jpg", "description": "Descripción del producto 3."},
]

def initialize_cart():
    if 'cart' not in session:
        session['cart'] = []

def calculate_cart_total():
    return sum(item['price'] * item['quantity'] for item in session['cart'])

def find_product_by_id(product_id):
    return next((p for p in PRODUCTS if p['id'] == product_id), None)

@app.route('/')
def home():
    initialize_cart()
    return render_template('index.html', products=PRODUCTS)

@app.route('/add-to-cart-ajax/<int:product_id>', methods=['POST'])
def add_to_cart_ajax(product_id):
    initialize_cart()

    product = find_product_by_id(product_id)
    if product:
        data = request.get_json()
        quantity = data.get('quantity', 1)

        for item in session['cart']:
            if item['id'] == product_id:
                item['quantity'] += quantity
                break
        else:
            session['cart'].append({
                "id": product['id'],
                "name": product['name'],
                "price": product['price'],
                "quantity": quantity
            })
        session.modified = True
        cart_count = sum(item['quantity'] for item in session['cart'])
        return jsonify({"message": "Producto actualizado en el carrito", "cart_count": cart_count})
    return jsonify({"error": "Producto no encontrado"}), 404

@app.route('/cart')
def cart():
    initialize_cart()
    total = calculate_cart_total()
    return render_template('cart.html', cart=session['cart'], total=total)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    initialize_cart()
    product = find_product_by_id(product_id)
    if not product:
        return "Producto no encontrado", 404
    cart = session['cart']
    cart_count = sum(item['quantity'] for item in cart)
    return render_template('product_detail.html', product=product, cart=cart, cart_count=cart_count)

@app.route('/clear-cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('home'))

@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    initialize_cart()
    data = request.get_json()
    quantity = data.get('quantity', 1)

    for item in session['cart']:
        if item['id'] == product_id:
            item['quantity'] = max(1, quantity)  # Asegurar que la cantidad sea al menos 1
            break

    session.modified = True
    return jsonify({"success": True})

@app.route('/checkout')
def checkout():
    initialize_cart()
    if not session['cart']:
        return redirect(url_for('home'))
    total = calculate_cart_total()
    return render_template('checkout.html', total=total)

@app.route('/pay-with-paypal', methods=['POST'])
def pay_with_paypal():
    total = calculate_cart_total()
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": url_for('payment_success', _external=True),
            "cancel_url": url_for('payment_cancel', _external=True)
        },
        "transactions": [{
            "amount": {
                "total": f"{total:.2f}",
                "currency": "USD"
            },
            "description": "Compra en YOUR BEST STYLE"
        }]
    })

    try:
        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
    except Exception as e:
        return f"Error al crear el pago con PayPal: {str(e)}"

    return "Error al crear el pago con PayPal"

@app.route('/pay-with-card', methods=['POST'])
def pay_with_card():
    return render_template('credit_card_form.html')

@app.route('/complete-payment', methods=['POST'])
def complete_payment():
    card_number = request.form['card_number']
    expiration_date = request.form['expiration_date']
    cvv = request.form['cvv']
    total = int(calculate_cart_total() * 100)  # Convertir a centavos

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=total,
            currency="usd",
            payment_method_data={
                "type": "card",
                "card": {
                    "number": card_number,
                    "exp_month": int(expiration_date.split('/')[0]),
                    "exp_year": int(expiration_date.split('/')[1]),
                    "cvc": cvv,
                },
            },
            confirm=True,
        )
        session.pop('cart', None)  # Limpiar el carrito después del pago
        return "¡Pago completado con éxito!"
    except stripe.error.CardError as e:
        return f"Error al procesar el pago: {e.user_message}"

@app.route('/payment-success')
def payment_success():
    session.pop('cart', None)  # Limpiar el carrito después del pago
    return "¡Pago completado con éxito!"

@app.route('/payment-cancel')
def payment_cancel():
    return "El pago fue cancelado."

if __name__ == '__main__':
    app.run(debug=True)
