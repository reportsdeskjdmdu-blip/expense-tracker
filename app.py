import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
from PIL import Image
import pytesseract

# Tesseract path configuration (Windows default path)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- 1. DATABASE SETUP ---
DB_NAME = "expenses.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            store_name TEXT,
            store_contact TEXT,
            bill_no TEXT,
            product_name TEXT,
            quantity REAL,
            rate REAL,
            total_price REAL,
            entry_type TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        data = cursor.fetchall()
        conn.close()
        return data
    conn.commit()
    conn.close()

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title="Smart Expense Tracker", page_icon="📊", layout="centered")
st.title("🛒 Smart Expense Tracker & Price Trend")

menu = st.sidebar.radio("Navigation", ["Dashboard", "Manual Entry", "Bill OCR Scan", "View All Expenses"])

# --- 3. MANUAL ENTRY PAGE ---
if menu == "Manual Entry":
    st.header("📝 Manual Expense Entry")
    with st.form("manual_entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("Date", datetime.today())
            store_name = st.text_input("Store Name", value="முத்து ஸ்டோர்")
            bill_no = st.text_input("Bill No")
        with col2:
            entry_time = st.time_input("Time", datetime.now().time())
            store_contact = st.text_input("Store Contact No", value="8838250290")
            
        st.divider()
        product_name = st.text_input("Product Name (English / தமிழ்)")
        c1, c2 = st.columns(2)
        with c1:
            quantity = st.number_input("Quantity / Weight", min_value=0.01, value=1.0)
        with c2:
            rate = st.number_input("Rate per Unit (₹)", min_value=0.0, value=0.0)
            
        total_price = quantity * rate
        st.info(f"Calculated Total Price: ₹ **{total_price:.2f}**")
        
        submit = st.form_submit_button("Save Expense")
        if submit:
            if store_name and product_name and rate > 0:
                run_query(
                    "INSERT INTO expenses (date, time, store_name, store_contact, bill_no, product_name, quantity, rate, total_price, entry_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(entry_date), str(entry_time), store_name, store_contact, bill_no, product_name, quantity, rate, total_price, "Manual"),
                    fetch=False
                )
                st.success("Expense saved successfully!")
            else:
                st.error("Please fill required fields.")

# --- 4. BILL OCR SCAN & MULTI-ITEM EXTRACTION PAGE ---
elif menu == "Bill OCR Scan":
    st.header("📸 Tamil & English Bill OCR Scan")
    st.write("பில் போட்டோவை அப்லோட் செய்யவும் அல்லது கேமராவில் எடுக்கவும்:")
    
    upload_option = st.radio("Choose option:", ["Take Photo using Camera", "Upload Bill Image / PDF"], horizontal=True)
    
    bill_image = None
    if upload_option == "Take Photo using Camera":
        bill_image = st.camera_input("Take a picture of the bill")
    else:
        bill_image = st.file_uploader("Upload Bill (JPEG, PNG)", type=["jpg", "jpeg", "png"])
    
    if bill_image is not None:
        img = Image.open(bill_image)
        st.image(img, caption="Uploaded Bill", use_container_width=True)
        
        with st.spinner("Reading Tamil & English Text from Bill (OCR Processing)..."):
            try:
                ocr_text = pytesseract.image_to_string(img, lang='eng+tam')
                st.subheader("Extracted Raw Text from Bill:")
                st.text_area("OCR Result", ocr_text, height=150)
            except Exception as e:
                st.error(f"OCR Error: {e}")
                ocr_text = ""

        st.divider()
        st.subheader("📦 Add Bill Items (Multi-Item Entry)")
        st.write("பில்லில் உள்ள பொருட்களை கீழே உள்ள டேபிளில் சரிபார்த்து ஒரே அடியில் சேமிக்கவும்:")
        
        default_data = pd.DataFrame([
            {"Product Name": "சன்ரைஸ் 2ரூ", "Quantity": 1.0, "Rate": 22.0},
            {"Product Name": "குழம்பு மிளகாய் தூள்", "Quantity": 1.0, "Rate": 37.0},
            {"Product Name": "ஆச்சி சில்லி 20 rs", "Quantity": 1.0, "Rate": 18.0},
            {"Product Name": "சிக்கன் மசாலா 50g", "Quantity": 1.0, "Rate": 18.0},
            {"Product Name": "விம் ஜெல் 15ரூ", "Quantity": 1.0, "Rate": 14.5},
            {"Product Name": "பிலவர்ஸ் லிலய் ப்ரே", "Quantity": 1.0, "Rate": 90.0},
            {"Product Name": "5ரூ இஞ்சி பூண்டு பேஸ்ட்", "Quantity": 2.0, "Rate": 5.0}
        ])

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            b_store = st.text_input("Store Name", value="முத்து ஸ்டோர், மதுரை")
            b_no = st.text_input("Bill No", value="15426")
        with col_b2:
            b_date = st.date_input("Bill Date", datetime.strptime("2026-10-02", "%Y-%m-%d"))
            b_contact = st.text_input("Store Contact", value="8838250290")

        edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

        if st.button("💾 Save All Bill Items"):
            saved_count = 0
            for index, row in edited_df.iterrows():
                p_name = row["Product Name"]
                qty = float(row["Quantity"])
                rate = float(row["Rate"])
                tot = qty * rate
                if p_name and rate > 0:
                    run_query(
                        "INSERT INTO expenses (date, time, store_name, store_contact, bill_no, product_name, quantity, rate, total_price, entry_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (str(b_date), str(datetime.now().time()), b_store, b_contact, b_no, p_name, qty, rate, tot, "OCR Multi"),
                        fetch=False
                    )
                    saved_count += 1
            st.success(f"Successfully saved {saved_count} items from the bill to Database!")

# --- 5. DASHBOARD & ANALYTICS PAGE ---
elif menu == "Dashboard":
    st.header("📊 Expense Dashboard")
    data = run_query("SELECT * FROM expenses")
    if not data:
        st.info("No expense data found yet.")
    else:
        df = pd.DataFrame(data, columns=["ID", "Date", "Time", "Store Name", "Store Contact", "Bill No", "Product Name", "Quantity", "Rate", "Total Price", "Entry Type"])
        df['Date'] = pd.to_datetime(df['Date'])
        
        today_str = pd.Timestamp.today().normalize()
        daily_total = df[df['Date'] == today_str]['Total Price'].sum()
        monthly_total = df[df['Date'].dt.month == pd.Timestamp.today().month]['Total Price'].sum()
        yearly_total = df[df['Date'].dt.year == pd.Timestamp.today().year]['Total Price'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Today's Total", f"₹ {daily_total:.2f}")
        col2.metric("This Month", f"₹ {monthly_total:.2f}")
        col3.metric("This Year", f"₹ {yearly_total:.2f}")  # Corrected format specifier
        
        st.divider()
        st.subheader("📈 Product Price Trend Tracker")
        unique_products = df['Product Name'].unique()
        selected_product = st.selectbox("Select a product to view price history:", unique_products)
        
        if selected_product:
            prod_df = df[df['Product Name'] == selected_product].sort_values('Date')
            if not prod_df.empty:
                fig = px.line(prod_df, x='Date', y='Rate', markers=True, title=f"Price History for: {selected_product}")
                st.plotly_chart(fig, use_container_width=True)

# --- 6. VIEW ALL EXPENSES & EXCEL DOWNLOAD PAGE ---
elif menu == "View All Expenses":
    st.header("📋 All Expense Records & Excel Download")
    data = run_query("SELECT date, time, store_name, store_contact, bill_no, product_name, quantity, rate, total_price, entry_type FROM expenses ORDER BY date DESC")
    if data:
        df_all = pd.DataFrame(data, columns=["Date", "Time", "Store", "Contact", "Bill No", "Product", "Qty", "Rate", "Total", "Type"])
        st.dataframe(df_all, use_container_width=True)
        
        csv = df_all.to_csv(index=False).encode('utf-8-sig')
        
        st.download_button(
            label="📥 Download Expenses as Excel/CSV",
            data=csv,
            file_name=f"expenses_report_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("No records found to download.")