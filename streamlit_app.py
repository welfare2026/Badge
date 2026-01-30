import streamlit as st
from supabase import create_client

# Initialize Supabase Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🛡️ Gate Pass Portal")

# Barcode Scanner Input
v_id = st.text_input("Scan National ID Barcode")

if v_id:
    # Check if visitor is already in our database
    res = supabase.table("visitors").select("*").eq("national_id", v_id).execute()
    
    if res.data:
        # VISITOR FOUND: Auto-attach details and photo
        visitor = res.data[0]
        st.success(f"Visitor Recognized: {visitor['full_name']}")
        # Display the stored photo directly from SQL
        st.image(visitor['photo_data'], width=250, caption="Stored Identity Photo")
        
        emp_name = st.text_input("Employee Name (Requester)")
        if st.button("Request Gate Pass"):
            supabase.table("pass_requests").insert({
                "visitor_id": v_id,
                "employee_name": emp_name,
                "status": "Pending"
            }).execute()
            st.info("Request sent to Security Officers!")
    else:
        # NEW VISITOR: Registration logic
        st.warning("New Visitor - Registration Required")
        new_name = st.text_input("Enter Full Name")
        new_photo = st.camera_input("Take Photo")
        
        if st.button("Register & Create Pass"):
            if new_photo and new_name:
                # Convert camera image to a string for SQL storage
                import base64
                encoded_img = f"data:image/jpeg;base64,{base64.b64encode(new_photo.getvalue()).decode()}"
                
                # Save to database
                supabase.table("visitors").insert({
                    "national_id": v_id,
                    "full_name": new_name,
                    "photo_data": encoded_img
                }).execute()
                st.success("Registered! Please refresh to create pass.")
              
