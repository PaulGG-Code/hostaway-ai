from langchain_experimental.agents import create_csv_agent
from langchain_openai import OpenAI
import streamlit as st
import pandas as pd
from io import StringIO
import requests

# Channel ID to Name Mapping
CHANNELS = {
    2018: "Airbnb Official",
    2005: "Booking.com",
    2000: "Direct",
    # Add more channel IDs and names if needed
}

def fetch_listing_map_ids(api_url, bearer_token):
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Cache-control": "no-cache",
    }
    response = requests.get(f"{api_url}/listings", headers=headers, timeout=60)
    if response.status_code == 200:
        data = response.json()
        return [item['id'] for item in data.get('result', [])]
    return []

def fetch_csv_from_hostaway(api_url, bearer_token, payload):
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Cache-control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(api_url, headers=headers, data=payload, timeout=120)
    if response.status_code == 200:
        csv_content = StringIO(response.text)
        return pd.read_csv(csv_content, delimiter="\t")
    return None

def csv_analysis_page():
    st.title("Hostaway CSV Analysis")

    # Retrieve keys from session state
    openai_api_key = st.session_state.get("openai_api_key")
    hostaway_bearer_token = st.session_state.get("hostaway_bearer_token")
    hostaway_api_url = "https://api.hostaway.com/v1/finance/report/calculated"

    if not openai_api_key or not hostaway_bearer_token:
        st.error("Please provide your OpenAI API Key and Hostaway Token in the sidebar.")
        return

    listing_map_ids = fetch_listing_map_ids("https://api.hostaway.com/v1", hostaway_bearer_token)
    if not listing_map_ids:
        st.error("No listingMapIds found.")
        return

    from_date = st.date_input("From Date:", value=pd.to_datetime("2023-01-01")).strftime("%Y-%m-%d")
    to_date = st.date_input("To Date:", value=pd.to_datetime("2023-12-31")).strftime("%Y-%m-%d")
    date_type = st.selectbox("Select Date Type:", ["arrivalDate", "departureDate", "reservationDate"])
    status = st.selectbox("Status:", ["new", "cancelled", ""])
    selected_channels = st.multiselect("Select Channels:", list(CHANNELS.keys()), format_func=lambda x: CHANNELS[x])

    payload = (
        f"{'&'.join([f'listingMapIds%5B{index}%5D={id}' for index, id in enumerate(listing_map_ids)])}"
        f"&fromDate={from_date}&toDate={to_date}&dateType={date_type}"
        f"{'&'.join([f'channelIds%5B{index}%5D={channel}' for index, channel in enumerate(selected_channels)])}"
        f"&statuses%5B0%5D={status}&format=csv&sortBy=arrivalDate&sortOrder=asc&delimiter=tab"
    )

    csv_data = fetch_csv_from_hostaway(hostaway_api_url, hostaway_bearer_token, payload)
    if csv_data is not None and not csv_data.empty:
        st.success("CSV data loaded successfully!")
        st.dataframe(csv_data)

        csv_buffer = StringIO()
        csv_data.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Create the LangChain agent
        agent = create_csv_agent(OpenAI(temperature=0, openai_api_key=openai_api_key), csv_buffer, verbose=True, allow_dangerous_code=True)

        user_question = st.text_input("Ask a question about your CSV:")
        if user_question:
            response = agent.run(user_question)
            st.write(response)