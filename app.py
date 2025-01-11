from flask import Flask, render_template, redirect, url_for, request, session
import paypalrestsdk

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

# Configuración de PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # Cambia a "live" en producción
    "client_id": "AecI7QKARsB1KWPJdkm8_kL5aYMyo2rHhGHapOkcy45Bgf7msIR5inMCpF6gM3MwRNaHJbCCHk-J2n13",
    "client_secret": "EKjsitEsh19neAi9qYcvDtxo4_L7aerUO17ZSCpuB_XQl33r8yMUb7UjTy5RtaHLC24ZOPbNKeepITMY"
})

# Rutas existentes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/pay-with-paypal', methods=['POST'])
def pay_with_paypal():
    # Configuración del pago en PayPal
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
        # Redirigir al usuario a PayPal
        for link in payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)
    else:
        return "Error al crear el pago con PayPal"

@app.route('/pay-with-card', methods=['POST'])
def pay_with_card():
    # Redirige a una página para que el usuario ingrese los datos de la tarjeta
    return render_template('credit_card_form.html')

@app.route('/payment-success')
def payment_success():
    return "¡Pago completado con éxito!"

@app.route('/payment-cancel')
def payment_cancel():
    return "El pago fue cancelado."

if __name__ == '__main__':
    app.run(debug=True)
