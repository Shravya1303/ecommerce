from flask import Flask,render_template,request,flash,url_for,session,redirect
from otp_generator import genotp
from cmail import sendmail
import mysql.connector
import os
import razorpay
from http import client
from itemid import itemidotp

mydb=mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='ecommerce'
)

app=Flask(__name__)
app.secret_key='hvbaiuskhfirf'

@app.route('/',methods=['GET','POST'])
def home():
    return render_template('homepage.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=="POST":
        username=request.form['username']
        mobile=request.form['mobile']
        email=request.form['email']
        address=request.form['address']
        password=request.form['password']
        cursor=mydb.cursor()
        cursor.execute('select email from signup')
        data=cursor.fetchall()
        cursor.execute('select mobile from signup')
        edata=cursor.fetchall()
        if (mobile,) in edata:
            flash("User already exists")
            return render_template('register.html')
        if (email,) in data:
            flash("Email address already exists")
            return render_template('register.html')
        cursor.close()
        otp=genotp()
        subject='thanks for registering to the application'
        body=f'use this otp to register {otp}'
        sendmail(email,subject,body)
        return render_template('otp.html',otp=otp,username=username,mobile=mobile,email=email,address=address,password=password)
    else:
        return render_template('register.html')

@app.route('/otp/<otp>/<username>/<mobile>/<email>/<address>/<password>',methods=['GET','POST'])
def otp(otp,username,mobile,email,address,password):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            lst=[username,mobile,email,address,password]
            query='insert into signup values(%s,%s,%s,%s,%s)'
            cursor=mydb.cursor()
            cursor.execute(query,lst)
            mydb.commit()
            cursor.close()
            flash('User registered')
            return render_template('login.html')
        else:
            flash("Wrong otp")
            return render_template('otp.html',otp=otp,username=username,mobile=mobile,email=email,address=address,password=password)
    # render_template('otp.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        username=request.form['username']
        password=request.form['password']
        print(username)
        print(password)
        cursor=mydb.cursor()
        cursor.execute('select count(*) from signup where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        print(count)
        if count==0:
            flash("Invalid email or password")
            return render_template('login.html')
        else:
            session['user']=username
            if not session.get(username):
                session[username]={}
            return redirect(url_for('additem'))
    return render_template('login.html')

# @app.route('/dashboard',methods=['GET','POST'])
# def dashboard():
#     return render_template('dashboard.html')

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        flash("Already logged out!")
        return redirect(url_for('login'))
    
@app.route('/adminreg',methods=['GET','POST'])
def adminreg():
    if request.method == "POST":
        username=request.form['name']
        mobile=request.form['mob']
        email=request.form['mail']
        password=request.form['pswd']
        cursor = mydb.cursor()
        cursor.execute('INSERT INTO admindata(name, phone, mail, passcode) VALUES (%s, %s, %s, %s)',(username,mobile,email,password))
        mydb.commit()
        cursor.close()
        return redirect(url_for('adminlogin'))
    return render_template('adminregister.html')

@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if request.method == 'POST':
        email=request.form['mail']
        password=request.form['pswd']
        print(email)
        print(password)
        cursor=mydb.cursor()
        cursor.execute('select count(*) from admindata where mail=%s and passcode=%s',[email,password])
        count=cursor.fetchone()
        print(count)
        if count==0:
            flash("Invalid email or password")
            return render_template('adminlogin.html')
        else:
            session['mail']=email
            if not session.get(email):
                session[email]={}
            return redirect(url_for('admindashboard'))
    return render_template('adminlogin.html')

@app.route('/admindashboard',methods=['GET','POST'])
def admindashboard():
    return render_template('admindashboard.html')

@app.route('/adminlogout')
def adminlogout():
    if session.get('mail'):
        session.pop('mail')
        return redirect(url_for('home'))
    else:
        flash("Already logged out!")
        return redirect(url_for('adminlogin'))

@app.route('/additems',methods=['GET','POST'])
def additem():
    if request.method=="POST":
        name=request.form['itemname']
        description=request.form['description']
        quantity=request.form['quantity']
        category=request.form['category']
        price=request.form['price']
        image=request.files['image']
        valid_categories=['electronics','fashion','groceries','home']
        if category not in valid_categories:
            flash("invalid category")
            return render_template('items.html')
        cursor=mydb.cursor()
        idotp=itemidotp()
        filename=idotp+'.jpg'
        cursor.execute('insert into additems(itemid,name,description,qty,category,price)values(%s,%s,%s,%s,%s,%s)',[idotp,name,description,quantity,category,price])
        mydb.commit()
        path=os.path.dirname(os.path.abspath(__file__))
        static_path=os.path.join(path,'static')
        image.save(os.path.join(static_path,filename))
        flash("Item added successfully!")
    return render_template('items.html')

@app.route('/dashboardpage')
def itemdashboard():
    cursor=mydb.cursor()
    cursor.execute('select * from additems')
    items=cursor.fetchall()
    print(items)
    return render_template('itemdashboard.html',items=items)

@app.route('/status')
def status():
    cursor=mydb.cursor()
    cursor.execute('select * from additems')
    items=cursor.fetchall()
    return render_template('status.html',items=items)

@app.route("/updateproducts/<itemid>",methods=['GET','POST'])
def updateproducts(itemid):
    print(itemid)
    cursor=mydb.cursor()
    cursor.execute('select name,description,qty,category,price from additems where itemid=%s',[itemid])
    items=cursor.fetchone()
    print(items)
    cursor.close()
    if request.method=="POST":
        name=request.form['name']
        description=request.form['desc']
        quantity=request.form['qty']
        category=request.form['category']
        price=request.form['price']
        cursor=mydb.cursor()
        cursor.execute('update additems set name=%s,description=%s,qty=%s,category=%s,price=%s where itemid=%s',[name,description,quantity,category,price,itemid])
        mydb.commit()
        cursor.close()
    return render_template('updateproducts.html',items=items)

@app.route('/deleteproducts/<itemid>',methods=['GET','POST'])
def deleteproducts(itemid):
    cursor=mydb.cursor()
    cursor.execute('delete from additems where itemid=%s',[itemid])
    mydb.commit()
    cursor.close()
    path=os.path.dirname(os.path.abspath(__file__))
    static_path=os.path.join(path,'static')
    filename=itemid+'.jpg'
    os.remove(os.path.join(static_path,filename))
    flash("Deleted")
    return redirect(url_for('status'))

# @app.route('/cart/<itemid>/<name>/<int:price>',methods=['GET','POST'])
# def cart(itemid,name,price):
#     if session.get('user'):
#         if request.method=='POST':
#             qty=int(request.form['qty'])
#             if itemid not in session[session.get('user')]:
#                 session[session.get('user')][itemid]=[name,qty,price]
#                 session.modified=True
#                 flash(f'{name} added to cart')
#                 return redirect(url_for('viewcart'))
#             session[session.get('user')][itemid][1]+=qty
#             session.modified=True
#             flash('Item already in cart. Quantity increased to +{qty}')
#     return redirect(url_for('login'))

# @app.route('/viewcart')
# def viewcart():
#     if not session.get('user'):
#         return redirect(url_for('login'))
#     items=session.get(session.get('user')) if session.get(session.get('user')) else 'empty'
#     if items=='empty':
#         return 'No products in cart'
#     return render_template('cart.html',items=items)

@app.route('/display/<itemid>')
def display(itemid):
    cursor=mydb.cursor()
    cursor.execute('select * from additems where itemid=%s',[itemid])
    items=cursor.fetchone()
    return render_template('display.html',items=items)

@app.route('/index')
def index():
    cursor = mydb.cursor(buffered=True)
    # Fetching item details from the database
    cursor.execute('SELECT itemid, name, qty, category, price FROM additems')
    item_data = cursor.fetchall()
    print(item_data)  # Debugging to verify data
    return render_template('index.html', item_data=item_data)

@app.route('/addcart/<itemid>/<name>/<category>/<price>/<quantity>',methods=['GET','POST'])
def addcart(itemid,name,category,price,quantity):
    if not session.get('user'):
        return redirect(url_for('login')) 
    else:
        print(session)
        if itemid not in session.get(session['user'],{}):
            if session.get(session['user']) is None:
                session[session['user']]={}
            session[session['user']][itemid]=[name,price,1,f'{itemid}.jpg',category]
            #print(session)
            session.modified=True
            flash(f'{name} added to cart')
            # return redirect(url_for('index'))
            return "Added to cart."
        session[session['user']][itemid][2]+=1
        session.modified=True
        flash(f'{name} quantity increased in the cart')
        return 'quantity increased in the cart'          
            
@app.route('/viewcart')
def viewcart():
    if not session.get('user'):
        return redirect(url_for('login'))
    #print(session)
    user_cart=session.get(session.get('user'))
    if not user_cart:
        print(user_cart)
        items='empty'
    else:
        print(user_cart)
        items=user_cart
    if items=="empty":
        return 'your cart is empty'
    return render_template('cart.html',items=items)

@app.route('/pay/<itemid>/<name>/<price>',methods=['GET','POST'])
def pay(itemid,name,price):
    try:
        quantity=int(request.form['quantity'])
        amount=price*100
        total_price=amount*quantity
        print("creating the total amount in paisa (price is in rupees)")
        order = client.order.create({ 
            'amount':total_price,
            'currency':'INR',
            'payment':'1'
        })
        print(f"order created:{order}")
        return render_template('pay.html',order=order,itemid=itemid,name=name,price=total_price,quantity=quantity)
    except Exception as e:
        print(f"error creating order: {str(0)}")
        return str(0),400
    
@app.route('/success',methods=['POST'])
def success():
    payment_id=request.form('razorpay_payment_id')
    order_id=request.form('razorpay_order_id')
    signature=request.form('razorpay_signature')
    name=request.form('name')
    itemid=request.form('itemid') 
    total_price=request.form('total_price')
    quantity=request.form('quantity')
    
    params_dict={
        'razorpay_payment_id'
        'razorpay_order_id'
        'razorpay_signature'
    }  
    try:
        client.utility.verify_payments_signature(params_dict)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into orders(itemid,item_name,total_price,user,quantity)values(%s,%s,%s,%s,%s)',[itemid,name,total_price,session.get('user'),quantity])
        mydb.commit()
        cursor.close()
        flash('orders placed successfully')
        return 'orders'
    except razorpay.errors.SignatureVerificationError:
        return 'payments verification failed',400
    
@app.route('/orders')
def orders():
    if session.get('user'):
        user=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from orders where user=%s',[user])
        data=cursor.fetchall()
        cursor.close()
        return render_template('orderdisplay.html',data=data)
    else:
        return redirect(url_for('login'))

app.run(debug=True)