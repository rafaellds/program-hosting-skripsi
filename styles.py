import streamlit as st


def load_css():
    """
    Fungsi ini digunakan untuk memuat CSS agar tampilan aplikasi lebih rapi.
    """
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 34px;
            font-weight: 700;
            color: #4DA3FF;
            margin-bottom: 5px;
        }

        .sub-title {
            font-size: 18px;
            color: #B8C7D9;
            margin-bottom: 25px;
        }

        .section-title {
            font-size: 24px;
            font-weight: 650;
            color: #4DA3FF;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .info-card {
            background-color: #EAF4FF;
            color: #102A43 !important;
            padding: 18px;
            border-radius: 12px;
            border-left: 6px solid #1F4E79;
            margin-bottom: 18px;
            line-height: 1.6;
        }

        .info-card b {
            color: #102A43 !important;
        }

        .success-card {
            background-color: #E9FBEF;
            color: #102A43 !important;
            padding: 18px;
            border-radius: 12px;
            border-left: 6px solid #2E8B57;
            margin-bottom: 18px;
            line-height: 1.6;
        }

        .success-card b {
            color: #102A43 !important;
        }

        .warning-card {
            background-color: #FFF4D6;
            color: #102A43 !important;
            padding: 18px;
            border-radius: 12px;
            border-left: 6px solid #E6A100;
            margin-bottom: 18px;
            line-height: 1.6;
        }

        .warning-card b {
            color: #102A43 !important;
        }

        .error-card {
            background-color: #FFECEC;
            color: #102A43 !important;
            padding: 18px;
            border-radius: 12px;
            border-left: 6px solid #C0392B;
            margin-bottom: 18px;
            line-height: 1.6;
        }

        .error-card b {
            color: #102A43 !important;
        }

        .login-card {
            background-color: rgba(234, 244, 255, 0.08);
            padding: 24px;
            border-radius: 14px;
            border: 1px solid rgba(77, 163, 255, 0.25);
            margin-bottom: 16px;
        }

        .method-badge {
            display: inline-block;
            background-color: #EAF4FF;
            color: #1F4E79 !important;
            padding: 8px 14px;
            border-radius: 20px;
            font-weight: 600;
            margin: 5px 6px 5px 0;
            border: 1px solid #B7D7F5;
        }

        .small-text {
            font-size: 14px;
            color: #B8C7D9;
        }

        div.stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 45px;
            font-weight: 600;
        }

        div.stDownloadButton > button {
            width: 100%;
            border-radius: 10px;
            height: 45px;
            font-weight: 600;
            background-color: #1F4E79;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
