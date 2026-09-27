import pandas as pd
from sklearn.preprocessing import MinMaxScaler


# Enam atribut penilaian nonteknis sesuai sertifikat PKL.
FITUR_NONTEKNIS = [
    "nilai_kedisiplinan",
    "nilai_kerjasama",
    "nilai_inisiatif",
    "nilai_kerajinan",
    "nilai_tanggung_jawab",
    "nilai_sikap_perilaku",
]


# Delapan atribut penilaian teknis sesuai sertifikat PKL.
FITUR_TEKNIS = [
    "nilai_ms_word",
    "nilai_ms_excel",
    "nilai_mikrotik",
    "nilai_kabel_lan",
    "nilai_fiber_optic",
    "nilai_hardware",
    "nilai_perakitan_cpu",
    "nilai_windows",
]


# Seluruh atribut yang digunakan dalam proses clustering.
FITUR_CLUSTERING = FITUR_NONTEKNIS + FITUR_TEKNIS


def preprocessing_data(df):
    """
    Fungsi ini digunakan untuk mengambil 14 atribut clustering,
    mengubah data menjadi numerik, memeriksa nilai kosong,
    memeriksa rentang nilai, dan melakukan normalisasi
    menggunakan MinMaxScaler.

    Parameter:
        df (pandas.DataFrame):
            Dataset penilaian siswa PKL.

    Return:
        fitur:
            Daftar 14 atribut yang digunakan untuk clustering.

        data_clustering:
            Data sebelum normalisasi yang hanya berisi
            14 atribut clustering.

        data_normalisasi:
            Data hasil normalisasi dalam bentuk array NumPy.

        df_normalisasi:
            Data hasil normalisasi dalam bentuk DataFrame.

        scaler:
            Objek MinMaxScaler yang telah digunakan.
    """

    # Memastikan data yang diterima berupa DataFrame.
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Data yang diproses harus berupa pandas DataFrame."
        )

    # Memastikan dataset tidak kosong.
    if df.empty:
        raise ValueError(
            "Dataset masih kosong dan belum dapat diproses."
        )

    # Membuat salinan agar data asli tidak berubah.
    data = df.copy()

    # Menghapus spasi yang tidak diperlukan pada nama kolom.
    data.columns = data.columns.astype(str).str.strip()

    # Memeriksa apakah seluruh atribut clustering tersedia.
    kolom_tidak_ditemukan = [
        kolom
        for kolom in FITUR_CLUSTERING
        if kolom not in data.columns
    ]

    if kolom_tidak_ditemukan:
        raise ValueError(
            "Dataset tidak memiliki kolom berikut: "
            + ", ".join(kolom_tidak_ditemukan)
        )

    # Mengambil 14 atribut yang digunakan untuk clustering.
    data_clustering = data[FITUR_CLUSTERING].copy()

    # Mengubah seluruh nilai atribut menjadi numerik.
    # Nilai yang tidak dapat dikonversi akan menjadi NaN.
    data_clustering = data_clustering.apply(
        pd.to_numeric,
        errors="coerce",
    )

    # Mengubah nilai tak terhingga menjadi nilai kosong.
    data_clustering = data_clustering.replace(
        [float("inf"), float("-inf")],
        pd.NA,
    )

    # Menghapus baris yang masih memiliki nilai kosong.
    data_clustering = data_clustering.dropna(
        subset=FITUR_CLUSTERING
    )

    # Memastikan seluruh nilai berada pada rentang 1 sampai 100.
    kondisi_minimum = data_clustering.ge(1).all(axis=1)
    kondisi_maksimum = data_clustering.le(100).all(axis=1)

    data_clustering = data_clustering.loc[
        kondisi_minimum & kondisi_maksimum
    ]

    # Mengatur ulang indeks setelah proses pembersihan.
    data_clustering = data_clustering.reset_index(drop=True)

    # K-Means dan K-Medoids diuji sampai k=5.
    # Oleh karena itu, jumlah data minimal harus lebih dari 5.
    if len(data_clustering) < 6:
        raise ValueError(
            "Jumlah data valid tidak mencukupi. "
            "Diperlukan minimal 6 data untuk pengujian k=2 sampai k=5."
        )

    # Membuat objek MinMaxScaler.
    scaler = MinMaxScaler()

    # Melakukan normalisasi seluruh 14 atribut ke rentang 0 sampai 1.
    data_normalisasi = scaler.fit_transform(
        data_clustering
    )

    # Mengubah hasil normalisasi menjadi DataFrame.
    df_normalisasi = pd.DataFrame(
        data_normalisasi,
        columns=FITUR_CLUSTERING,
        index=data_clustering.index,
    )

    return (
        FITUR_CLUSTERING.copy(),
        data_clustering,
        data_normalisasi,
        df_normalisasi,
        scaler,
    )