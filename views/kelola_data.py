import numpy as np
import pandas as pd
import streamlit as st

from components import (
    page_header,
    section_title,
    info_card,
    success_card,
    error_card,
)

from utils.data_loader import load_default_dataset
from utils.database import simpan_dataset

from utils.preprocessing import (
    FITUR_CLUSTERING,
    FITUR_NONTEKNIS,
    FITUR_TEKNIS,
)


# ============================================================
# KOLOM YANG DIBUTUHKAN DATABASE
# ============================================================

KOLOM_DATABASE = [
    "tahun",
    "sumber_sheet",
    "nama_siswa",
    "nama_sekolah",
    "kompetensi_keahlian",
    "nisn",

    "nilai_kedisiplinan",
    "nilai_kerjasama",
    "nilai_inisiatif",
    "nilai_kerajinan",
    "nilai_tanggung_jawab",
    "nilai_sikap_perilaku",

    "nilai_ms_word",
    "nilai_ms_excel",
    "nilai_mikrotik",
    "nilai_kabel_lan",
    "nilai_fiber_optic",
    "nilai_hardware",
    "nilai_perakitan_cpu",
    "nilai_windows",

    "ratarata_nonteknis",
    "ratarata_teknis",
    "ratarata_keseluruhan",

    "kategori_nonteknis",
    "kategori_teknis",
    "kategori_keseluruhan",
]


# ============================================================
# PEMBERSIHAN DATASET
# ============================================================

def bersihkan_dataset(df):
    """
    Membersihkan format dasar dataset setelah dataset
    bawaan atau dataset upload dibaca.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Dataset yang dibaca harus berupa pandas DataFrame."
        )

    if df.empty:
        raise ValueError(
            "Dataset berhasil dibaca, tetapi tidak memiliki data."
        )

    data = df.copy()

    # Menghapus spasi pada nama kolom.
    data.columns = (
        data.columns
        .astype(str)
        .str.strip()
    )

    # Membersihkan format NISN apabila tersedia.
    if "nisn" in data.columns:
        data["nisn"] = (
            data["nisn"]
            .astype("string")
            .str.strip()
            .str.replace(
                r"\.0$",
                "",
                regex=True,
            )
            .str.zfill(10)
        )

    return data


# ============================================================
# PEMERIKSAAN DATASET UNTUK CLUSTERING
# ============================================================

def periksa_dataset(df):
    """
    Memeriksa kelengkapan dan validitas 14 atribut
    yang digunakan dalam proses clustering.
    """

    hasil_pemeriksaan = {
        "valid": False,
        "kolom_tidak_ditemukan": [],
        "jumlah_data_valid": 0,
        "jumlah_data_tidak_valid": len(df),
        "jumlah_nilai_kosong": 0,
        "jumlah_nilai_di_luar_rentang": 0,
    }

    # Memeriksa kelengkapan 14 atribut clustering.
    kolom_tidak_ditemukan = [
        kolom
        for kolom in FITUR_CLUSTERING
        if kolom not in df.columns
    ]

    hasil_pemeriksaan[
        "kolom_tidak_ditemukan"
    ] = kolom_tidak_ditemukan

    if kolom_tidak_ditemukan:
        return hasil_pemeriksaan

    # Mengubah 14 atribut menjadi numerik.
    data_fitur = df[FITUR_CLUSTERING].copy()

    data_fitur = data_fitur.apply(
        pd.to_numeric,
        errors="coerce",
    )

    # Mengubah nilai infinity menjadi kosong.
    data_fitur = data_fitur.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    # Menghitung nilai kosong.
    hasil_pemeriksaan["jumlah_nilai_kosong"] = int(
        data_fitur.isna().sum().sum()
    )

    # Setiap baris harus memiliki nilai lengkap.
    kondisi_tidak_kosong = (
        data_fitur.notna().all(axis=1)
    )

    # Semua nilai harus berada pada rentang 1–100.
    kondisi_rentang = (
        data_fitur.ge(1).all(axis=1)
        & data_fitur.le(100).all(axis=1)
    )

    kondisi_valid = (
        kondisi_tidak_kosong
        & kondisi_rentang
    )

    jumlah_data_valid = int(
        kondisi_valid.sum()
    )

    jumlah_data_tidak_valid = int(
        (~kondisi_valid).sum()
    )

    kondisi_di_luar_rentang = (
        data_fitur.lt(1)
        | data_fitur.gt(100)
    )

    jumlah_nilai_di_luar_rentang = int(
        kondisi_di_luar_rentang.sum().sum()
    )

    # Dataset dinyatakan valid untuk sistem hanya apabila
    # seluruh baris valid dan jumlah data mencukupi.
    dataset_valid = (
        jumlah_data_valid >= 6
        and jumlah_data_tidak_valid == 0
    )

    hasil_pemeriksaan.update({
        "valid": dataset_valid,
        "jumlah_data_valid": jumlah_data_valid,
        "jumlah_data_tidak_valid": (
            jumlah_data_tidak_valid
        ),
        "jumlah_nilai_di_luar_rentang": (
            jumlah_nilai_di_luar_rentang
        ),
    })

    return hasil_pemeriksaan


# ============================================================
# PEMERIKSAAN DATASET UNTUK DATABASE
# ============================================================

def periksa_kesiapan_database(df):
    """
    Memeriksa apakah dataset memiliki struktur yang
    diperlukan untuk disimpan ke PostgreSQL.
    """

    hasil = {
        "siap": False,
        "kolom_tidak_ditemukan": [],
        "nisn_duplikat": [],
        "nisn_tidak_valid": [],
    }

    # Memeriksa 26 kolom dataset.
    kolom_tidak_ditemukan = [
        kolom
        for kolom in KOLOM_DATABASE
        if kolom not in df.columns
    ]

    hasil[
        "kolom_tidak_ditemukan"
    ] = kolom_tidak_ditemukan

    if kolom_tidak_ditemukan:
        return hasil

    data = df.copy()

    # Menyeragamkan NISN.
    data["nisn"] = (
        data["nisn"]
        .astype("string")
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
        .str.zfill(10)
    )

    # Memeriksa NISN kosong atau tidak valid.
    kondisi_nisn_valid = (
        data["nisn"].notna()
        & data["nisn"].str.fullmatch(
            r"\d{10}",
            na=False,
        )
    )

    if not kondisi_nisn_valid.all():
        hasil["nisn_tidak_valid"] = (
            data.loc[
                ~kondisi_nisn_valid,
                "nisn",
            ]
            .astype(str)
            .tolist()
        )

    # Memeriksa NISN duplikat.
    kondisi_duplikat = data[
        "nisn"
    ].duplicated(
        keep=False
    )

    if kondisi_duplikat.any():
        hasil["nisn_duplikat"] = (
            data.loc[
                kondisi_duplikat,
                "nisn",
            ]
            .drop_duplicates()
            .tolist()
        )

    hasil["siap"] = (
        not hasil["kolom_tidak_ditemukan"]
        and not hasil["nisn_duplikat"]
        and not hasil["nisn_tidak_valid"]
    )

    return hasil


# ============================================================
# SESSION STATE
# ============================================================

def siapkan_session_state():
    """
    Menyiapkan session state yang digunakan
    pada halaman Kelola Data.
    """

    nilai_default = {
        "df": None,
        "hasil": None,
        "nama_dataset": None,
        "id_dataset": None,
        "id_penilaian_map": {},
        "dataset_tersimpan_db": False,
        "sedang_menyimpan_dataset": False,
        "id_proses": None,
    }

    for key, value in nilai_default.items():
        if key not in st.session_state:
            st.session_state[key] = value


def simpan_dataset_ke_session(
    df,
    nama_dataset,
):
    """
    Menyimpan dataset ke session state dan
    menghapus hasil proses sebelumnya.
    """

    st.session_state.df = df

    st.session_state.nama_dataset = (
        nama_dataset
    )

    # Dataset yang baru dimuat berarti hasil,
    # referensi database, dan ID proses sebelumnya
    # tidak berlaku lagi untuk dataset aktif.
    st.session_state.hasil = None
    st.session_state.id_dataset = None
    st.session_state.id_penilaian_map = {}
    st.session_state.dataset_tersimpan_db = False
    st.session_state.sedang_menyimpan_dataset = False
    st.session_state.id_proses = None


# ============================================================
# HALAMAN KELOLA DATA
# ============================================================

def halaman_kelola_data():
    """
    Fungsi utama halaman Kelola Data Penilaian.
    """

    siapkan_session_state()

    # --------------------------------------------------------
    # PEMBATASAN HAK AKSES
    # --------------------------------------------------------

    role = st.session_state.get(
        "role"
    )

    if role not in [
        "admin",
        "pengelola_pkl",
    ]:

        st.error(
            "Anda tidak memiliki hak akses "
            "untuk mengelola data penilaian."
        )

        return

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    page_header(
        "Kelola Data Penilaian",
        (
            "Menu untuk memuat, memeriksa, menyimpan, "
            "dan menampilkan dataset penilaian siswa PKL "
            "sebelum diproses."
        ),
    )

    info_card(
        "Fungsi Menu",
        (
            "Dataset harus memiliki 14 atribut penilaian, "
            "yang terdiri dari 6 atribut nonteknis dan "
            "8 atribut teknis. Seluruh atribut digunakan "
            "dalam proses clustering K-Means dan K-Medoids."
        ),
    )

    # --------------------------------------------------------
    # SUMBER DATASET
    # --------------------------------------------------------

    pilihan_data = st.radio(
        "Pilih sumber dataset:",
        [
            "Gunakan dataset bawaan",
            "Upload dataset baru",
        ],
    )

    # ========================================================
    # DATASET BAWAAN
    # ========================================================

    if pilihan_data == "Gunakan dataset bawaan":

        if st.button(
            "Muat Dataset Bawaan",
            use_container_width=True,
        ):

            try:

                df = load_default_dataset()

                df = bersihkan_dataset(
                    df
                )

                simpan_dataset_ke_session(
                    df=df,
                    nama_dataset=(
                        "dataset_final_14_atribut_"
                        "2021_2025.xlsx"
                    ),
                )

                st.success(
                    "Dataset bawaan berhasil dimuat."
                )

            except Exception as error:

                st.error(
                    f"Dataset gagal dimuat: {error}"
                )

    # ========================================================
    # DATASET UPLOAD
    # ========================================================

    else:

        uploaded_file = st.file_uploader(
            "Upload file Excel",
            type=["xlsx"],
        )

        if uploaded_file is not None:

            try:

                excel_file = pd.ExcelFile(
                    uploaded_file
                )

                sheet = st.selectbox(
                    "Pilih sheet:",
                    excel_file.sheet_names,
                )

                if st.button(
                    "Muat Dataset Upload",
                    use_container_width=True,
                ):

                    df = excel_file.parse(
                        sheet_name=sheet,
                        dtype={
                            "nisn": "string",
                        },
                    )

                    df = bersihkan_dataset(
                        df
                    )

                    simpan_dataset_ke_session(
                        df=df,
                        nama_dataset=(
                            uploaded_file.name
                        ),
                    )

                    st.success(
                        "Dataset upload berhasil dimuat."
                    )

            except Exception as error:

                st.error(
                    f"File upload gagal dibaca: {error}"
                )

    # ========================================================
    # DATASET BELUM DIMUAT
    # ========================================================

    if st.session_state.df is None:
        return

    # ========================================================
    # INFORMASI DATASET
    # ========================================================

    df = st.session_state.df

    hasil_pemeriksaan = (
        periksa_dataset(
            df
        )
    )

    kesiapan_database = (
        periksa_kesiapan_database(
            df
        )
    )

    section_title(
        "Informasi Dataset"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Jumlah Data",
            df.shape[0],
        )

    with col2:

        st.metric(
            "Jumlah Kolom",
            df.shape[1],
        )

    with col3:

        st.metric(
            "Data Valid",
            hasil_pemeriksaan[
                "jumlah_data_valid"
            ],
        )

    with col4:

        st.metric(
            "Data Tidak Valid",
            hasil_pemeriksaan[
                "jumlah_data_tidak_valid"
            ],
        )

    # ========================================================
    # HASIL VALIDASI CLUSTERING
    # ========================================================

    if hasil_pemeriksaan[
        "kolom_tidak_ditemukan"
    ]:

        daftar_kolom = ", ".join(
            hasil_pemeriksaan[
                "kolom_tidak_ditemukan"
            ]
        )

        error_card(
            "Dataset Belum Valid",
            (
                "Dataset belum memiliki seluruh atribut "
                "yang dibutuhkan. Kolom yang tidak "
                f"ditemukan: {daftar_kolom}."
            ),
        )

    elif hasil_pemeriksaan[
        "jumlah_data_valid"
    ] < 6:

        error_card(
            "Dataset Belum Valid",
            (
                "Jumlah data valid kurang dari 6 baris. "
                "Diperlukan minimal 6 data valid untuk "
                "pengujian jumlah cluster k=2 sampai k=5."
            ),
        )

    elif hasil_pemeriksaan[
        "jumlah_data_tidak_valid"
    ] > 0:

        error_card(
            "Dataset Belum Valid",
            (
                "Seluruh 14 atribut tersedia, tetapi terdapat "
                f"{hasil_pemeriksaan['jumlah_data_tidak_valid']} "
                "baris yang memiliki nilai kosong, bukan angka, "
                "atau berada di luar rentang 1 sampai 100. "
                "Data tersebut harus diperbaiki terlebih dahulu "
                "sebelum dataset dapat disimpan dan digunakan "
                "dalam proses clustering."
            ),
        )

    else:

        success_card(
            "Dataset Valid",
            (
                "Seluruh 14 atribut penilaian tersedia, "
                "seluruh data berada pada rentang nilai "
                "1 sampai 100, dan dataset dapat disimpan "
                "serta digunakan dalam proses clustering."
            ),
        )

    # ========================================================
    # RINCIAN MASALAH NILAI
    # ========================================================

    if hasil_pemeriksaan[
        "jumlah_nilai_kosong"
    ] > 0:

        st.warning(
            "Ditemukan "
            f"{hasil_pemeriksaan['jumlah_nilai_kosong']} "
            "nilai kosong atau nilai yang tidak dapat "
            "dibaca sebagai angka pada 14 atribut."
        )

    if hasil_pemeriksaan[
        "jumlah_nilai_di_luar_rentang"
    ] > 0:

        st.warning(
            "Ditemukan "
            f"{hasil_pemeriksaan['jumlah_nilai_di_luar_rentang']} "
            "nilai yang berada di luar rentang "
            "1 sampai 100."
        )

    # ========================================================
    # PENYIMPANAN DATABASE
    # ========================================================

    section_title(
        "Penyimpanan Database"
    )

    # Memeriksa struktur 26 kolom.
    if kesiapan_database[
        "kolom_tidak_ditemukan"
    ]:

        st.warning(
            "Dataset belum dapat disimpan ke database "
            "karena kolom berikut tidak ditemukan: "
            + ", ".join(
                kesiapan_database[
                    "kolom_tidak_ditemukan"
                ]
            )
        )

    # Memeriksa NISN tidak valid.
    elif kesiapan_database[
        "nisn_tidak_valid"
    ]:

        st.error(
            "Dataset belum dapat disimpan ke database "
            "karena terdapat NISN yang tidak valid."
        )

    # Memeriksa NISN duplikat.
    elif kesiapan_database[
        "nisn_duplikat"
    ]:

        st.error(
            "Dataset belum dapat disimpan ke database "
            "karena ditemukan NISN duplikat: "
            + ", ".join(
                kesiapan_database[
                    "nisn_duplikat"
                ]
            )
        )

    # Semua data penilaian harus valid.
    elif hasil_pemeriksaan[
        "jumlah_data_tidak_valid"
    ] > 0:

        st.warning(
            "Dataset belum dapat disimpan ke database "
            "karena masih memiliki data penilaian "
            "yang tidak valid. Perbaiki data terlebih "
            "dahulu dan muat kembali dataset."
        )

    # Dataset sudah tersimpan.
    elif st.session_state[
        "dataset_tersimpan_db"
    ]:

        success_card(
            "Dataset Tersimpan",
            (
                "Dataset telah berhasil disimpan "
                "ke PostgreSQL dengan ID Dataset "
                f"{st.session_state.id_dataset}."
            ),
        )

    # Dataset siap disimpan.
    else:

        st.write(
            "Dataset telah memenuhi struktur dan "
            "validasi yang dibutuhkan serta siap "
            "disimpan ke database."
        )

        tombol_simpan = st.button(
            "Simpan Dataset ke Database",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.get(
                "sedang_menyimpan_dataset",
                False,
            ),
        )

        if tombol_simpan:

            id_pengguna = (
                st.session_state.get(
                    "id_pengguna"
                )
            )

            if id_pengguna is None:

                st.error(
                    "ID pengguna tidak ditemukan. "
                    "Silakan login kembali."
                )

            else:

                # Status ini mencegah proses simpan dipanggil ulang
                # selama penyimpanan yang sama masih berlangsung.
                st.session_state[
                    "sedang_menyimpan_dataset"
                ] = True

                try:

                    with st.spinner(
                        "Menyimpan dataset ke database..."
                    ):

                        hasil_simpan = (
                            simpan_dataset(
                                df=df,
                                id_pengguna=id_pengguna,
                                nama_dataset=(
                                    st.session_state[
                                        "nama_dataset"
                                    ]
                                ),
                                sumber_data=(
                                    "PT FNI Teknologi Digital"
                                ),
                            )
                        )

                    st.session_state[
                        "id_dataset"
                    ] = hasil_simpan[
                        "id_dataset"
                    ]

                    st.session_state[
                        "id_penilaian_map"
                    ] = hasil_simpan[
                        "id_penilaian_map"
                    ]

                    st.session_state[
                        "dataset_tersimpan_db"
                    ] = True

                    if hasil_simpan.get(
                        "sudah_ada",
                        False,
                    ):
                        st.info(
                            "Dataset yang sama sudah tersedia "
                            "di PostgreSQL. Sistem menggunakan "
                            f"ID Dataset: {hasil_simpan['id_dataset']} "
                            "tanpa membuat salinan baru."
                        )
                    else:
                        st.success(
                            "Dataset berhasil disimpan "
                            "ke PostgreSQL. "
                            f"ID Dataset: "
                            f"{hasil_simpan['id_dataset']}. "
                            f"Jumlah data: "
                            f"{hasil_simpan['jumlah_data']}."
                        )

                except Exception as error:

                    st.error(
                        "Dataset gagal disimpan "
                        f"ke database: {error}"
                    )

                finally:
                    st.session_state[
                        "sedang_menyimpan_dataset"
                    ] = False

    # ========================================================
    # PREVIEW DATASET
    # ========================================================

    section_title(
        "Preview Dataset"
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    # ========================================================
    # DAFTAR ATRIBUT CLUSTERING
    # ========================================================

    with st.expander(
        "Lihat daftar atribut clustering"
    ):

        st.markdown(
            "**Atribut Nonteknis (6 atribut):**"
        )

        for nomor, kolom in enumerate(
            FITUR_NONTEKNIS,
            start=1,
        ):

            st.write(
                f"{nomor}. {kolom}"
            )

        st.markdown(
            "**Atribut Teknis (8 atribut):**"
        )

        for nomor, kolom in enumerate(
            FITUR_TEKNIS,
            start=1,
        ):

            st.write(
                f"{nomor}. {kolom}"
            )

    # ========================================================
    # SELURUH KOLOM DATASET
    # ========================================================

    with st.expander(
        "Lihat seluruh kolom dataset"
    ):

        st.write(
            df.columns.tolist()
        )