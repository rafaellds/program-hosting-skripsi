import streamlit as st

from styles import load_css

from views.login import halaman_login
from views.dashboard import halaman_dashboard
from views.kelola_data import halaman_kelola_data
from views.proses import halaman_proses
from views.hasil import halaman_hasil
from views.laporan import halaman_laporan


# =========================================================
# KONFIGURASI HALAMAN
# =========================================================

st.set_page_config(
    page_title="Sistem Clustering Siswa PKL",
    page_icon="📊",
    layout="wide",
)


# =========================================================
# LOAD CSS
# =========================================================

load_css()


# =========================================================
# SESSION STATE
# =========================================================

if "login" not in st.session_state:
    st.session_state.login = False

if "df" not in st.session_state:
    st.session_state.df = None

if "hasil" not in st.session_state:
    st.session_state.hasil = None

if "id_dataset" not in st.session_state:
    st.session_state.id_dataset = None

if "id_proses" not in st.session_state:
    st.session_state.id_proses = None


# =========================================================
# MAIN PROGRAM
# =========================================================

if not st.session_state.login:

    halaman_login()

else:

    # -----------------------------------------------------
    # INFORMASI PENGGUNA
    # -----------------------------------------------------

    role = st.session_state.get(
        "role"
    )

    nama_pengguna = st.session_state.get(
        "nama_pengguna",
        "Pengguna",
    )

    username = st.session_state.get(
        "username",
        "-",
    )

    # Nama role yang ditampilkan pada sidebar.
    nama_role = {
        "admin": "Admin",
        "pengelola_pkl": "Pengelola PKL",
        "pimpinan": "Pimpinan",
    }

    role_tampil = nama_role.get(
        role,
        "Tidak Diketahui",
    )


    # =====================================================
    # DAFTAR MENU BERDASARKAN ROLE
    # =====================================================

    menu_per_role = {

        # -------------------------------------------------
        # ADMIN
        # -------------------------------------------------
        # Admin memiliki akses ke seluruh fungsi sistem.
        "admin": [
            "Dashboard",
            "Kelola Data Penilaian",
            "Proses Clustering dan Evaluasi",
            "Hasil dan Perbandingan",
            "Laporan",
        ],

        # -------------------------------------------------
        # PENGELOLA PKL
        # -------------------------------------------------
        # Pengelola PKL dapat mengelola data,
        # menjalankan clustering, dan melihat hasil.
        # Pengelola PKL tidak memiliki akses laporan.
        "pengelola_pkl": [
            "Dashboard",
            "Kelola Data Penilaian",
            "Proses Clustering dan Evaluasi",
            "Hasil dan Perbandingan",
        ],

        # -------------------------------------------------
        # PIMPINAN
        # -------------------------------------------------
        # Pimpinan hanya melihat hasil dan laporan.
        "pimpinan": [
            "Dashboard",
            "Hasil dan Perbandingan",
            "Laporan",
        ],
    }


    # =====================================================
    # SIDEBAR
    # =====================================================

    st.sidebar.title(
        "Menu Sistem"
    )

    st.sidebar.write(
        f"**{nama_pengguna}**"
    )

    st.sidebar.caption(
        f"{role_tampil} | {username}"
    )

    st.sidebar.markdown(
        "---"
    )


    # =====================================================
    # VALIDASI ROLE
    # =====================================================

    if role not in menu_per_role:

        st.sidebar.error(
            "Role pengguna tidak dikenali."
        )

        if st.sidebar.button(
            "Logout",
            use_container_width=True,
        ):

            st.session_state.clear()

            st.rerun()

        st.error(
            "Role akun tidak sesuai dengan "
            "hak akses yang tersedia."
        )

        st.stop()


    # =====================================================
    # PILIHAN MENU
    # =====================================================

    menu = st.sidebar.radio(
        "Pilih Menu:",
        menu_per_role[role],
    )

    st.sidebar.markdown(
        "---"
    )

    st.sidebar.caption(
        "K-Means dan K-Medoids"
    )


    # =====================================================
    # LOGOUT
    # =====================================================

    if st.sidebar.button(
        "Logout",
        use_container_width=True,
    ):

        # Menghapus seluruh session agar akun
        # berikutnya tidak mewarisi session
        # pengguna sebelumnya.
        st.session_state.clear()

        # Memuat ulang aplikasi ke halaman login.
        st.rerun()


    # =====================================================
    # NAVIGASI HALAMAN
    # =====================================================

    if menu == "Dashboard":

        halaman_dashboard()

    elif menu == "Kelola Data Penilaian":

        halaman_kelola_data()

    elif menu == "Proses Clustering dan Evaluasi":

        halaman_proses()

    elif menu == "Hasil dan Perbandingan":

        halaman_hasil()

    elif menu == "Laporan":

        halaman_laporan()