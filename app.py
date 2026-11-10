import streamlit as st

st.title("Waseem Gold")
st.write("Waseem Gold - Gold Price Calculator")

weight = st.number_input("Gold Weight (gram me likhein)", min_value=0.0, value=1.0)
price = st.number_input("1 Gram Gold Price (SAR)", min_value=0.0, value=350.0)

total = weight * price

st.success(f"Total Price: {total} SAR")
st.write("Made by Waseem")
