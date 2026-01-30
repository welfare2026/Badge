import streamlit as st
from supabase import create_client
import base64

# 1. Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Gate Pass System", layout="wide")

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Employee Portal", "Security Dashboard"])

# --- PAGE 1: EMPLOYEE PORTAL (Requesting the Pass) ---
if page == "Employee Portal":
    st.header("Step 1: Request a Gate Pass")
    v_id = st.text_input("Scan National ID Barcode")

    if v_id:
        res = supabase.table("visitors").select("*").eq("national_id", v_id).execute()
        
        if res.data:
            visitor = res.data[0]
            st.success(f"Visitor Recognized: {visitor['full_name']}")
            st.image(visitor['photo_data'], width=200)
            
            emp_name = st.text_input("Employee Name (Requester)")
            if st.button("Submit Request"):
                supabase.table("pass_requests").insert({
                    "visitor_id": v_id, "employee_name": emp_name, "status": "Pending"
                }).execute()
                st.info("Request sent to Security Officers!")
        else:
            st.warning("New Visitor - Register First")
            new_name = st.text_input("Enter Full Name")
            new_photo = st.camera_input("Take Photo")
            if st.button("Register Visitor"):
                if new_photo:
                    encoded_img = f"data:image/jpeg;base64,{base64.b64encode(new_photo.getvalue()).decode()}"
                    supabase.table("visitors").insert({
                        "national_id": v_id, "full_name": new_name, "photo_data": encoded_img
                    }).execute()
                    st.success("Registered! Now enter the ID again to request a pass.")

# --- PAGE 2: SECURITY DASHBOARD (Approving the Pass) ---
elif page == "Security Dashboard":
    st.header("Step 2 & 3: Security Approval")
    st.write("Review pending requests and click Approve to allow entry.")

    # Fetch all Pending requests and join with Visitor data
    pending = supabase.table("pass_requests").select("*, visitors(full_name, photo_data)").eq("status", "Pending").execute()

    if pending.data:
        for req in pending.data:
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    # Show the photo the employee uploaded/found
                    st.image(req['visitors']['photo_data'], width=120)
                with col2:
                    st.subheader(req['visitors']['full_name'])
                    st.write(f"**Requested by:** {req['employee_name']}")
                    st.write(f"**Date:** {req['created_at'][:10]}")
                with col3:
                    # The Approval Button
                    if st.button("✅ APPROVE", key=f"btn_{req['id']}"):
                        supabase.table("pass_requests").update({"status": "Approved"}).eq("id", req['id']).execute()
                        st.rerun()
    else:
        st.info("No pending requests at the moment.")
        
