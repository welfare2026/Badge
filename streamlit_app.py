import streamlit as st
from supabase import create_client

# 1. Initialize Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- LOGIN SYSTEM ---
if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.header("🔑 Login to Gate Pass System")
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        res = supabase.table("app_users").select("*").eq("username", user_input).eq("password", pass_input).execute()
        if res.data:
            st.session_state.user = res.data[0]
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# Get current user info
user_role = st.session_state.user['role']
username = st.session_state.user['username']

st.sidebar.write(f"Logged in as: **{username}** ({user_role})")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# --- ADMIN PANEL (Only for Approver/Admin role) ---
if user_role == "Approver":
    with st.sidebar.expander("⚙️ Admin Settings"):
        st.subheader("Add New User")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        new_role = st.selectbox("Assign Role", ["Creator", "Approver", "Security"])
        
        if st.button("Create User"):
            supabase.table("app_users").insert({
                "username": new_user, "password": new_pass, "role": new_role
            }).execute()
            st.success("User added!")

# --- ROLE-BASED NAVIGATION ---
menu = []
if user_role == "Creator":
    menu = ["Employee Portal"]
elif user_role == "Approver":
    menu = ["Employee Portal", "Security Dashboard"]
elif user_role == "Security":
    menu = ["Gate Control (Guard)"]

page = st.sidebar.radio("Navigation", menu)

import streamlit as st
from supabase import create_client
import base64

# 1. Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Gate Pass System", layout="wide")

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Employee Portal", "Security Dashboard", "Gate Control (Guard)"])

# --- PAGE 1: EMPLOYEE PORTAL ---
if page == "Employee Portal":
    st.header("Step 1: Request a Gate Pass")
    v_id = st.text_input("Scan National ID Barcode")
    if v_id:
        res = supabase.table("visitors").select("*").eq("national_id", v_id).execute()
        if res.data:
            visitor = res.data[0]
            st.success(f"Visitor Found: {visitor['full_name']}")
            st.image(visitor['photo_data'], width=200)
            emp_name = st.text_input("Your Name (Requester)")
            if st.button("Submit Request"):
                supabase.table("pass_requests").insert({"visitor_id": v_id, "employee_name": emp_name, "status": "Pending"}).execute()
                st.info("Request sent!")
        else:
            st.warning("New Visitor - Register First")
            new_name = st.text_input("Enter Full Name")
            new_photo = st.camera_input("Take Photo")
            if st.button("Register Visitor"):
                if new_photo:
                    encoded_img = f"data:image/jpeg;base64,{base64.b64encode(new_photo.getvalue()).decode()}"
                    supabase.table("visitors").insert({"national_id": v_id, "full_name": new_name, "photo_data": encoded_img}).execute()
                    st.success("Registered! Scan ID again to request pass.")

# --- PAGE 2: SECURITY DASHBOARD ---
elif page == "Security Dashboard":
    st.header("Step 2: Security Office Approval")
    pending = supabase.table("pass_requests").select("*, visitors(full_name, photo_data)").eq("status", "Pending").execute()
    if pending.data:
        for req in pending.data:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                with c1: st.image(req['visitors']['photo_data'], width=100)
                with c2: st.write(f"**Visitor:** {req['visitors']['full_name']} | **Req by:** {req['employee_name']}")
                with c3:
                    if st.button("✅ APPROVE", key=f"app_{req['id']}"):
                        supabase.table("pass_requests").update({"status": "Approved"}).eq("id", req['id']).execute()
                        st.rerun()
    else: st.info("No pending requests.")

# --- PAGE 3: GATE CONTROL (THE GUARD) ---
elif page == "Gate Control (Guard)":
    st.header("Step 3 & 4: Gate Check-In/Out")
    st.write("Scan the National ID barcode to check-in or check-out a visitor.")
    
    scan_id = st.text_input("SCAN BARCODE HERE", key="guard_scan")
    
    if scan_id:
        # Check for Approved or On-Site status
        res = supabase.table("pass_requests").select("*, visitors(full_name, photo_data)").eq("visitor_id", scan_id).in_("status", ["Approved", "On-Site"]).order("created_at", desc=True).limit(1).execute()
        
        if res.data:
            current_pass = res.data[0]
            st.image(current_pass['visitors']['photo_data'], width=200)
            st.subheader(f"Visitor: {current_pass['visitors']['full_name']}")
            
            if current_pass['status'] == "Approved":
                st.warning("Status: READY FOR ENTRY")
                if st.button("🟢 MARK AS ENTERED"):
                    supabase.table("pass_requests").update({"status": "On-Site"}).eq("id", current_pass['id']).execute()
                    st.success("Visitor is now On-Site")
                    st.rerun()
            
            elif current_pass['status'] == "On-Site":
                st.error("Status: CURRENTLY ON-SITE")
                if st.button("🔴 MARK AS EXITED"):
                    supabase.table("pass_requests").update({"status": "Exited"}).eq("id", current_pass['id']).execute()
                    st.success("Visitor has Exited")
                    st.rerun()
        else:
            st.error("No valid/approved pass found for this ID.")
            
