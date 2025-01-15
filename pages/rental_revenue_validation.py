from langchain_experimental.agents import create_csv_agent
from langchain.chat_models import ChatOpenAI
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

def fetch_csv_from_hostaway(api_url, bearer_token, payload):
    """
    Fetch the CSV data from Hostaway API using a POST request.
    """
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Cache-control": "no-cache",
        "Content-Type": "application/json",
    }
    response = requests.post(api_url, headers=headers, json=payload, timeout=120)
    if response.status_code == 200:
        csv_content = StringIO(response.text)
        return pd.read_csv(csv_content, delimiter=",")
    else:
        st.error(f"Failed to fetch data: {response.status_code} {response.text}")
        return None

def rental_revenue_validation_page():
    """
    Main function to validate and display Rental Revenue data, filtering out columns with all zeros.
    """
    st.title("Rental Revenue Validation")

    # Retrieve keys from session state
    openai_api_key = st.session_state.get("openai_api_key")
    hostaway_bearer_token = st.session_state.get("hostaway_bearer_token")
    hostaway_api_url = "https://api.hostaway.com/v1/finance/report/listingFinancials"

    if not openai_api_key or not hostaway_bearer_token:
        st.error("Please provide your OpenAI API Key and Hostaway Token in the sidebar.")
        return

    # Input for filtering parameters
    from_date = st.date_input("From Date:", value=pd.to_datetime("2023-01-01")).strftime("%Y-%m-%d")
    to_date = st.date_input("To Date:", value=pd.to_datetime("2023-12-31")).strftime("%Y-%m-%d")

    # Construct the payload dynamically
    payload = {
        "fromDate": from_date,
        "toDate": to_date,
        "channelIds": [2000],  # Filter only Direct Bookings
        "format": "csv",
        "sortBy": "arrivalDate",
        "sortOrder": "asc",
        "delimiter": "comma",
    }

    # Fetch CSV data
    with st.spinner("Fetching CSV data..."):
        csv_data = fetch_csv_from_hostaway(hostaway_api_url, hostaway_bearer_token, payload)

    if csv_data is not None and not csv_data.empty:
        st.success("CSV data loaded successfully!")
        st.write(f"Total Rows: {len(csv_data)}")

        # Filter out columns where all rows are 0
        st.header("Filtered Dataset (Excluding All-Zero Columns)")
        filtered_data = csv_data.loc[:, ~(csv_data.eq(0).all())]
        st.write(f"Columns removed: {set(csv_data.columns) - set(filtered_data.columns)}")
        st.dataframe(filtered_data)

        # Ensure necessary columns exist for validation
        required_columns = ["Listing ID", "Base rate", "Cleaning fee value", "rentalRevenue"]
        missing_columns = [col for col in required_columns if col not in filtered_data.columns]

        if missing_columns:
            st.error(f"Missing required columns for validation: {missing_columns}")
            return

        # Validate: Base Rate + Cleaning Fee = Rental Revenue
        filtered_data["Calculated Revenue"] = filtered_data["Base rate"] + filtered_data["Cleaning fee value"]
        filtered_data["Validation Status"] = filtered_data["Calculated Revenue"] == filtered_data["rentalRevenue"]

        # Identify discrepancies
        discrepancies = filtered_data[filtered_data["Validation Status"] == False]

        # Display results visually
        st.header("Validation Results")
        if discrepancies.empty:
            st.success("All records are valid! No discrepancies found.")
        else:
            st.error(f"Discrepancies found in {len(discrepancies)} rows!")
            st.write("Here are the mismatched rows:")
            st.dataframe(discrepancies[["Listing ID", "Base rate", "Cleaning fee value", "rentalRevenue", "Calculated Revenue"]])

            # Provide a download option for discrepancies
            st.download_button(
                label="Download Discrepancies as CSV",
                data=discrepancies.to_csv(index=False),
                file_name="rental_revenue_discrepancies.csv",
                mime="text/csv",
            )

        # AI Agent: Query insights from data
        st.header("Ask the AI Agent")
        filtered_csv_buffer = StringIO()
        filtered_data.to_csv(filtered_csv_buffer, index=False)
        filtered_csv_buffer.seek(0)

        agent = create_csv_agent(
            ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=openai_api_key),
            filtered_csv_buffer,
            verbose=True,
            allow_dangerous_code=True,
        )

        user_question = st.text_input("Ask a question about your rental revenue data:")
        if user_question:
            with st.spinner("Processing your query..."):
                try:
                    response = agent.run(user_question)
                    st.write(response)
                except Exception as e:
                    st.error(f"An error occurred: {e}")
    else:
        st.warning("No data available. Please check your parameters.")