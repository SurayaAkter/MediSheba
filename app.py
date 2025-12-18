import os
import pymysql
pymysql.install_as_MySQLdb()

import pathlib

import requests
from flask import Flask, session, abort, redirect, request, render_template, url_for
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from google.auth.transport import requests
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, text, or_
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from sslcommerz_lib import SSLCOMMERZ 

# from flask_ngrok import run_with_ngrok
from abc import ABC, abstractmethod 

app = Flask("MediSheba")
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql://root:@localhost/medisheba'
db = SQLAlchemy(app)
app.secret_key = "medisheba.com"

# run_with_ngrok(app)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "853888832125-llhj81iuaold01co7k1b24bb6qrs46r1.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
    # redirect_uri="https://555e-118-179-194-148.ngrok-free.app/callback"
)

# settings = { 'store_id': 'north651ad2fdce573', 'store_pass': 'north651ad2fdce573@ssl', 'issandbox': True }
# sslcz = SSLCOMMERZ(settings)

# Your payment gateway configuration settings
gateway_settings = {
    'store_id': 'north651ad2fdce573',
    'store_pass': 'north651ad2fdce573@ssl',
    'issandbox': True
}





#db models
# class User(db.Model):
#     UserID = db.Column(db.Integer, primary_key=True)
#     Username = db.Column(db.String(255), nullable=False)
#     Email = db.Column(db.String(255), nullable=False)
#     Address = db.Column(db.String(255), nullable=True)
#     PhoneNumber = db.Column(db.String(15), nullable=True)

class User(db.Model):
    UserID = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    Address = db.Column(db.String(255), nullable=True)
    PhoneNumber = db.Column(db.String(15), nullable=True)
    user_type = db.Column(
        db.Enum('admin', 'user', name='user_type'),
        nullable=False,
        default='user'
    )

class Product_info(db.Model):
    productID = db.Column(db.Integer, primary_key=True)
    Manufacturer = db.Column(db.String(47), nullable=True)
    BrandName = db.Column(db.String(38), nullable=True)
    GenericName = db.Column(db.String(393), nullable=True)
    Strength = db.Column(db.String(265), nullable=True)
    Description = db.Column(db.String(26), nullable=True)
    Price = db.Column(db.String(72), nullable=True)

class Cart(db.Model):
    __tablename__ = 'cart'

    CartID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, ForeignKey('user.UserID'), nullable=False) 
    ProductID = db.Column(db.Integer, ForeignKey('product_info.productID'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)

    # Define relationship with Product_info
    product = relationship('Product_info', backref='cart_items')

class History(db.Model):
    HistoryID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('user.UserID'), nullable=False)
    ProductID = db.Column(db.Integer, db.ForeignKey('product_info.productID'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    Timestamp = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Define relationships
    user = db.relationship('User', backref=db.backref('history_entries', lazy=True))
    product = db.relationship('Product_info', backref=db.backref('history_entries', lazy=True))

class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)



class DoctorInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(255), nullable=False)
    speciality = db.Column(db.String(255), nullable=False)
    Gender = db.Column(db.Enum('male', 'female'), nullable=False)
    Experience = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)



class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.UserID'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_info.id'), nullable=False)

    user = db.relationship('User', foreign_keys=[user_id])
    doctor = db.relationship('DoctorInfo', foreign_keys=[doctor_id])   




# factory pattern begin
# Define an abstract UserFactory class
class UserFactory(ABC):
    @abstractmethod
    def create_user(self, username, password, user_type):
        pass

# Concrete UserFactory for regular users
class RegularUserFactory(UserFactory):
    def create_user(self, username, password, user_type):
        return RegularUser(username, password, user_type)

# Concrete UserFactory for admin users
class AdminUserFactory(UserFactory):
    def create_user(self, username, password, user_type):
        return AdminUser(username, password, user_type)


# Define a common User interface
class User_(ABC):
    def __init__(self, username, password, user_type):
        self.username = username
        self.password = password
        self.user_type = user_type

    @abstractmethod
    def __str__(self):
        pass

# Concrete RegularUser class
class RegularUser(User_):
    def __str__(self):
        return f"Regular User: {self.username}"

# Concrete AdminUser class
class AdminUser(User_):
    def __str__(self):
        return f"Admin User: {self.username}"

#factory pattern end 





#paymentstrategy pattern begin
class PaymentStrategy:
    def pay(self, amount):
        pass

class CreditCardPaymentStrategy(PaymentStrategy):
    def __init__(self, credit_card_number, expiration_date):
        self.credit_card_number = credit_card_number
        self.expiration_date = expiration_date
        self.payment_info = None

    def pay(self, amount):
        payment_info = f"Paying {amount} with credit card {self.credit_card_number}"
        self.payment_info = payment_info

class PayPalPaymentStrategy(PaymentStrategy):
    def __init__(self, email_address):
        self.email_address = email_address
        self.payment_info = None

    def pay(self, amount):
        payment_info = f"Paying {amount} with PayPal {self.email_address}"
        self.payment_info = payment_info

class Order:
    def __init__(self, total_amount):
        self.total_amount = total_amount
        self.payment_strategy = None

    def set_payment_strategy(self, payment_strategy):
        self.payment_strategy = payment_strategy

    def pay(self):
        self.payment_strategy.pay(self.total_amount)

#Paymentstrategy end



#singleton design pattern begin
class PaymentGatewayConfig:
    
    _instance = None
    def __new__(cls, settings):
        if cls._instance is None:
            cls._instance = super(PaymentGatewayConfig, cls).__new__(cls)
            cls._instance.init_config(settings)
        return cls._instance

    def init_config(self, settings):
        # Initialize payment gateway configuration using the provided settings
        self.sslcz = SSLCOMMERZ(settings)

    def get_sslcz_instance(self):
        return self.sslcz
    
    #singleton design pattern end



# Methods

# decorator design pattern to check if the user is logged in
def login_is_required(function):
    def decorated_function(*args, **kwargs):
       # if "google_id" not in session:
        if session['email']:
            return function()     
        else:
            return abort(401)  # Authorization required

    return decorated_function



@app.route("/signin")
def signin():
    # authorization_url, state = flow.authorization_url()
    # session["state"] = state
    # return redirect(authorization_url)
    return render_template('login.html')

@app.route("/To_Signup")
def To_Signup():
    
    return render_template('signup.html')



@app.route("/To_Login")
def To_Login():
    
    return render_template('login.html')

@app.route("/Diagnosis")
def Diagnosis():
    return render_template(
        "diagnosis.html",
        search_results=[],          
        user_appointments=[],
        email=session.get("email"),
        user_type=session.get("user_type")
    )


@app.route("/Admin_Dashboard")
def Admin_Dashboard():
    # Query the user data from your database
    users = User.query.all()  # Assuming User is the model for your user table

    return render_template('admin.html', email=session["email"], user_type=session['user_type'], users=users)




@app.route('/remove_user/<int:user_id>')
def remove_user(user_id):
    user = User.query.get(user_id)
    if user and user.user_type != 'admin':
        # Get the user's related appointments
        appointments = Appointment.query.filter_by(user_id=user.UserID).all()

        # Delete related appointments
        for appointment in appointments:
            db.session.delete(appointment)

        # Delete related cart records
        Cart.query.filter_by(UserID=user.UserID).delete()

        # Delete related history records (assuming the history table name is 'history')
        History.query.filter_by(UserID=user.UserID).delete()

        # Delete the user
        db.session.delete(user)
        db.session.commit()

    return redirect('/Admin_Dashboard')


#edit user_type
@app.route('/edit_user_type/<int:user_id>')
def edit_user_type(user_id):
    user = User.query.get(user_id)
    if user and user.user_type != 'admin':
        # Toggle user type
        user.user_type = 'admin' if user.user_type == 'user' else 'user'
        db.session.commit()
    return redirect('/Admin_Dashboard')



# @app.route("/Diagnosis_Search")
# def Diagnosis_Search():
    
#     return render_template('search.html', email = session["email"],user_type=session['user_type'])

# @app.route("/Diagnosis_Search", methods=['GET'])
# def Diagnosis_Search():
#     # Retrieve search criteria from the request
#     speciality = request.args.get("speciality")
#     name = request.args.get("name")
#     availability = request.args.get("availability")

#     # Perform the search based on the provided criteria
#     doctors = DoctorInfo.query

#     if speciality:
#         doctors = doctors.filter(DoctorInfo.speciality == speciality)

#     if name:
#         doctors = doctors.filter(DoctorInfo.Name == name)

#     if availability:
#         doctors = doctors.filter(DoctorInfo.Gender == availability)

#     # Execute the query and get the results
#     search_results = doctors.all()

#     # Render the search results in the search.html template
#     return render_template('search.html', search_results=search_results, email = session["email"],user_type=session['user_type'])
@app.route("/Diagnosis_Search", methods=["GET"])
def Diagnosis_Search():
    speciality = request.args.get("speciality")
    name = request.args.get("name")
    availability = request.args.get("availability")

    doctors = DoctorInfo.query

    if speciality:
        doctors = doctors.filter(
            DoctorInfo.speciality.ilike(f"%{speciality}%")
        )

    if name:
        doctors = doctors.filter(
            DoctorInfo.Name.ilike(f"%{name}%")
        )

    if availability:
        doctors = doctors.filter(
            DoctorInfo.Gender == availability
        )

    search_results = doctors.all()

    user_id = session.get("user_id")
    user_appointments = []

    if user_id:
        user_appointments = [
            a.doctor_id
            for a in Appointment.query.filter_by(user_id=user_id).all()
        ]


    return render_template(
        "diagnosis.html",
        search_results=search_results,
        user_appointments=user_appointments,
        email=session.get("email"),
        user_type=session.get("user_type")
    )



#Remove appointment


@app.route('/remove_appointment/<int:doctor_id>', methods=['GET', 'POST'])
def remove_appointment(doctor_id):
    # Assuming you have a way to get the logged-in user's ID
    user_id = session["user_id"]

    # Find the appointment and remove it from the database
    appointment = Appointment.query.filter_by(user_id=user_id, doctor_id=doctor_id).first()
    if appointment:
        db.session.delete(appointment)
        db.session.commit()

    # Redirect to a confirmation page or any other desired action
    return render_template('appointment_remove.html', email=session["email"], user_type=session['user_type'])


# Sign up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
  if request.method == 'GET':
    return render_template('signup.html')
  else:
    email = request.form['email']
    password = request.form['password']

    # Check if the user already exists
    user = User.query.filter_by(email=email).first()
    if user:
      return render_template('signup.html', error='User already exists')

    # Create a new user account
    new_user = User(email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    # Redirect the user to the login page
    return redirect('/login')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']  # Get the selected user type from the form

        # Check the user's credentials
        user = User.query.filter_by(email=email).first()
        if user is None:
            return render_template('login.html', error='User does not exist')
        if user.password != password:
            return render_template('login.html', error='Incorrect password')

        # Create a user instance based on the user_type
        # switch design pattern 
        if user_type == "user":
            user_factory = RegularUserFactory()
        elif user_type == "admin":
            user_factory = AdminUserFactory()
        else:
            return render_template('login.html', error='Invalid user type')
        
        # switch dp end


        # Create the appropriate user instance
        authenticated_user = user_factory.create_user(user.email, user.password, user_type)
        # Check if user_type from the form matches the user_type in the database
        if authenticated_user.user_type != user.user_type:
            return render_template('login.html', error='Invalid user type')

        # Continue with session handling and rendering
        session["user_id"]=user.UserID
        session['email'] = user.email
        session['user_type'] = user_type  # Store the user type in the session
        print(authenticated_user)
        # return render_template('home.html', email=session['email'], user_type=session['user_type'])
        return redirect("/protected_area")

# @app.route("/login")
# def login():
#     # authorization_url, state = flow.authorization_url()
#     # session["state"] = state
#     # return redirect(authorization_url)

# @app.route("/callback")
# def callback():
#     flow.fetch_token(authorization_response=request.url)

#     if not session["state"] == request.args["state"]:
#         abort(500)  # State does not match!

#     credentials = flow.credentials
#     request_session = requests.session()
#     cached_session = cachecontrol.CacheControl(request_session)
#     token_request = google.auth.transport.requests.Request(session=cached_session)

#     id_info = id_token.verify_oauth2_token(
#         id_token=credentials._id_token,
#         request=token_request,
#         audience=GOOGLE_CLIENT_ID
#     )

#     session["google_id"] = id_info.get("sub")
#     session["name"] = id_info.get("name")
#     session["email"] = id_info.get("email") 
#     session["picture"] = id_info.get("picture")


#     first_name = session["name"].split()[0]
#     session["first_name"] = first_name

#     # Check if a user with a specific email exists
#     email_exists = db.session.query(User).filter(User.Email == session["email"]).count() > 0

#     if email_exists == 0:
#         # Create a new user and add it to the database
#         new_user = User(Username=session["name"], Email=session["email"])
#         db.session.add(new_user)
#         db.session.commit()

#     return redirect("/protected_area")

@app.route("/logout")
def logout():
     # session.clear()
    session.pop('email',None)
    return redirect("/")

@app.route("/")
def index():
     # session.clear()
    session.pop('email',None)
    return render_template('home.html')

@app.route("/shop")
def shop():
    products = Product_info.query.all()
    images = Images.query.join(Product_info, Images.category == Product_info.Description).add_columns(Images.url).all()

    # if "google_id" in session:
    if session.get('email'):
        return render_template('shop.html', email = session["email"], products=products, images=images,user_type=session['user_type'])
    else:
        # session.clear()
        session.pop('email',None)
        return render_template('shop.html', products=products, images=images)

@app.route('/view_product/<int:product_id>')
def view_product(product_id):
    product_detail = Product_info.query.get_or_404(product_id)

    # if "google_id" in session:
    if session.get('email'):
        return render_template('product_details.html', email = session["email"], product=product_detail,user_type=session['user_type'])
    else:
        return render_template('product_details.html', product=product_detail)

@app.route('/search_products', methods=['GET', 'POST'])
def search_products():

    # POST (form submit from shop page)
    if request.method == 'POST':
        search_query = request.form.get('search_query')
    else:
        search_query = request.args.get('q')

    if not search_query:
        return redirect(url_for('shop'))

    products = Product_info.query.filter(
        or_(
            Product_info.Manufacturer.ilike(f"%{search_query}%"),
            Product_info.BrandName.ilike(f"%{search_query}%"),
            Product_info.GenericName.ilike(f"%{search_query}%"),
            Product_info.Strength.ilike(f"%{search_query}%"),
            Product_info.Description.ilike(f"%{search_query}%")
        )
    ).all()

    if session.get('email'):
        return render_template(
            'shop.html',
            products=products,
            email=session.get('email'),
            user_type=session.get('user_type')
        )
    else:
        return render_template('shop.html', products=products)

# if "google_id" in session:
    if session.get('email'):
        # return render_template('shop.html', email = session["name"], products=products)
        return render_template('shop.html', email = session["email"], products=products)

    else:
        # session.clear()
        session.pop('email',None)
        return render_template('shop.html', products=products)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
     # if "google_id" in session:
    if session.get('email'):
        user = User.query.filter_by(email=session["email"]).first()
        user_id = user.UserID
        quantity = int(request.form['quantity'])

        new_cart_item = Cart(ProductID=product_id, Quantity=quantity, UserID=user_id)
        db.session.add(new_cart_item)
        db.session.commit()

        # Retrieve the redirect URL from the request
        redirect_url = request.args.get('redirect_url', '/shop')

        return redirect(redirect_url)
    else:
        return redirect(url_for('login'))
    

    

@app.route('/cart')
def cart():
    # if "google_id" in session:
    if session.get('email'):
        print(session)
        user = User.query.filter_by(email=session["email"]).first()
        user_id = user.UserID
        cart_items = Cart.query.filter_by(UserID=user_id).all()

        total_price = 0

        for item in cart_items:
            item_price = float(item.product.Price)  # Convert to float
            item_quantity = float(item.Quantity)   # Convert to float
            total_price += item_price * item_quantity
            
        formatted_price = "{:.2f}".format(total_price)

        return render_template('cart.html', email = session["email"], cart_items=cart_items, total_price=formatted_price,user_type=session['user_type'])
    else:
        return render_template('cart.html')
    
@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
   # if "google_id" in session:
    if session.get('email'):
        cart_item = Cart.query.get_or_404(cart_id)
        db.session.delete(cart_item)
        db.session.commit()
        return redirect(url_for('cart'))
    else:
        return redirect(url_for('login'))
    
    

#Appointment Booking

@app.route('/appointment_book/<int:doctor_id>', methods=['GET', 'POST'])
def appointment_book(doctor_id):
    # if request.method == 'POST':
        # Assuming you have a way to get the logged-in user's ID
        user_id = session.get("user_id")

        # Create a new appointment record in the database
        appointment = Appointment(user_id=user_id, doctor_id=doctor_id)
        db.session.add(appointment)
        db.session.commit()

        # Redirect to a confirmation page or any other desired action
        # return redirect(url_for('confirmation_page'))

        return render_template('appointment_book.html', email=session["email"], user_type=session['user_type'])





@app.route('/checkout')
def checkout():
    # if "google_id" in session:
    if session.get('email'):
        user = User.query.filter_by(email=session["email"]).first()
        user_id = user.UserID
        cart_items = Cart.query.filter_by(UserID=user_id).all()
        user_address = user.Address
        user_phone = user.PhoneNumber
        if user_phone is not None:
            user_phone = user_phone[4:]

        total_price = 0

        for item in cart_items:
            item_price = float(item.product.Price)  # Convert to float
            item_quantity = float(item.Quantity)   # Convert to float
            total_price += item_price * item_quantity

        formatted_price = "{:.2f}".format(total_price)
        session['formatted_price'] = formatted_price

        return render_template('checkout.html', email = session["email"], cart_items=cart_items, total_price=formatted_price, address = user_address, phone = user_phone,user_type=session['user_type'])
    else:
        return redirect(url_for('login'))


# Create a PaymentGatewayConfig Singleton instance with the settings
payment_gateway_config = PaymentGatewayConfig(gateway_settings)


# @app.route('/order', methods=['GET', 'POST'])
@app.route('/order')

def order():
   # if "google_id" in session:
    if session.get('email'):
        user = User.query.filter_by(email=session["email"]).first()
        user_id = user.UserID
        cart_items = Cart.query.filter_by(UserID=user_id).all()

        total_price = 0

        for item in cart_items:
            item_price = float(item.product.Price)  # Convert to float
            item_quantity = float(item.Quantity)   # Convert to float
            total_price += item_price * item_quantity

        # # Get address and phone number from the form
        # address = request.form.get('address')
        # phone_number = "+880" + str(request.form.get('phone_number'))

        # # Update user's address and phone number
        # user.Address = address
        # user.PhoneNumber = phone_number

        # db.session.commit()
        # # formatted_price = "{:.2f}".format(total_price)

        status_url = request.url_root + url_for('sslc_status')  # Generating the status URL

        post_body = {}
        post_body['total_amount'] = total_price
        post_body['currency'] = "BDT"
        post_body['tran_id'] = "12345"
        post_body['success_url'] = status_url
        post_body['fail_url'] = status_url
        post_body['cancel_url'] = status_url
        post_body['emi_option'] = 0
        post_body['cus_name'] = "Jandu"
        post_body['cus_email'] = session["email"]
        post_body['cus_phone'] = user.PhoneNumber
        post_body['cus_add1'] = user.Address
        post_body['cus_city'] = "Dhaka"
        post_body['cus_country'] = "Bangladesh"
        post_body['shipping_method'] = "NO"
        post_body['multi_card_name'] = ""
        post_body['num_of_item'] = 1
        post_body['product_name'] = "Test"
        post_body['product_category'] = "Test Category"
        post_body['product_profile'] = "general"

 # Access the payment gateway instance from the Singleton
        sslcz = payment_gateway_config.get_sslcz_instance()

        response = sslcz.createSession(post_body) # API response
        print("====================")
        print(response)
        print("====================")
        # Need to redirect user to response['GatewayPageURL']

        # return redirect(url_for('cart'))
        return redirect(response['GatewayPageURL'])

    else:
        return redirect(url_for('login'))


@app.route('/sslc/status', methods=['POST'])
def sslc_status():
    if request.method == 'POST':
        payment_data = request.form

        print("====================")
        print(payment_data)
        print("====================")

        status = payment_data['status']
        if status == 'VALID':
            val_id = payment_data['val_id']
            tran_id = payment_data['tran_id']

            return redirect(url_for('sslc_complete', val_id=val_id, tran_id=tran_id))

    return render_template('status.html')

@app.route('/sslc/complete/<val_id>/<tran_id>')
def sslc_complete(val_id, tran_id):
        user = User.query.filter_by(email=session["email"]).first()
        user_id = user.UserID
        cart_items = Cart.query.filter_by(UserID=user_id).all()

        total_price = 0

        for item in cart_items:
            item_price = float(item.product.Price)  # Convert to float
            item_quantity = float(item.Quantity)   # Convert to float
            total_price += item_price * item_quantity

            new_history_item = History(
                UserID=user_id,
                ProductID=item.ProductID,
                Quantity=item.Quantity,
                Timestamp=datetime.utcnow() + timedelta(hours=6)
            )
            db.session.add(new_history_item)
            db.session.delete(item)  # Remove item from cart

        db.session.commit()
        formatted_price = "{:.2f}".format(total_price)

        return redirect(url_for('cart'))


@app.route('/success')
def success():
    # if "google_id" in session:
    if session.get('email'):

        return render_template('success.html')
    else:
        return redirect(url_for('login'))
    

@app.route('/history')
def history():
    # if "google_id" in session:
    if session.get('email'):
        user = User.query.filter_by(email=session["email"]).first()
        user_id = user.UserID
        history_items = History.query.filter_by(UserID=user_id).all()

        total_price = 0

        for item in history_items:
            item_price = float(item.product.Price)  # Convert to float
            item_quantity = float(item.Quantity)   # Convert to float
            total_price += item_price * item_quantity
            
        formatted_price = "{:.2f}".format(total_price)
        
        return render_template('history.html', email = session["email"],  history_items=history_items, total_price=formatted_price,user_type=session['user_type'])
    else:
        return render_template('history.html')

@app.route('/clear_history')
def clear_history():
     # if "google_id" in session:
    if session.get('email'):
        user = User.query.filter_by(email=session["email"]).first()
        user_id = user.UserID

        History.query.filter_by(UserID=user_id).delete()
        db.session.commit()

        return redirect(url_for('history'))
    else:
        return redirect(url_for('login'))



@app.route("/protected_area")
@login_is_required
def protected_area():
    return render_template('home.html', email = session["email"],user_type=session['user_type']) 

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/faqs")
def faqs():
    return render_template("faqs.html")

@app.route("/shipping")
def shipping():
    return render_template("shipping.html")

@app.route("/returns")
def returns():
    return render_template("returns.html")

#Payment strategy Method begin
@app.route("/payment_option", methods=['GET', 'POST'])
def payment_option():
        user = User.query.filter_by(email=session["email"]).first()
        user_id = user.UserID
    # Get address and phone number from the form
        address = request.form.get('address')
        phone_number = "+880" + str(request.form.get('phone_number'))

        # Update user's address and phone number
        user.Address = address
        user.PhoneNumber = phone_number

        db.session.commit()

        
        
        # formatted_price = "{:.2f}".format(total_price)
        return render_template('payment_option.html')

@app.route("/credit_card")
def credit_card():
    return render_template('credit_card.html')

@app.route("/paypal")
def paypal ():
    return render_template('paypal.html')

@app.route("/paypal_payment", methods=['POST'])
def paypal_payment():
    email = request.form["email"]
    password = request.form["password"]


    # Process the PayPal payment here
    # Set the payment strategy to PayPal
    order.set_payment_strategy(PayPalPaymentStrategy(email))

# Retrieve formatted_price from the session
    formatted_price = session.get('formatted_price')


    # Call the pay method to set payment_info
    order.payment_strategy.pay(formatted_price)
    
    # Get the payment_info from the payment strategy
    payment_info = order.payment_strategy.payment_info

    return render_template("success.html", payment_info=payment_info)


@app.route("/credit_card_payment", methods=['POST'])
def credit_card_payment():
    card_number = request.form["card_number"]
    card_name = request.form["card_name"]
    expiration_date = request.form["expiration_date"]
    cvv = request.form["cvv"]

    # Process the credit card payment here
    # Set the payment strategy to credit card
    order.set_payment_strategy(CreditCardPaymentStrategy(card_number, expiration_date))

# Retrieve formatted_price from the session
    formatted_price = session.get('formatted_price')

    # Call the pay method to set payment_info
    order.payment_strategy.pay(formatted_price)
    
    # Get the payment_info from the payment strategy
    payment_info = order.payment_strategy.payment_info

    return render_template("success.html", payment_info=payment_info)

#Payment strategy Method end
# def total_price():
#         user = User.query.filter_by(email=session["email"]).first()
#         user_id = user.UserID
#         cart_items = Cart.query.filter_by(UserID=user_id).all()
#         total_price = 0

#         for item in cart_items:
#                     item_price = float(item.product.Price)  # Convert to float
#                     item_quantity = float(item.Quantity)   # Convert to float
#                     total_price += item_price * item_quantity

#         formatted_price = "{:.2f}".format(total_price)
#         return formatted_price


if __name__ == "__main__":
    order = Order(100)
    # formatted_price=100.567
    # order_price=total_price()
    # order = Order(order_price)
    app.run(debug=True, host='0.0.0.0')
    # app.run()