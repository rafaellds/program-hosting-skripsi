import streamlit as st


def page_header(title, subtitle=None):
    """
    Fungsi ini digunakan untuk menampilkan judul halaman dengan format yang rapi.
    """
    st.markdown(f'<div class="main-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="sub-title">{subtitle}</div>', unsafe_allow_html=True)


def section_title(title):
    """
    Fungsi ini digunakan untuk menampilkan judul bagian atau subbagian.
    """
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def info_card(title, body):
    """
    Fungsi ini digunakan untuk menampilkan kotak informasi.
    """
    st.markdown(
        f"""
        <div class="info-card">
            <b>{title}</b><br>
            {body}
        </div>
        """,
        unsafe_allow_html=True
    )


def success_card(title, body):
    """
    Fungsi ini digunakan untuk menampilkan kotak status berhasil.
    """
    st.markdown(
        f"""
        <div class="success-card">
            <b>{title}</b><br>
            {body}
        </div>
        """,
        unsafe_allow_html=True
    )


def warning_card(title, body):
    """
    Fungsi ini digunakan untuk menampilkan kotak peringatan.
    """
    st.markdown(
        f"""
        <div class="warning-card">
            <b>{title}</b><br>
            {body}
        </div>
        """,
        unsafe_allow_html=True
    )


def error_card(title, body):
    """
    Fungsi ini digunakan untuk menampilkan kotak error.
    """
    st.markdown(
        f"""
        <div class="error-card">
            <b>{title}</b><br>
            {body}
        </div>
        """,
        unsafe_allow_html=True
    )


def badge(text):
    """
    Fungsi ini digunakan untuk menampilkan label kecil pada dashboard.
    """
    st.markdown(f'<span class="method-badge">{text}</span>', unsafe_allow_html=True)
