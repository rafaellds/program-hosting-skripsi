import pandas as pd
import streamlit as st

from components import (
    page_header,
    section_title,
    info_card,
    success_card,
    warning_card,
)

from utils.clustering import proses_clustering
from utils.database import (
    simpan_proses_clustering,
)

from utils.preprocessing import (
    FITUR_CLUSTERING,
    FITUR_NONTEKNIS,
    FITUR_TEKNIS,
)


def halaman_proses():
    """
    Menampilkan halaman proses clustering
    dan evaluasi.
    """

    # ========================================================
    # SESSION STATE
    # ========================================================

    if "df" not in st.session_state:
        st.session_state.df = None

    if "hasil" not in st.session_state:
        st.session_state.hasil = None

    if "id_proses" not in st.session_state:
        st.session_state.id_proses = None

    # ========================================================
    # HAK AKSES
    # ========================================================

    role = st.session_state.get(
        "role"
    )

    if role not in [
        "admin",
        "pengelola_pkl",
    ]:
        st.error(
            "Anda tidak memiliki hak akses "
            "untuk menjalankan proses clustering."
        )
        return

    # ========================================================
    # HEADER
    # ========================================================

    page_header(
        "Proses Clustering dan Evaluasi",
        (
            "Menu untuk menjalankan preprocessing, "
            "normalisasi, K-Means, K-Medoids, "
            "dan evaluasi Silhouette Coefficient."
        ),
    )

    # ========================================================
    # DATASET BELUM DIMUAT
    # ========================================================

    if st.session_state.df is None:

        warning_card(
            "Dataset Belum Dimuat",
            (
                "Silakan buka menu Kelola Data Penilaian "
                "terlebih dahulu sebelum menjalankan "
                "proses clustering."
            ),
        )

        return

    # ========================================================
    # DATASET BELUM DISIMPAN KE DATABASE
    # ========================================================

    id_dataset = st.session_state.get(
        "id_dataset"
    )

    if id_dataset is None:

        warning_card(
            "Dataset Belum Disimpan",
            (
                "Dataset telah dimuat, tetapi belum "
                "disimpan ke database. Silakan buka "
                "menu Kelola Data Penilaian dan pilih "
                "Simpan Dataset ke Database terlebih dahulu."
            ),
        )

        return

    df = st.session_state.df

    # ========================================================
    # INFORMASI ATRIBUT
    # ========================================================

    info_card(
        "Atribut yang Digunakan",
        (
            "Proses clustering menggunakan 14 atribut "
            "penilaian, yang terdiri dari 6 atribut "
            "nonteknis dan 8 atribut teknis. "
            "Seluruh atribut dinormalisasi menggunakan "
            "MinMaxScaler sebelum diproses oleh "
            "algoritma K-Means dan K-Medoids."
        ),
    )

    # ========================================================
    # INFORMASI DATASET
    # ========================================================

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:
        st.metric(
            "Jumlah Data Awal",
            df.shape[0],
        )

    with col2:
        st.metric(
            "Jumlah Kolom",
            df.shape[1],
        )

    with col3:
        st.metric(
            "Atribut Clustering",
            len(FITUR_CLUSTERING),
        )

    with col4:
        st.metric(
            "Rentang k Diuji",
            "2 - 5",
        )

    st.caption(
        f"ID Dataset PostgreSQL: {id_dataset}"
    )

    # ========================================================
    # ATRIBUT CLUSTERING
    # ========================================================

    with st.expander(
        "Lihat atribut yang digunakan "
        "dalam proses clustering"
    ):

        st.markdown(
            f"**Atribut Nonteknis "
            f"({len(FITUR_NONTEKNIS)} atribut):**"
        )

        for nomor, atribut in enumerate(
            FITUR_NONTEKNIS,
            start=1,
        ):
            st.write(
                f"{nomor}. {atribut}"
            )

        st.markdown(
            f"**Atribut Teknis "
            f"({len(FITUR_TEKNIS)} atribut):**"
        )

        for nomor, atribut in enumerate(
            FITUR_TEKNIS,
            start=1,
        ):
            st.write(
                f"{nomor}. {atribut}"
            )

    # ========================================================
    # PROSES CLUSTERING
    # ========================================================

    if st.button(
        "Mulai Proses Clustering dan Evaluasi",
        use_container_width=True,
        type="primary",
    ):

        try:

            id_pengguna = (
                st.session_state.get(
                    "id_pengguna"
                )
            )

            if id_pengguna is None:
                raise ValueError(
                    "ID pengguna tidak ditemukan. "
                    "Silakan login kembali."
                )

            with st.spinner(
                "Proses clustering dan evaluasi "
                "sedang dijalankan..."
            ):

                # --------------------------------------------
                # Menjalankan clustering
                # --------------------------------------------

                hasil = proses_clustering(
                    df
                )

                # --------------------------------------------
                # Menyimpan proses ke database
                # --------------------------------------------

                hasil_database = (
                    simpan_proses_clustering(
                        hasil=hasil,
                        id_dataset=id_dataset,
                        id_pengguna=id_pengguna,
                    )
                )

            # -----------------------------------------------
            # Menyimpan hasil ke session
            # -----------------------------------------------

            st.session_state.hasil = (
                hasil
            )

            st.session_state.id_proses = (
                hasil_database[
                    "id_proses"
                ]
            )

            st.success(
                "Proses clustering dan evaluasi "
                "berhasil dilakukan dan disimpan "
                "ke PostgreSQL. "
                f"ID Proses: "
                f"{hasil_database['id_proses']}."
            )

        except Exception as error:

            st.session_state.hasil = None
            st.session_state.id_proses = None

            st.error(
                "Proses clustering gagal "
                f"dijalankan: {error}"
            )

    # ========================================================
    # HASIL BELUM ADA
    # ========================================================

    if st.session_state.hasil is None:
        return

    hasil = st.session_state.hasil

    # ========================================================
    # HASIL PREPROCESSING
    # ========================================================

    section_title(
        "Hasil Preprocessing"
    )

    col5, col6, col7 = (
        st.columns(3)
    )

    with col5:
        st.metric(
            "Data Sebelum Preprocessing",
            df.shape[0],
        )

    with col6:
        st.metric(
            "Data Setelah Preprocessing",
            hasil[
                "data_clustering"
            ].shape[0],
        )

    with col7:
        st.metric(
            "Atribut Clustering",
            len(
                hasil["fitur"]
            ),
        )

    st.caption(
        "Tabel berikut menampilkan 14 atribut "
        "penilaian yang digunakan dalam proses "
        "clustering sebelum normalisasi."
    )

    st.dataframe(
        hasil["data_clustering"],
        use_container_width=True,
        hide_index=True,
    )

    # ========================================================
    # NORMALISASI
    # ========================================================

    section_title(
        "Data Setelah Normalisasi MinMaxScaler"
    )

    st.caption(
        "Setiap atribut dinormalisasi ke rentang "
        "0 sampai 1 agar memiliki skala "
        "yang sebanding."
    )

    df_normalisasi_tampil = (
        hasil[
            "df_normalisasi"
        ]
        .copy()
        .round(4)
    )

    st.dataframe(
        df_normalisasi_tampil,
        use_container_width=True,
        hide_index=True,
    )

    # ========================================================
    # EVALUASI SILHOUETTE
    # ========================================================

    section_title(
        "Hasil Evaluasi Silhouette Coefficient"
    )

    df_evaluasi_tampil = (
        hasil[
            "df_evaluasi"
        ].copy()
    )

    kolom_silhouette = [
        "Silhouette K-Means",
        "Silhouette K-Medoids",
    ]

    for kolom in kolom_silhouette:

        if (
            kolom
            in df_evaluasi_tampil.columns
        ):

            df_evaluasi_tampil[
                kolom
            ] = (
                pd.to_numeric(
                    df_evaluasi_tampil[
                        kolom
                    ],
                    errors="coerce",
                )
                .round(4)
            )

    st.dataframe(
        df_evaluasi_tampil,
        use_container_width=True,
        hide_index=True,
    )

    # ========================================================
    # NILAI TERBAIK
    # ========================================================

    col8, col9 = st.columns(2)

    with col8:

        st.metric(
            "k Terbaik K-Means",
            hasil[
                "k_terbaik_kmeans"
            ],
            help=(
                "Nilai k dengan Silhouette "
                "Coefficient tertinggi "
                "pada K-Means."
            ),
        )

        st.metric(
            "Silhouette Terbaik K-Means",
            (
                f"{hasil['silhouette_terbaik_kmeans']:.4f}"
            ),
        )

    with col9:

        st.metric(
            "k Terbaik K-Medoids",
            hasil[
                "k_terbaik_kmedoids"
            ],
            help=(
                "Nilai k dengan Silhouette "
                "Coefficient tertinggi "
                "pada K-Medoids."
            ),
        )

        st.metric(
            "Silhouette Terbaik K-Medoids",
            (
                f"{hasil['silhouette_terbaik_kmedoids']:.4f}"
            ),
        )

    # ========================================================
    # INFORMASI DATABASE
    # ========================================================

    if st.session_state.id_proses is not None:

        success_card(
            "Proses Berhasil",
            (
                "Hasil clustering dan evaluasi telah "
                "disimpan ke PostgreSQL dengan "
                f"ID Proses "
                f"{st.session_state.id_proses}. "
                "Silakan buka menu Hasil dan "
                "Perbandingan untuk melihat hasil "
                "K-Means, K-Medoids, visualisasi "
                "cluster, serta perbandingan "
                "kedua algoritma."
            ),
        )