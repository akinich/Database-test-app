import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

# Database connection pool
@st.cache_resource
def init_connection_pool():
    """Initialize connection pool to PostgreSQL database"""
    try:
        return psycopg2.pool.SimpleConnectionPool(
            1, 10,  # min and max connections
            host=st.secrets["database"]["host"],
            database=st.secrets["database"]["database"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            port=st.secrets["database"]["port"]
        )
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection_pool = init_connection_pool()
    if connection_pool is None:
        yield None
        return
    
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def init_database():
    """Initialize the database with tables if they don't exist"""
    with get_db_connection() as conn:
        if conn is None:
            return
        cursor = conn.cursor()
        
        # Create Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(50),
                city VARCHAR(100),
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create Inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id SERIAL PRIMARY KEY,
                product_name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                quantity INTEGER,
                price DECIMAL(10, 2),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()

# CRUD Operations for Customers
def add_customer(name, email, phone, city):
    """Add a new customer to the database"""
    with get_db_connection() as conn:
        if conn is None:
            return False, "Database connection failed"
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO customers (name, email, phone, city, created_date)
                VALUES (%s, %s, %s, %s, %s)
            ''', (name, email, phone, city, datetime.now()))
            conn.commit()
            return True, "Customer added successfully!"
        except psycopg2.IntegrityError:
            conn.rollback()
            return False, "Email already exists!"
        except Exception as e:
            conn.rollback()
            return False, f"Error: {str(e)}"

def get_all_customers():
    """Retrieve all customers from database"""
    with get_db_connection() as conn:
        if conn is None:
            return pd.DataFrame()
        try:
            df = pd.read_sql_query("SELECT * FROM customers ORDER BY id", conn)
            return df
        except Exception as e:
            st.error(f"Error fetching customers: {e}")
            return pd.DataFrame()

def update_customer(customer_id, name, email, phone, city):
    """Update an existing customer"""
    with get_db_connection() as conn:
        if conn is None:
            return False, "Database connection failed"
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE customers 
                SET name=%s, email=%s, phone=%s, city=%s
                WHERE id=%s
            ''', (name, email, phone, city, customer_id))
            conn.commit()
            return True, "Customer updated successfully!"
        except Exception as e:
            conn.rollback()
            return False, f"Error: {str(e)}"

def delete_customer(customer_id):
    """Delete a customer by ID"""
    with get_db_connection() as conn:
        if conn is None:
            return "Database connection failed"
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM customers WHERE id=%s", (customer_id,))
            conn.commit()
            return "Customer deleted successfully!"
        except Exception as e:
            conn.rollback()
            return f"Error: {str(e)}"

# CRUD Operations for Inventory
def add_inventory_item(product_name, category, quantity, price):
    """Add a new inventory item"""
    with get_db_connection() as conn:
        if conn is None:
            return "Database connection failed"
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO inventory (product_name, category, quantity, price, last_updated)
                VALUES (%s, %s, %s, %s, %s)
            ''', (product_name, category, quantity, price, datetime.now()))
            conn.commit()
            return "Inventory item added successfully!"
        except Exception as e:
            conn.rollback()
            return f"Error: {str(e)}"

def get_all_inventory():
    """Retrieve all inventory items"""
    with get_db_connection() as conn:
        if conn is None:
            return pd.DataFrame()
        try:
            df = pd.read_sql_query("SELECT * FROM inventory ORDER BY id", conn)
            return df
        except Exception as e:
            st.error(f"Error fetching inventory: {e}")
            return pd.DataFrame()

def update_inventory_item(item_id, product_name, category, quantity, price):
    """Update an existing inventory item"""
    with get_db_connection() as conn:
        if conn is None:
            return "Database connection failed"
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE inventory 
                SET product_name=%s, category=%s, quantity=%s, price=%s, last_updated=%s
                WHERE id=%s
            ''', (product_name, category, quantity, price, datetime.now(), item_id))
            conn.commit()
            return "Inventory item updated successfully!"
        except Exception as e:
            conn.rollback()
            return f"Error: {str(e)}"

def delete_inventory_item(item_id):
    """Delete an inventory item by ID"""
    with get_db_connection() as conn:
        if conn is None:
            return "Database connection failed"
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM inventory WHERE id=%s", (item_id,))
            conn.commit()
            return "Inventory item deleted successfully!"
        except Exception as e:
            conn.rollback()
            return f"Error: {str(e)}"

# Initialize database
init_database()

# Streamlit App
st.set_page_config(page_title="SQL Learning App", layout="wide")
st.title("🎓 SQL Database Learning App")
st.markdown("**Learn how SQL databases work with Python and Streamlit + Supabase**")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose a section:", 
                        ["📊 Dashboard", "👥 Customers", "📦 Inventory", "📚 SQL Basics"])

# Dashboard Page
if page == "📊 Dashboard":
    st.header("Dashboard Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        customers_df = get_all_customers()
        st.metric("Total Customers", len(customers_df))
        
        if not customers_df.empty and 'city' in customers_df.columns:
            st.subheader("Customers by City")
            city_counts = customers_df['city'].value_counts().reset_index()
            city_counts.columns = ['City', 'Count']
            fig = px.bar(city_counts, x='City', y='Count', color='City')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        inventory_df = get_all_inventory()
        st.metric("Total Products", len(inventory_df))
        
        if not inventory_df.empty and 'category' in inventory_df.columns:
            st.subheader("Inventory by Category")
            category_counts = inventory_df['category'].value_counts().reset_index()
            category_counts.columns = ['Category', 'Count']
            fig = px.pie(category_counts, values='Count', names='Category')
            st.plotly_chart(fig, use_container_width=True)

# Customers Page
elif page == "👥 Customers":
    st.header("Customer Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["View All", "Add New", "Update", "Delete"])
    
    with tab1:
        st.subheader("All Customers")
        customers_df = get_all_customers()
        if customers_df.empty:
            st.info("No customers found. Add your first customer!")
        else:
            st.dataframe(customers_df, use_container_width=True)
            
            # Download option
            csv = customers_df.to_csv(index=False)
            st.download_button("Download as CSV", csv, "customers.csv", "text/csv")
    
    with tab2:
        st.subheader("Add New Customer")
        with st.form("add_customer_form"):
            name = st.text_input("Name*")
            email = st.text_input("Email*")
            phone = st.text_input("Phone")
            city = st.text_input("City")
            submit = st.form_submit_button("Add Customer")
            
            if submit:
                if name and email:
                    success, message = add_customer(name, email, phone, city)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Name and Email are required!")
    
    with tab3:
        st.subheader("Update Customer")
        customers_df = get_all_customers()
        if customers_df.empty:
            st.info("No customers to update.")
        else:
            customer_id = st.selectbox("Select Customer ID", customers_df['id'].tolist())
            selected_customer = customers_df[customers_df['id'] == customer_id].iloc[0]
            
            with st.form("update_customer_form"):
                name = st.text_input("Name", value=selected_customer['name'])
                email = st.text_input("Email", value=selected_customer['email'])
                phone = st.text_input("Phone", value=str(selected_customer['phone']) if pd.notna(selected_customer['phone']) else "")
                city = st.text_input("City", value=str(selected_customer['city']) if pd.notna(selected_customer['city']) else "")
                submit = st.form_submit_button("Update Customer")
                
                if submit:
                    success, message = update_customer(customer_id, name, email, phone, city)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    with tab4:
        st.subheader("Delete Customer")
        customers_df = get_all_customers()
        if customers_df.empty:
            st.info("No customers to delete.")
        else:
            customer_id = st.selectbox("Select Customer ID to Delete", customers_df['id'].tolist())
            selected_customer = customers_df[customers_df['id'] == customer_id].iloc[0]
            
            st.warning(f"⚠️ You are about to delete: **{selected_customer['name']}** ({selected_customer['email']})")
            
            if st.button("Delete Customer", type="primary"):
                message = delete_customer(customer_id)
                st.success(message)
                st.rerun()

# Inventory Page
elif page == "📦 Inventory":
    st.header("Inventory Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["View All", "Add New", "Update", "Delete"])
    
    with tab1:
        st.subheader("All Inventory Items")
        inventory_df = get_all_inventory()
        if inventory_df.empty:
            st.info("No inventory items found. Add your first product!")
        else:
            st.dataframe(inventory_df, use_container_width=True)
            
            # Calculate total inventory value
            if 'quantity' in inventory_df.columns and 'price' in inventory_df.columns:
                total_value = (inventory_df['quantity'] * inventory_df['price']).sum()
                st.metric("Total Inventory Value", f"${total_value:,.2f}")
            
            csv = inventory_df.to_csv(index=False)
            st.download_button("Download as CSV", csv, "inventory.csv", "text/csv")
    
    with tab2:
        st.subheader("Add New Inventory Item")
        with st.form("add_inventory_form"):
            product_name = st.text_input("Product Name*")
            category = st.text_input("Category")
            quantity = st.number_input("Quantity", min_value=0, value=0)
            price = st.number_input("Price", min_value=0.0, value=0.0, format="%.2f")
            submit = st.form_submit_button("Add Item")
            
            if submit:
                if product_name:
                    message = add_inventory_item(product_name, category, quantity, price)
                    st.success(message)
                    st.rerun()
                else:
                    st.error("Product name is required!")
    
    with tab3:
        st.subheader("Update Inventory Item")
        inventory_df = get_all_inventory()
        if inventory_df.empty:
            st.info("No inventory items to update.")
        else:
            item_id = st.selectbox("Select Item ID", inventory_df['id'].tolist())
            selected_item = inventory_df[inventory_df['id'] == item_id].iloc[0]
            
            with st.form("update_inventory_form"):
                product_name = st.text_input("Product Name", value=selected_item['product_name'])
                category = st.text_input("Category", value=str(selected_item['category']) if pd.notna(selected_item['category']) else "")
                quantity = st.number_input("Quantity", min_value=0, value=int(selected_item['quantity']))
                price = st.number_input("Price", min_value=0.0, value=float(selected_item['price']), format="%.2f")
                submit = st.form_submit_button("Update Item")
                
                if submit:
                    message = update_inventory_item(item_id, product_name, category, quantity, price)
                    st.success(message)
                    st.rerun()
    
    with tab4:
        st.subheader("Delete Inventory Item")
        inventory_df = get_all_inventory()
        if inventory_df.empty:
            st.info("No inventory items to delete.")
        else:
            item_id = st.selectbox("Select Item ID to Delete", inventory_df['id'].tolist())
            selected_item = inventory_df[inventory_df['id'] == item_id].iloc[0]
            
            st.warning(f"⚠️ You are about to delete: **{selected_item['product_name']}**")
            
            if st.button("Delete Item", type="primary"):
                message = delete_inventory_item(item_id)
                st.success(message)
                st.rerun()

# SQL Basics Page
elif page == "📚 SQL Basics":
    st.header("Understanding SQL Basics")
    
    st.markdown("""
    ### What is SQL?
    **SQL (Structured Query Language)** is a language used to communicate with databases. Think of it as a way to ask questions and give commands to your data.
    
    ### PostgreSQL vs SQLite
    This app now uses **PostgreSQL** (via Supabase), which is a production-grade database that:
    - ✅ Stores data permanently in the cloud
    - ✅ Supports multiple users simultaneously
    - ✅ Is used by major companies worldwide
    - ✅ More powerful than SQLite
    
    ### Key SQL Operations (CRUD):
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 1. CREATE (Add Data)
        ```sql
        INSERT INTO customers (name, email, city)
        VALUES ('John Doe', 'john@email.com', 'New York')
        ```
        **What it does:** Adds a new customer to the database
        
        #### 2. READ (View Data)
        ```sql
        SELECT * FROM customers
        WHERE city = 'New York'
        ```
        **What it does:** Shows all customers from New York
        """)
    
    with col2:
        st.markdown("""
        #### 3. UPDATE (Modify Data)
        ```sql
        UPDATE inventory
        SET quantity = 50
        WHERE id = 5
        ```
        **What it does:** Changes the quantity of product #5 to 50
        
        #### 4. DELETE (Remove Data)
        ```sql
        DELETE FROM customers
        WHERE id = 10
        ```
        **What it does:** Removes customer with ID 10
        """)
    
    st.markdown("""
    ---
    ### How This App Uses SQL
    
    When you click buttons in this app, Python code runs SQL commands behind the scenes:
    
    1. **Add Customer Button** → Runs `INSERT INTO customers...`
    2. **View Customers** → Runs `SELECT * FROM customers`
    3. **Update Button** → Runs `UPDATE customers SET...`
    4. **Delete Button** → Runs `DELETE FROM customers WHERE...`
    
    ### Database Location
    Your data is stored securely in **Supabase's cloud PostgreSQL database**. This means:
    - 💾 Data persists even when the app restarts
    - 🌍 Accessible from anywhere
    - 🔒 Secure and backed up automatically
    
    ### Try It Out!
    Go to the Customers or Inventory pages and try adding, viewing, updating, and deleting data to see SQL in action!
    """)
