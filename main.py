import streamlit as st
from dotenv import load_dotenv

# Import pages
from pages.csv_analysis import csv_analysis_page
from pages.listing_financial_report import listing_financial_page
from pages.finance_standard_report import finance_standard_report_page
from pages.rental_revenue_validation import rental_revenue_validation_page

# Custom CSS for styling
def add_custom_css():
    st.markdown(
        """
        <style>
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f4f4f4; /* Light gray sidebar background */
        }

        /* Menu header styling */
        .menu-header {
            font-size: 18px;
            font-weight: bold;
            color: #f3f6f4;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        /* Input field styling */
        .css-1cpxqw2 textarea {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: ##f3f6f4;
        }
        
        /* Sidebar radio styling */
        .css-qrbaxs {
            font-size: 16px;
            font-weight: 500;
            color: ##f3f6f4;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Main app function
def main():
    st.set_page_config(page_title="Hostaway Dashboard", layout="wide")
    add_custom_css()  # Apply custom styles

    # Sidebar: Styled menu with icons and inputs
    st.sidebar.title("🔧 Environment Setup")
    st.sidebar.markdown('<div class="menu-header">API Keys</div>', unsafe_allow_html=True)
    if "openai_api_key" not in st.session_state:
        st.session_state["openai_api_key"] = ""
    if "hostaway_bearer_token" not in st.session_state:
        st.session_state["hostaway_bearer_token"] = ""

    # Input fields for OpenAI and Hostaway tokens
    st.session_state["openai_api_key"] = st.sidebar.text_input(
        "🔑 OpenAI API Key",
        value=st.session_state["openai_api_key"],
        type="password",
        help="Enter your OpenAI API key here.",
    )
    st.session_state["hostaway_bearer_token"] = st.sidebar.text_input(
        "🔑 Hostaway Bearer Token",
        value=st.session_state["hostaway_bearer_token"],
        type="password",
        help="Enter your Hostaway token here.",
    )

    # Navigation menu
    st.sidebar.markdown('<div class="menu-header">Navigation</div>', unsafe_allow_html=True)
    page = st.sidebar.radio(
        "📂 Select a Page:",
        options=[
            "CSV Analysis",
            "Listing Financial Report",
            "Finance Standard Report",
            "Rental Revenue Validation",  # New page added here
        ],
    )

    # Render the selected page
    if page == "CSV Analysis":
        csv_analysis_page()
    elif page == "Listing Financial Report":
        listing_financial_page()
    elif page == "Finance Standard Report":
        finance_standard_report_page()
    elif page == "Rental Revenue Validation":  # New page case
        rental_revenue_validation_page()

    # Footer in the sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <small>🔍 <a href="https://hostaway.com" target="_blank" style="text-decoration: none;">Hostaway API Documentation</a></small>
        <br>
        <small>⚙️ <a href="https://platform.openai.com/docs" target="_blank" style="text-decoration: none;">OpenAI Documentation</a></small>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()