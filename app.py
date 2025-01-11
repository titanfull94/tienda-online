from flask import Flask, render_template, redirect, url_for, session, request
import paypalrestsdk
import stripe

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cambia esto por algo seguro

# Configuración de PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # Cambiar a "live" en producción
    "client_id": "AecI7QKARsB1KWPJdkm8_kL5aYMyo2rHhGHapOkcy45Bgf7msIR5inMCpF6gM3MwRNaHJbCCHk-J2n13",
    "client_secret": "EKjsitEsh19neAi9qYcvDtxo4_L7aerUO17ZSCpuB_XQl33r8yMUb7UjTy5RtaHLC24ZOPbNKeepITMY"
})

# Configuración de Stripe
stripe.api_key = "sk_test_XXXXXXXXXXXXXXXXXXXXXX"  # Cambiar a tu clave secreta de Stripe

# Datos de ejemplo de productos
PRODUCTS = [
    {"id": 1, "name": "Producto 1", "price": 10.00},
    {"id": 2, "name": "Producto 2", "price": 15.00},
    {"id": 3, "name": "Producto 3", "price": 20.00},
]

@app.route('/')
def home():
    if 'cart' not in session:
        session['cart'] = []
    return render_template('index.html', products=PRODUCTS)

@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if product:
        session['cart'].append(product)
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = []
    cart = session['cart']
    total = sum(item['price'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

@app.route('/clear-cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('home'))

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/pay-with-paypal', methods=['POST'])
def pay_with_paypal():
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
                "total": "20.00",  # Monto total (puedes ajustarlo dinámicamente)
                "currency": "USD"
            },
            "description": "Compra en YOUR BEST STYLE"
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)
    else:
        return "Error al crear el pago con PayPal"

@app.route('/pay-with-card', methods=['POST'])
def pay_with_card():
    return render_template('credit_card_form.html')

@app.route('/complete-payment', methods=['POST'])
def complete_payment():
    card_number = request.form['card_number']
    expiration_date = request.form['expiration_date']
    cvv = request.form['cvv']
    card_holder = request.form['card_holder']
    total = 2000  # Total en centavos (ejemplo: $20.00)

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
        return "¡Pago completado con éxito!"
    except stripe.error.CardError as e:
        return f"Error al procesar el pago: {e.user_message}"

@app.route('/payment-success')
def payment_success():
    return "¡Pago completado con éxito!"

@app.route('/payment-cancel')
def payment_cancel():
    return "El pago fue cancelado."

if __name__ == '__main__':
    app.run(debug=True)
