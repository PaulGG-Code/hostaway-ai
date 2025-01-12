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

def finance_standard_report_page():
    """
    Main function to handle the Finance Standard Report page.
    """
    st.title("Finance Standard Report")

    # Retrieve keys from session state
    openai_api_key = st.session_state.get("openai_api_key")
    hostaway_bearer_token = st.session_state.get("hostaway_bearer_token")
    hostaway_api_url = "https://api.hostaway.com/v1/finance/report/standard"

    if not openai_api_key or not hostaway_bearer_token:
        st.error("Please provide your OpenAI API Key and Hostaway Token in the sidebar.")
        return

    # Input for filtering parameters
    from_date = st.date_input("From Date:", value=pd.to_datetime("2023-01-01")).strftime("%Y-%m-%d")
    to_date = st.date_input("To Date:", value=pd.to_datetime("2023-12-31")).strftime("%Y-%m-%d")
    date_type = st.selectbox("Select Date Type:", ["arrivalDate", "departureDate", "reservationDate"])
    selected_channels = st.multiselect(
        "Select Channels:",
        options=list(CHANNELS.keys()),
        format_func=lambda x: CHANNELS[x],
        default=[2018]  # Default to Airbnb Official
    )

    payload = {
        "fromDate": from_date,
        "toDate": to_date,
        "dateType": date_type,
        "channelIds": selected_channels,
        "format": "csv",
        "sortBy": "arrivalDate",
        "sortOrder": "asc",
        "delimiter": "comma",
    }

    # Fetch CSV data
    with st.spinner("Fetching CSV data... This might take a while for large datasets."):
        csv_data = fetch_csv_from_hostaway(hostaway_api_url, hostaway_bearer_token, payload)

    if csv_data is not None and not csv_data.empty:
        st.success("CSV data loaded successfully!")
        st.write(f"Total Rows: {len(csv_data)}")

        # Reduce the dataset size if it's too large
        MAX_ROWS = 100
        if len(csv_data) > MAX_ROWS:
            st.warning(f"The dataset is too large. Displaying the first {MAX_ROWS} rows.")
            csv_data = csv_data.head(MAX_ROWS)

        # Allow users to optimize the dataset further by selecting specific columns
        if st.checkbox("Optimize Data for Analysis (Remove Unnecessary Columns)"):
            columns_to_keep = st.multiselect(
                "Select Columns to Keep:",
                csv_data.columns.tolist(),
                default=csv_data.columns.tolist()[:5],  # Default to first 5 columns
            )
            csv_data = csv_data[columns_to_keep]

        # Display the dataset
        st.dataframe(csv_data)

        # Prepare the CSV buffer for the agent
        csv_buffer = StringIO()
        csv_data.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # Create the LangChain agent
        agent = create_csv_agent(OpenAI(temperature=0, openai_api_key=openai_api_key), csv_buffer, verbose=True, allow_dangerous_code=True)

        # User input for questions
        user_question = st.text_input("Ask a question about your financial data:")
        if user_question:
            with st.spinner("Processing your query..."):
                try:
                    response = agent.run(user_question)
                    st.write(response)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        # Provide a download option for the dataset
        st.download_button(
            label="Download Finance Standard Data CSV",
            data=csv_data.to_csv(index=False),
            file_name="finance_standard_report.csv",
            mime="text/csv"
        )
    else:
        st.warning("No data available. Please check your parameters.")