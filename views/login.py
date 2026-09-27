import streamlit as st
import bcrypt

from utils.database import get_connection


def halaman_login():
    """
    Menampilkan halaman login dan melakukan autentikasi
    pengguna menggunakan data akun pada PostgreSQL.
    """

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:

        # ====================================================
        # HEADER LOGIN
        # ====================================================

        st.markdown(
            """<div class="login-card">
<div class="main-title" style="font-size:30px; text-align:center;">
Login Sistem
</div>
<div class="sub-title" style="text-align:center; margin-bottom:12px;">
Sistem Clustering Siswa PKL<br>
K-Means dan K-Medoids
</div>
</div>""",
            unsafe_allow_html=True,
        )

        # ====================================================
        # INPUT LOGIN
        # ====================================================

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password",
        )

        # ====================================================
        # PROSES LOGIN
        # ====================================================

        if st.button(
            "Login",
            use_container_width=True,
            type="primary",
        ):

            username_bersih = username.strip()

            # -----------------------------------------------
            # VALIDASI INPUT
            # -----------------------------------------------

            if not username_bersih or not password:

                st.warning(
                    "Username dan password harus diisi."
                )

                return

            # -----------------------------------------------
            # KONEKSI DATABASE
            # -----------------------------------------------

            conn = get_connection()

            if conn is None:

                st.error(
                    "Koneksi database gagal."
                )

                return

            cursor = None

            try:

                cursor = conn.cursor()

                # -------------------------------------------
                # MENCARI AKUN
                # -------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        id_pengguna,
                        nama_pengguna,
                        username,
                        password_hash,
                        role
                    FROM pengguna
                    WHERE username = %s
                    """,
                    (username_bersih,),
                )

                pengguna = cursor.fetchone()

                # -------------------------------------------
                # MEMERIKSA PASSWORD
                # -------------------------------------------

                password_valid = False

                if pengguna is not None:

                    password_valid = bcrypt.checkpw(
                        password.encode("utf-8"),
                        pengguna[3].encode("utf-8"),
                    )

                if not password_valid:

                    st.error(
                        "Username atau password salah."
                    )

                    return

                # -------------------------------------------
                # VALIDASI ROLE
                # -------------------------------------------

                role = pengguna[4]

                role_valid = [
                    "admin",
                    "pengelola_pkl",
                    "pimpinan",
                ]

                if role not in role_valid:

                    st.error(
                        "Role pengguna tidak dikenali oleh sistem."
                    )

                    return

                # -------------------------------------------
                # MENYIMPAN SESSION LOGIN
                # -------------------------------------------

                st.session_state.login = True
                st.session_state.id_pengguna = pengguna[0]
                st.session_state.nama_pengguna = pengguna[1]
                st.session_state.username = pengguna[2]
                st.session_state.role = role

                st.success(
                    "Login berhasil."
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Terjadi kesalahan saat proses login: {error}"
                )

            finally:

                if cursor is not None:
                    cursor.close()

                conn.close()

        # ====================================================
        # INFORMASI LOGIN
        # ====================================================

        st.markdown(
            """<div class="small-text" style="text-align:center; margin-top:10px;">
Masukkan username dan password sesuai akun pengguna.
</div>""",
            unsafe_allow_html=True,
        )