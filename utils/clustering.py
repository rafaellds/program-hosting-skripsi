import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn_extra.cluster import KMedoids

from utils.preprocessing import preprocessing_data


def ambil_data_valid(df, fitur):
    """
    Fungsi ini digunakan untuk mengambil kembali data siswa
    yang memenuhi ketentuan preprocessing.

    Data valid diperlukan agar label cluster dapat digabungkan
    dengan identitas siswa yang sesuai.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Data yang diproses harus berupa pandas DataFrame."
        )

    data = df.copy()

    # Menghapus spasi yang tidak diperlukan pada nama kolom.
    data.columns = data.columns.astype(str).str.strip()

    # Memastikan seluruh atribut clustering tersedia.
    kolom_tidak_ditemukan = [
        kolom
        for kolom in fitur
        if kolom not in data.columns
    ]

    if kolom_tidak_ditemukan:
        raise ValueError(
            "Dataset tidak memiliki kolom berikut: "
            + ", ".join(kolom_tidak_ditemukan)
        )

    # Mengubah seluruh atribut clustering menjadi numerik.
    data_numerik = data[fitur].apply(
        pd.to_numeric,
        errors="coerce",
    )

    # Mengubah nilai tak terhingga menjadi nilai kosong.
    data_numerik = data_numerik.replace(
        [float("inf"), float("-inf")],
        pd.NA,
    )

    # Memeriksa baris yang tidak memiliki nilai kosong.
    kondisi_tidak_kosong = data_numerik.notna().all(axis=1)

    # Memeriksa seluruh nilai berada pada rentang 1 sampai 100.
    kondisi_minimum = data_numerik.ge(1).all(axis=1)
    kondisi_maksimum = data_numerik.le(100).all(axis=1)

    kondisi_valid = (
        kondisi_tidak_kosong
        & kondisi_minimum
        & kondisi_maksimum
    )

    # Mengambil data siswa yang memenuhi seluruh ketentuan.
    data_valid = data.loc[kondisi_valid].copy()

    # Menyamakan nilai numerik pada data hasil dengan data
    # yang telah diperiksa.
    data_valid.loc[:, fitur] = data_numerik.loc[
        kondisi_valid,
        fitur,
    ]

    # Mengatur ulang indeks agar sesuai dengan urutan label cluster.
    data_valid = data_valid.reset_index(drop=True)

    return data_valid


def proses_clustering(df):
    """
    Fungsi ini digunakan untuk menjalankan proses clustering
    menggunakan K-Means dan K-Medoids.

    Proses dilakukan dengan menguji jumlah cluster dari k=2
    sampai k=5, menghitung nilai Silhouette Coefficient,
    menentukan nilai k terbaik, dan membentuk model akhir.
    """

    # Menjalankan preprocessing terhadap 14 atribut penilaian.
    (
        fitur,
        data_clustering,
        data_normalisasi,
        df_normalisasi,
        scaler,
    ) = preprocessing_data(df)

    hasil_evaluasi = []

    # Menguji jumlah cluster dari k=2 sampai k=5.
    for k in range(2, 6):

        # Membentuk dan menjalankan model K-Means.
        kmeans = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10,
        )

        label_kmeans = kmeans.fit_predict(
            data_normalisasi
        )

        # Menghitung Silhouette Coefficient K-Means.
        silhouette_kmeans = silhouette_score(
            data_normalisasi,
            label_kmeans,
        )

        # Membentuk dan menjalankan model K-Medoids
        # menggunakan metode PAM.
        kmedoids = KMedoids(
            n_clusters=k,
            random_state=42,
            method="pam",
        )

        label_kmedoids = kmedoids.fit_predict(
            data_normalisasi
        )

        # Menghitung Silhouette Coefficient K-Medoids.
        silhouette_kmedoids = silhouette_score(
            data_normalisasi,
            label_kmedoids,
        )

        # Menyimpan hasil evaluasi setiap nilai k.
        hasil_evaluasi.append({
            "Jumlah Cluster (k)": k,
            "Silhouette K-Means": float(
                silhouette_kmeans
            ),
            "Silhouette K-Medoids": float(
                silhouette_kmedoids
            ),
        })

    # Mengubah hasil evaluasi menjadi DataFrame.
    df_evaluasi = pd.DataFrame(
        hasil_evaluasi
    )

    # Menentukan baris hasil terbaik K-Means.
    indeks_terbaik_kmeans = (
        df_evaluasi["Silhouette K-Means"].idxmax()
    )

    best_kmeans = df_evaluasi.loc[
        indeks_terbaik_kmeans
    ]

    # Menentukan baris hasil terbaik K-Medoids.
    indeks_terbaik_kmedoids = (
        df_evaluasi["Silhouette K-Medoids"].idxmax()
    )

    best_kmedoids = df_evaluasi.loc[
        indeks_terbaik_kmedoids
    ]

    # Mengambil nilai k terbaik untuk masing-masing algoritma.
    k_terbaik_kmeans = int(
        best_kmeans["Jumlah Cluster (k)"]
    )

    k_terbaik_kmedoids = int(
        best_kmedoids["Jumlah Cluster (k)"]
    )

    # Mengambil nilai Silhouette Coefficient terbaik.
    silhouette_terbaik_kmeans = float(
        best_kmeans["Silhouette K-Means"]
    )

    silhouette_terbaik_kmedoids = float(
        best_kmedoids["Silhouette K-Medoids"]
    )

    # Membentuk model akhir K-Means menggunakan k terbaik.
    model_kmeans = KMeans(
        n_clusters=k_terbaik_kmeans,
        random_state=42,
        n_init=10,
    )

    label_final_kmeans = model_kmeans.fit_predict(
        data_normalisasi
    )

    # Membentuk model akhir K-Medoids menggunakan k terbaik.
    model_kmedoids = KMedoids(
        n_clusters=k_terbaik_kmedoids,
        random_state=42,
        method="pam",
    )

    label_final_kmedoids = model_kmedoids.fit_predict(
        data_normalisasi
    )

    # Mengembalikan centroid K-Means dari skala normalisasi
    # ke skala nilai asli.
    centroid_kmeans = scaler.inverse_transform(
        model_kmeans.cluster_centers_
    )

    # Mengembalikan medoid K-Medoids dari skala normalisasi
    # ke skala nilai asli.
    medoid_kmedoids = scaler.inverse_transform(
        model_kmedoids.cluster_centers_
    )

    # Mengambil data siswa yang valid sesuai preprocessing.
    hasil_df = ambil_data_valid(
        df,
        fitur,
    )

    # Memastikan jumlah data sesuai dengan jumlah label cluster.
    if len(hasil_df) != len(data_clustering):
        raise ValueError(
            "Jumlah data siswa yang valid tidak sesuai "
            "dengan jumlah data clustering."
        )

    if len(hasil_df) != len(label_final_kmeans):
        raise ValueError(
            "Jumlah data siswa tidak sesuai dengan jumlah "
            "label cluster K-Means."
        )

    if len(hasil_df) != len(label_final_kmedoids):
        raise ValueError(
            "Jumlah data siswa tidak sesuai dengan jumlah "
            "label cluster K-Medoids."
        )

    # Menambahkan label cluster ke data siswa.
    hasil_df["cluster_kmeans"] = (
        label_final_kmeans.astype(int)
    )

    hasil_df["cluster_kmedoids"] = (
        label_final_kmedoids.astype(int)
    )

    return {
        "fitur": fitur,
        "data_clustering": data_clustering,
        "data_normalisasi": data_normalisasi,
        "df_normalisasi": df_normalisasi,
        "df_evaluasi": df_evaluasi,
        "hasil_df": hasil_df,
        "k_terbaik_kmeans": k_terbaik_kmeans,
        "k_terbaik_kmedoids": k_terbaik_kmedoids,
        "silhouette_terbaik_kmeans": (
            silhouette_terbaik_kmeans
        ),
        "silhouette_terbaik_kmedoids": (
            silhouette_terbaik_kmedoids
        ),
        "centroid_kmeans": centroid_kmeans,
        "medoid_kmedoids": medoid_kmedoids,
    }