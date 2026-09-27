import streamlit as st

from components import (
    page_header,
    section_title,
    info_card,
    success_card,
    warning_card,
    badge,
)

from utils.database import (
    ambil_daftar_proses,
    ambil_hasil_proses,
)

from utils.preprocessing import (
    FITUR_CLUSTERING,
    FITUR_NONTEKNIS,
    FITUR_TEKNIS,
)


# ============================================================
# HALAMAN DASHBOARD
# ============================================================

def halaman_dashboard():
    """
    Menampilkan halaman utama sistem clustering siswa PKL.

    Dashboard menampilkan informasi pengguna, metode,
    atribut clustering, dataset aktif pada sesi aplikasi,
    serta riwayat proses clustering yang tersimpan
    di PostgreSQL.
    """

    # ========================================================
    # SESSION STATE
    # ========================================================

    if "df" not in st.session_state:
        st.session_state.df = None

    if "hasil" not in st.session_state:
        st.session_state.hasil = None

    if "id_dataset" not in st.session_state:
        st.session_state.id_dataset = None

    if "id_proses" not in st.session_state:
        st.session_state.id_proses = None

    # ========================================================
    # INFORMASI PENGGUNA
    # ========================================================

    role = st.session_state.get(
        "role"
    )

    nama_pengguna = st.session_state.get(
        "nama_pengguna",
        "Pengguna",
    )

    nama_role = {
        "admin": "Admin",
        "pengelola_pkl": "Pengelola PKL",
        "pimpinan": "Pimpinan",
    }

    role_tampil = nama_role.get(
        role,
        "Pengguna",
    )

    # ========================================================
    # HEADER
    # ========================================================

    page_header(
        "Dashboard Sistem Clustering Siswa PKL",
        (
            "Aplikasi berbasis web untuk membandingkan "
            "algoritma K-Means dan K-Medoids dalam "
            "pengelompokan siswa PKL berdasarkan "
            "profil kinerja."
        ),
    )

    # ========================================================
    # INFORMASI PENGGUNA AKTIF
    # ========================================================

    info_card(
        "Pengguna Aktif",
        (
            f"Anda masuk sebagai {nama_pengguna} "
            f"dengan role {role_tampil}. "
            "Fitur yang tersedia disesuaikan dengan "
            "hak akses pengguna."
        ),
    )

    # ========================================================
    # DESKRIPSI SISTEM
    # ========================================================

    info_card(
        "Deskripsi Sistem",
        (
            "Sistem menggunakan satu dataset penilaian siswa PKL "
            "dengan 14 atribut, yang terdiri dari 6 atribut "
            "nonteknis dan 8 atribut teknis. Dataset diproses "
            "menggunakan K-Means dan K-Medoids, kemudian hasil "
            "kedua algoritma dibandingkan menggunakan "
            "Silhouette Coefficient."
        ),
    )

    # ========================================================
    # ALUR SISTEM BERDASARKAN ROLE
    # ========================================================

    if role == "admin":

        teks_alur = (
            "Login → Kelola Data Penilaian → "
            "Proses Clustering dan Evaluasi → "
            "Hasil dan Perbandingan → Laporan."
        )

    elif role == "pengelola_pkl":

        teks_alur = (
            "Login → Kelola Data Penilaian → "
            "Proses Clustering dan Evaluasi → "
            "Hasil dan Perbandingan."
        )

    elif role == "pimpinan":

        teks_alur = (
            "Login → Hasil dan Perbandingan → "
            "Laporan."
        )

    else:

        teks_alur = (
            "Hak akses pengguna belum dikenali."
        )

    success_card(
        "Alur Sistem",
        teks_alur,
    )

    # ========================================================
    # METODE DAN KOMPONEN SISTEM
    # ========================================================

    section_title(
        "Metode dan Komponen Utama"
    )

    badge("Data Mining")
    badge("CRISP-DM")
    badge("MinMaxScaler")
    badge("K-Means")
    badge("K-Medoids/PAM")
    badge("Silhouette Coefficient")
    badge("Streamlit")
    badge("PostgreSQL")

    # ========================================================
    # ATRIBUT CLUSTERING
    # ========================================================

    section_title(
        "Atribut Clustering"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Atribut Nonteknis",
            len(FITUR_NONTEKNIS),
        )

    with col2:

        st.metric(
            "Atribut Teknis",
            len(FITUR_TEKNIS),
        )

    with col3:

        st.metric(
            "Total Atribut",
            len(FITUR_CLUSTERING),
        )

    with st.expander(
        "Lihat daftar atribut yang digunakan"
    ):

        st.markdown(
            "**Atribut Nonteknis:**"
        )

        for nomor, atribut in enumerate(
            FITUR_NONTEKNIS,
            start=1,
        ):

            st.write(
                f"{nomor}. {atribut}"
            )

        st.markdown(
            "**Atribut Teknis:**"
        )

        for nomor, atribut in enumerate(
            FITUR_TEKNIS,
            start=1,
        ):

            st.write(
                f"{nomor}. {atribut}"
            )

    # ========================================================
    # STATUS DATASET AKTIF
    # ========================================================

    section_title(
        "Status Dataset Aktif"
    )

    if st.session_state.df is not None:

        df = st.session_state.df

        kolom_tidak_ditemukan = [
            kolom
            for kolom in FITUR_CLUSTERING
            if kolom not in df.columns
        ]

        col4, col5, col6, col7 = (
            st.columns(4)
        )

        with col4:

            st.metric(
                "Jumlah Data",
                df.shape[0],
            )

        with col5:

            st.metric(
                "Jumlah Kolom",
                df.shape[1],
            )

        with col6:

            atribut_tersedia = (
                len(FITUR_CLUSTERING)
                - len(kolom_tidak_ditemukan)
            )

            st.metric(
                "Atribut Tersedia",
                atribut_tersedia,
            )

        with col7:

            if not kolom_tidak_ditemukan:
                status_dataset = "Valid"
            else:
                status_dataset = "Belum Valid"

            st.metric(
                "Status Dataset",
                status_dataset,
            )

        # ----------------------------------------------------
        # DATASET VALID DAN SUDAH TERSIMPAN
        # ----------------------------------------------------

        if (
            not kolom_tidak_ditemukan
            and st.session_state.id_dataset is not None
        ):

            success_card(
                "Dataset Aktif",
                (
                    "Dataset telah dimuat dan tersimpan "
                    "di PostgreSQL dengan ID Dataset "
                    f"{st.session_state.id_dataset}. "
                    "Dataset dapat digunakan untuk "
                    "proses clustering."
                ),
            )

        # ----------------------------------------------------
        # DATASET VALID TETAPI BELUM TERSIMPAN
        # ----------------------------------------------------

        elif not kolom_tidak_ditemukan:

            warning_card(
                "Dataset Belum Disimpan",
                (
                    "Dataset telah dimuat dan memiliki "
                    "14 atribut clustering, tetapi belum "
                    "disimpan ke PostgreSQL."
                ),
            )

        # ----------------------------------------------------
        # ATRIBUT DATASET BELUM LENGKAP
        # ----------------------------------------------------

        else:

            daftar_kolom = ", ".join(
                kolom_tidak_ditemukan
            )

            warning_card(
                "Atribut Dataset Belum Lengkap",
                (
                    "Dataset telah dimuat, tetapi masih "
                    "terdapat atribut yang belum ditemukan, "
                    f"yaitu: {daftar_kolom}."
                ),
            )

    # ========================================================
    # TIDAK ADA DATASET AKTIF
    # ========================================================

    else:

        if role in [
            "admin",
            "pengelola_pkl",
        ]:

            warning_card(
                "Tidak Ada Dataset Aktif",
                (
                    "Belum terdapat dataset yang dimuat "
                    "pada sesi aplikasi saat ini. "
                    "Jika ingin menjalankan proses baru, "
                    "buka menu Kelola Data Penilaian."
                ),
            )

        elif role == "pimpinan":

            info_card(
                "Dataset Aktif",
                (
                    "Tidak ada dataset yang sedang aktif "
                    "pada sesi ini. Riwayat hasil clustering "
                    "yang telah diproses tetap dapat dilihat "
                    "melalui database PostgreSQL."
                ),
            )

        else:

            warning_card(
                "Dataset Belum Tersedia",
                (
                    "Tidak terdapat dataset aktif "
                    "pada sesi aplikasi saat ini."
                ),
            )

    # ========================================================
    # RIWAYAT PROSES CLUSTERING
    # ========================================================

    section_title(
        "Riwayat Proses Clustering"
    )

    try:

        daftar_proses = (
            ambil_daftar_proses()
        )

    except Exception as error:

        daftar_proses = []

        st.warning(
            "Riwayat proses dari PostgreSQL "
            f"belum dapat dibaca: {error}"
        )

    # ========================================================
    # RIWAYAT TERSEDIA
    # ========================================================

    if daftar_proses:

        # Data pertama dianggap sebagai proses terbaru
        # karena query database diurutkan berdasarkan
        # proses terbaru.
        proses_terbaru = (
            daftar_proses[0]
        )

        id_proses_terbaru = (
            proses_terbaru.get(
                "id_proses"
            )
        )

        id_dataset_terbaru = (
            proses_terbaru.get(
                "id_dataset"
            )
        )

        k_kmeans = (
            proses_terbaru.get(
                "k_terbaik_kmeans",
                "-",
            )
        )

        k_kmedoids = (
            proses_terbaru.get(
                "k_terbaik_kmedoids",
                "-",
            )
        )

        # ----------------------------------------------------
        # MENGAMBIL HASIL PROSES TERBARU
        # ----------------------------------------------------

        hasil_terbaru = None

        if id_proses_terbaru is not None:

            try:

                hasil_terbaru = (
                    ambil_hasil_proses(
                        id_proses_terbaru
                    )
                )

            except Exception:

                hasil_terbaru = None

        # ----------------------------------------------------
        # INFORMASI PROSES
        # ----------------------------------------------------

        col8, col9, col10, col11 = (
            st.columns(4)
        )

        with col8:

            st.metric(
                "ID Proses Terbaru",
                (
                    id_proses_terbaru
                    if id_proses_terbaru is not None
                    else "-"
                ),
            )

        with col9:

            st.metric(
                "ID Dataset",
                (
                    id_dataset_terbaru
                    if id_dataset_terbaru is not None
                    else "-"
                ),
            )

        with col10:

            st.metric(
                "k Terbaik K-Means",
                k_kmeans,
            )

        with col11:

            st.metric(
                "k Terbaik K-Medoids",
                k_kmedoids,
            )

        # ====================================================
        # NILAI SILHOUETTE
        # ====================================================

        if hasil_terbaru is not None:

            silhouette_kmeans = (
                hasil_terbaru.get(
                    "silhouette_terbaik_kmeans"
                )
            )

            silhouette_kmedoids = (
                hasil_terbaru.get(
                    "silhouette_terbaik_kmedoids"
                )
            )

            col12, col13 = (
                st.columns(2)
            )

            with col12:

                if silhouette_kmeans is not None:

                    nilai_kmeans = (
                        f"{float(silhouette_kmeans):.4f}"
                    )

                else:

                    nilai_kmeans = "-"

                st.metric(
                    "Silhouette K-Means",
                    nilai_kmeans,
                )

            with col13:

                if silhouette_kmedoids is not None:

                    nilai_kmedoids = (
                        f"{float(silhouette_kmedoids):.4f}"
                    )

                else:

                    nilai_kmedoids = "-"

                st.metric(
                    "Silhouette K-Medoids",
                    nilai_kmedoids,
                )

        # ====================================================
        # INFORMASI WAKTU DAN DATASET
        # ====================================================

        tanggal = (
            proses_terbaru.get(
                "tanggal_proses"
            )
        )

        if tanggal is not None:

            if hasattr(
                tanggal,
                "strftime",
            ):

                tanggal_teks = (
                    tanggal.strftime(
                        "%d-%m-%Y %H:%M:%S"
                    )
                )

            else:

                tanggal_teks = str(
                    tanggal
                )

        else:

            tanggal_teks = "-"

        nama_dataset = (
            proses_terbaru.get(
                "nama_dataset",
                "-",
            )
        )

        nama_pemroses = (
            proses_terbaru.get(
                "nama_pengguna",
                "-",
            )
        )

        success_card(
            "Riwayat Tersedia",
            (
                "Proses clustering terbaru tersimpan "
                "di PostgreSQL. "
                f"Dataset: {nama_dataset}. "
                f"Diproses oleh {nama_pemroses} "
                f"pada {tanggal_teks}. "
                "Hasil lengkap dapat dilihat melalui "
                "menu Hasil dan Perbandingan."
            ),
        )

    # ========================================================
    # RIWAYAT BELUM TERSEDIA
    # ========================================================

    else:

        warning_card(
            "Riwayat Belum Tersedia",
            (
                "Belum terdapat proses clustering "
                "yang tersimpan di PostgreSQL."
            ),
        )