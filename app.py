#app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import ForeignKey, Table, String, Column, DateTime, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List

#Initialize Flask app
app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Kimbalama#32@localhost/Ecommerce API'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Creating our Base Model
class Base(DeclarativeBase):
    pass

#Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class = Base)
db.init_app(app)
ma = Marshmallow(app)

#============Models==========

order_product = Table(      #   ***Association Table***
	"order_product",
	Base.metadata,
	Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
)

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(100))
		
	# One-to-Many relationship: A customer can have many orders
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")

 
 
class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_date: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
		
    # Many-to-One relationship: Each order is related to one customer
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")

    # Many-to-Many relationship: An order can have many products
    products: Mapped[List["Product"]] = relationship("Product", secondary=order_product, back_populates="orders")




class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float)


    # Many-to-Many relationship: A product can appear in many orders
    orders: Mapped[List["Order"]] = relationship("Order", secondary=order_product, back_populates="products")

#===============SCHEMAS===========

# Customer Schema
class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        
# Order Schema
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        
# Product Schema
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
       
       
# Initialize Schemas
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True) #Serialization
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


#===========END POINTS CUSTOMERS =============




def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400  # Return validation error if any
    new_customer = Customer(name=customer_data['name'], address=customer_data['address'], email=customer_data['email'])

    # Add and commit the customer to the database
    db.session.add(new_customer)
    db.session.commit()

    # Return the created customer as JSON
    return customer_schema.jsonify(new_customer), 201


# Get All Customers Route
@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)


# Get One Customer by ID Route
@app.route('/customers/<id>', methods=['GET'])
def get_customer(id):
    customer = Customer.query.get_or_404(id)
    
    return customer_schema.jsonify(customer)


# Update Customer Route
@app.route('/customers/<id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    customer_data = request.json

    # PUT/ UPDATE CUSTOMER INFO
    if 'name' in customer_data:
        customer.name = customer_data['name']
    if 'address' in customer_data:
        customer.address = customer_data['address']
    if 'email' in customer_data:
        customer.email = customer_data['email']
    

    db.session.commit()
    return customer_schema.jsonify(customer)


# Delete Customer Route
@app.route('/customers/<id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    

    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"}), 200





#============ END POINTS PRODUCTS ===============

# Create a Product
@app.route('/products', methods=['POST'])
def create_product():
    product_data = request.json
    new_product = Product(product_name=product_data['product_name'], price=product_data['price'])
    
    db.session.add(new_product)
    db.session.commit()
    return product_schema.jsonify(new_product), 201

# Route to Get all Products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

# Route to Get Product by ID
@app.route('/products/<id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return product_schema.jsonify(product)

# Route to Update Product by ID
@app.route('/products/<id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    product_data = request.json

    if 'product_name' in product_data:
        product.product_name = product_data['product_name']
    if 'price' in product_data:
        product.price = product_data['price']

    db.session.commit()
    return product_schema.jsonify(product)

# Route to Delete Product
@app.route('/products/<id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200

#======= END POINTS ORDERS============

# Create Order Route
@app.route('/orders', methods=['POST'])
def create_order():
    order_data = request.json
    customer_id = order_data.get('customer_id')
    new_order = Order(customer_id=customer_id)
    db.session.add(new_order)
    db.session.commit()
    return order_schema.jsonify(new_order), 201

# Add Product to Order Route
@app.route('/orders/<order_id>/add_product/<product_id>', methods=['GET'])
def add_product_to_order(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)

    # Duplicates
    if product in order.products:
        return jsonify({"message": "Product already added to the order"}), 400

    order.products.append(product)
    db.session.commit()
    return order_schema.jsonify(order)

# Remove Product from a Order Route
@app.route('/orders/<order_id>/remove_product', methods=['DELETE'])
def remove_product_from_order(order_id):
    order = Order.query.get_or_404(order_id)
    product_id = request.json.get('product_id')
    product = Product.query.get_or_404(product_id)

    if product not in order.products:
        return jsonify({"message": "Product not found in the order"}), 404

    order.products.remove(product)
    db.session.commit()
    return order_schema.jsonify(order)

# Get Orders for a User Route
@app.route('/orders/user/<user_id>', methods=['GET'])
def get_orders_for_user(user_id):
    orders = Order.query.filter_by(customer_id=user_id).all()
    return orders_schema.jsonify(orders)

# Get Products for a Order Route
@app.route('/orders/<order_id>/products', methods=['GET'])
def get_products_for_order(order_id):
    order = Order.query.get_or_404(order_id)
    return products_schema.jsonify(order.products)


if __name__ == "__main__":
    
    with app.app_context():
        
        db.create_all()
    
    app.run(debug=True)