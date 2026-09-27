import numpy as np
import pandas as pd
import streamlit as st

from components import (
    page_header,
    section_title,
    info_card,
    success_card,
    warning_card,
)
from utils.preprocessing import (
    FITUR_CLUSTERING,
    FITUR_NONTEKNIS,
    FITUR_TEKNIS,
)
from utils.visualisasi import tampilkan_scatter_plot
from utils.database import (
    ambil_daftar_proses,
    ambil_hasil_proses,
)

from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import MinMaxScaler


def buat_ringkasan_jumlah(hasil_df, kolom_cluster, nama_cluster):
    """
    Fungsi ini digunakan untuk menghitung jumlah anggota
    pada setiap cluster.
    """
    ringkasan = (
        hasil_df[kolom_cluster]
        .value_counts()
        .sort_index()
        .rename_axis(nama_cluster)
        .reset_index(name="Jumlah Data")
    )

    return ringkasan


def tentukan_kategori_performa(nilai_rata_rata):
    """
    Fungsi ini digunakan untuk memberikan kategori performa
    berdasarkan urutan rata-rata keseluruhan setiap cluster.

    Kategori yang diberikan bersifat relatif terhadap cluster
    lain dalam dataset yang sama.
    """
    jumlah_cluster = len(nilai_rata_rata)

    daftar_kategori = {
        2: [
            "Relatif Rendah",
            "Relatif Tinggi",
        ],
        3: [
            "Relatif Rendah",
            "Relatif Sedang",
            "Relatif Tinggi",
        ],
        4: [
            "Relatif Terendah",
            "Relatif Menengah Bawah",
            "Relatif Menengah Atas",
            "Relatif Tertinggi",
        ],
        5: [
            "Relatif Terendah",
            "Relatif Rendah",
            "Relatif Sedang",
            "Relatif Tinggi",
            "Relatif Tertinggi",
        ],
    }

    kategori = daftar_kategori.get(
        jumlah_cluster,
        [
            f"Peringkat Performa {nomor}"
            for nomor in range(1, jumlah_cluster + 1)
        ],
    )

    # Mengurutkan cluster dari rata-rata terendah ke tertinggi.
    indeks_terurut = nilai_rata_rata.sort_values().index

    hasil_kategori = pd.Series(
        index=nilai_rata_rata.index,
        dtype="string",
    )

    for indeks, nama_kategori in zip(
        indeks_terurut,
        kategori,
    ):
        hasil_kategori.loc[indeks] = nama_kategori

    return hasil_kategori


def buat_karakteristik_cluster(
    hasil_df,
    kolom_cluster,
    fitur,
):
    """
    Fungsi ini digunakan untuk menghitung rata-rata setiap
    atribut pada masing-masing cluster.

    Selain 14 atribut, fungsi juga menghitung rata-rata kelompok
    atribut nonteknis, teknis, dan keseluruhan untuk mempermudah
    interpretasi hasil.
    """

    # Memastikan seluruh atribut tersedia.
    kolom_tidak_ditemukan = [
        kolom
        for kolom in fitur
        if kolom not in hasil_df.columns
    ]

    if kolom_tidak_ditemukan:
        raise ValueError(
            "Kolom atribut berikut tidak ditemukan: "
            + ", ".join(kolom_tidak_ditemukan)
        )

    if kolom_cluster not in hasil_df.columns:
        raise ValueError(
            f"Kolom {kolom_cluster} tidak ditemukan."
        )

    data_profil = hasil_df[
        [kolom_cluster] + fitur
    ].copy()

    # Memastikan seluruh atribut berbentuk numerik.
    data_profil[fitur] = data_profil[fitur].apply(
        pd.to_numeric,
        errors="coerce",
    )

    if data_profil[fitur].isna().any().any():
        raise ValueError(
            "Data profil cluster masih memiliki nilai kosong "
            "atau nilai yang tidak dapat dibaca sebagai angka."
        )

    # Menghitung jumlah anggota setiap cluster.
    jumlah_anggota = (
        data_profil
        .groupby(kolom_cluster)
        .size()
        .reset_index(name="jumlah_data")
    )

    # Menghitung rata-rata 14 atribut setiap cluster.
    karakteristik = (
        data_profil
        .groupby(kolom_cluster, as_index=False)[fitur]
        .mean()
    )

    karakteristik = jumlah_anggota.merge(
        karakteristik,
        on=kolom_cluster,
        how="left",
    )

    # Menghitung rata-rata enam atribut nonteknis.
    karakteristik["rata_rata_nonteknis"] = (
        karakteristik[FITUR_NONTEKNIS]
        .mean(axis=1)
    )

    # Menghitung rata-rata delapan atribut teknis.
    karakteristik["rata_rata_teknis"] = (
        karakteristik[FITUR_TEKNIS]
        .mean(axis=1)
    )

    # Menghitung rata-rata seluruh 14 atribut.
    karakteristik["rata_rata_keseluruhan"] = (
        karakteristik[fitur]
        .mean(axis=1)
    )

    # Memberikan kategori performa relatif.
    karakteristik["kategori_performa"] = (
        tentukan_kategori_performa(
            karakteristik["rata_rata_keseluruhan"]
        )
    )

    # Mengatur urutan kolom agar ringkasan mudah dibaca.
    kolom_awal = [
        kolom_cluster,
        "jumlah_data",
        "rata_rata_nonteknis",
        "rata_rata_teknis",
        "rata_rata_keseluruhan",
        "kategori_performa",
    ]

    karakteristik = karakteristik[
        kolom_awal + fitur
    ]

    return karakteristik


def buat_teks_interpretasi(
    karakteristik,
    kolom_cluster,
    nama_algoritma,
):
    """
    Fungsi ini digunakan untuk membuat interpretasi singkat
    berdasarkan rata-rata keseluruhan cluster tertinggi dan
    cluster terendah.
    """
    indeks_tertinggi = (
        karakteristik["rata_rata_keseluruhan"].idxmax()
    )

    indeks_terendah = (
        karakteristik["rata_rata_keseluruhan"].idxmin()
    )

    cluster_tertinggi = karakteristik.loc[
        indeks_tertinggi
    ]

    cluster_terendah = karakteristik.loc[
        indeks_terendah
    ]

    jumlah_cluster = len(karakteristik)

    teks = (
        f"Pada hasil {nama_algoritma}, Cluster "
        f"{int(cluster_tertinggi[kolom_cluster])} memiliki "
        f"rata-rata nonteknis sebesar "
        f"{cluster_tertinggi['rata_rata_nonteknis']:.2f}, "
        f"rata-rata teknis sebesar "
        f"{cluster_tertinggi['rata_rata_teknis']:.2f}, dan "
        f"rata-rata keseluruhan sebesar "
        f"{cluster_tertinggi['rata_rata_keseluruhan']:.2f}. "
        f"Cluster tersebut merupakan kelompok dengan performa "
        f"relatif tertinggi dan memiliki "
        f"{int(cluster_tertinggi['jumlah_data'])} anggota. "
        f"Sementara itu, Cluster "
        f"{int(cluster_terendah[kolom_cluster])} memiliki "
        f"rata-rata keseluruhan sebesar "
        f"{cluster_terendah['rata_rata_keseluruhan']:.2f}, "
        f"sehingga menjadi kelompok dengan performa relatif "
        f"terendah dan memiliki "
        f"{int(cluster_terendah['jumlah_data'])} anggota."
    )

    if jumlah_cluster > 2:
        teks += (
            " Cluster lainnya berada di antara kedua kelompok "
            "tersebut berdasarkan urutan rata-rata keseluruhan "
            "14 atribut penilaian."
        )

    return teks



def hitung_centroid_dari_hasil(hasil_df, fitur):
    """
    Menghitung kembali centroid K-Means berdasarkan
    anggota cluster yang tersimpan di database.
    """
    return (
        hasil_df
        .groupby("cluster_kmeans")[fitur]
        .mean()
        .sort_index()
        .to_numpy(dtype=float)
    )


def hitung_medoid_dari_hasil(hasil_df, fitur):
    """
    Menghitung kembali medoid setiap cluster K-Medoids
    berdasarkan anggota cluster yang tersimpan di database.

    Perhitungan dilakukan pada data hasil MinMaxScaler agar
    konsisten dengan proses clustering utama.
    """
    data_nilai = hasil_df[fitur].apply(
        pd.to_numeric,
        errors="coerce",
    )

    if data_nilai.isna().any().any():
        raise ValueError(
            "Data hasil masih memiliki nilai kosong atau nilai "
            "yang tidak dapat dibaca sebagai angka."
        )

    scaler = MinMaxScaler()
    data_normalisasi = scaler.fit_transform(
        data_nilai
    )

    label = pd.to_numeric(
        hasil_df["cluster_kmedoids"],
        errors="raise",
    ).astype(int).to_numpy()

    daftar_medoid = []

    for nomor_cluster in sorted(np.unique(label)):
        indeks_cluster = np.where(
            label == nomor_cluster
        )[0]

        data_cluster = data_normalisasi[
            indeks_cluster
        ]

        matriks_jarak = pairwise_distances(
            data_cluster,
            metric="euclidean",
        )

        indeks_medoid_lokal = int(
            np.argmin(
                matriks_jarak.sum(axis=1)
            )
        )

        indeks_medoid_global = int(
            indeks_cluster[
                indeks_medoid_lokal
            ]
        )

        daftar_medoid.append(
            data_nilai.iloc[
                indeks_medoid_global
            ].to_numpy(dtype=float)
        )

    return np.asarray(
        daftar_medoid,
        dtype=float,
    )


def lengkapi_hasil_database(hasil_database):
    """
    Melengkapi data hasil yang dibaca dari PostgreSQL agar
    memiliki struktur yang sama dengan output proses_clustering().
    """
    hasil = dict(hasil_database)

    hasil_df = hasil[
        "hasil_df"
    ].copy()

    if hasil_df.empty:
        raise ValueError(
            "Hasil clustering pada database tidak memiliki data."
        )

    kolom_tidak_ditemukan = [
        kolom
        for kolom in FITUR_CLUSTERING
        if kolom not in hasil_df.columns
    ]

    if kolom_tidak_ditemukan:
        raise ValueError(
            "Data hasil pada database belum memiliki atribut: "
            + ", ".join(kolom_tidak_ditemukan)
        )

    data_clustering = hasil_df[
        FITUR_CLUSTERING
    ].copy()

    hasil["fitur"] = list(
        FITUR_CLUSTERING
    )
    hasil["data_clustering"] = (
        data_clustering
    )
    hasil["centroid_kmeans"] = (
        hitung_centroid_dari_hasil(
            hasil_df,
            FITUR_CLUSTERING,
        )
    )
    hasil["medoid_kmedoids"] = (
        hitung_medoid_dari_hasil(
            hasil_df,
            FITUR_CLUSTERING,
        )
    )

    return hasil


def buat_label_riwayat(proses):
    """
    Membuat teks pilihan riwayat proses pada selectbox.
    """
    tanggal = proses.get(
        "tanggal_proses"
    )

    if hasattr(tanggal, "strftime"):
        tanggal_text = tanggal.strftime(
            "%d-%m-%Y %H:%M:%S"
        )
    else:
        tanggal_text = str(tanggal)

    return (
        f"ID Proses {proses['id_proses']} | "
        f"ID Dataset {proses['id_dataset']} | "
        f"{proses['nama_dataset']} | "
        f"{tanggal_text}"
    )

def halaman_hasil():
    """
    Fungsi utama untuk menampilkan halaman hasil dan
    perbandingan clustering.

    Hasil utama dibaca dari PostgreSQL sehingga riwayat proses
    tetap dapat ditampilkan setelah aplikasi ditutup atau dibuka
    kembali. Session state digunakan sebagai fallback apabila
    riwayat database belum tersedia.
    """

    if "hasil" not in st.session_state:
        st.session_state.hasil = None

    if "id_proses" not in st.session_state:
        st.session_state.id_proses = None

    page_header(
        "Hasil dan Perbandingan",
        (
            "Menu untuk menampilkan output clustering K-Means, "
            "output clustering K-Medoids, visualisasi, profil "
            "cluster, dan perbandingan nilai evaluasi."
        ),
    )

    hasil = None
    proses_terpilih = None

    # =========================================================
    # RIWAYAT PROSES DARI POSTGRESQL
    # =========================================================

    try:
        daftar_proses = ambil_daftar_proses()
    except Exception as error:
        daftar_proses = []
        st.warning(
            "Riwayat proses dari PostgreSQL belum dapat dibaca: "
            f"{error}"
        )

    if daftar_proses:
        section_title(
            "Riwayat Proses Clustering"
        )

        label_ke_proses = {
            buat_label_riwayat(proses): proses
            for proses in daftar_proses
        }

        daftar_label = list(
            label_ke_proses.keys()
        )

        indeks_default = 0
        id_proses_aktif = st.session_state.get(
            "id_proses"
        )

        if id_proses_aktif is not None:
            for indeks, label in enumerate(
                daftar_label
            ):
                proses = label_ke_proses[label]
                if (
                    proses["id_proses"]
                    == id_proses_aktif
                ):
                    indeks_default = indeks
                    break

        label_terpilih = st.selectbox(
            "Pilih riwayat proses yang ingin ditampilkan:",
            daftar_label,
            index=indeks_default,
        )

        proses_terpilih = label_ke_proses[
            label_terpilih
        ]

        try:
            hasil_database = ambil_hasil_proses(
                proses_terpilih["id_proses"]
            )

            hasil = lengkapi_hasil_database(
                hasil_database
            )

            st.caption(
                "Data hasil ditampilkan dari PostgreSQL. "
                f"ID Proses: {proses_terpilih['id_proses']} | "
                f"ID Dataset: {proses_terpilih['id_dataset']} | "
                f"Diproses oleh: {proses_terpilih['nama_pengguna']}"
            )

        except Exception as error:
            st.error(
                "Hasil proses gagal dibaca dari database: "
                f"{error}"
            )
            return

    elif st.session_state.hasil is not None:
        hasil = st.session_state.hasil

        info_card(
            "Sumber Hasil",
            (
                "Riwayat PostgreSQL belum tersedia. Hasil yang "
                "ditampilkan berasal dari sesi aplikasi yang aktif."
            ),
        )

    else:
        warning_card(
            "Hasil Belum Tersedia",
            (
                "Belum terdapat riwayat proses clustering pada "
                "database. Silakan jalankan proses pada menu Proses "
                "Clustering dan Evaluasi terlebih dahulu."
            ),
        )
        return

    # Memastikan hasil proses memiliki seluruh data yang dibutuhkan.
    kunci_wajib = [
        "hasil_df",
        "fitur",
        "data_clustering",
        "df_evaluasi",
        "k_terbaik_kmeans",
        "k_terbaik_kmedoids",
        "silhouette_terbaik_kmeans",
        "silhouette_terbaik_kmedoids",
        "centroid_kmeans",
        "medoid_kmedoids",
    ]

    kunci_tidak_ditemukan = [
        kunci
        for kunci in kunci_wajib
        if kunci not in hasil
    ]

    if kunci_tidak_ditemukan:
        st.error(
            "Hasil proses belum lengkap. Data berikut tidak "
            "ditemukan: "
            + ", ".join(kunci_tidak_ditemukan)
        )
        return

    hasil_df = hasil["hasil_df"].copy()
    fitur = hasil["fitur"]

    silhouette_kmeans = float(
        hasil["silhouette_terbaik_kmeans"]
    )

    silhouette_kmedoids = float(
        hasil["silhouette_terbaik_kmedoids"]
    )

    # =========================================================
    # PERBANDINGAN SILHOUETTE COEFFICIENT
    # =========================================================

    section_title(
        "Perbandingan Nilai Silhouette Coefficient"
    )

    selisih_silhouette = abs(
        silhouette_kmeans - silhouette_kmedoids
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Silhouette Terbaik K-Means",
            f"{silhouette_kmeans:.4f}",
        )

        st.caption(
            f"Jumlah cluster terbaik: "
            f"{hasil['k_terbaik_kmeans']}"
        )

    with col2:
        st.metric(
            "Silhouette Terbaik K-Medoids",
            f"{silhouette_kmedoids:.4f}",
        )

        st.caption(
            f"Jumlah cluster terbaik: "
            f"{hasil['k_terbaik_kmedoids']}"
        )

    with col3:
        st.metric(
            "Selisih Nilai",
            f"{selisih_silhouette:.4f}",
        )

    # Menentukan algoritma dengan nilai evaluasi tertinggi.
    if np.isclose(
        silhouette_kmeans,
        silhouette_kmedoids,
        atol=1e-12,
        rtol=0,
    ):
        success_card(
            "Hasil Algoritma Setara",
            (
                "K-Means dan K-Medoids memiliki nilai "
                "Silhouette Coefficient yang sama, yaitu "
                f"{silhouette_kmeans:.4f}."
            ),
        )

    elif silhouette_kmeans > silhouette_kmedoids:
        success_card(
            "Algoritma Terbaik",
            (
                "Berdasarkan nilai Silhouette Coefficient, "
                "algoritma K-Means memperoleh hasil lebih baik "
                f"dengan nilai {silhouette_kmeans:.4f}, "
                f"sedangkan K-Medoids memperoleh nilai "
                f"{silhouette_kmedoids:.4f}."
            ),
        )

    else:
        success_card(
            "Algoritma Terbaik",
            (
                "Berdasarkan nilai Silhouette Coefficient, "
                "algoritma K-Medoids memperoleh hasil lebih baik "
                f"dengan nilai {silhouette_kmedoids:.4f}, "
                f"sedangkan K-Means memperoleh nilai "
                f"{silhouette_kmeans:.4f}."
            ),
        )

    with st.expander(
        "Lihat hasil evaluasi untuk seluruh nilai k"
    ):
        df_evaluasi_tampil = (
            hasil["df_evaluasi"]
            .copy()
        )

        for kolom in [
            "Silhouette K-Means",
            "Silhouette K-Medoids",
        ]:
            if kolom in df_evaluasi_tampil.columns:
                df_evaluasi_tampil[kolom] = (
                    pd.to_numeric(
                        df_evaluasi_tampil[kolom],
                        errors="coerce",
                    )
                    .round(4)
                )

        st.dataframe(
            df_evaluasi_tampil,
            use_container_width=True,
            hide_index=True,
        )

    # Kolom identitas yang tersedia pada dataset.
    daftar_identitas = [
        "tahun",
        "sumber_sheet",
        "nama_siswa",
        "nama_sekolah",
        "kompetensi_keahlian",
        "nisn",
    ]

    kolom_identitas = [
        kolom
        for kolom in daftar_identitas
        if kolom in hasil_df.columns
    ]

    # =========================================================
    # OUTPUT K-MEANS
    # =========================================================

    section_title(
        "Output 1: Hasil Clustering K-Means"
    )

    output_kmeans = hasil_df[
        kolom_identitas
        + fitur
        + ["cluster_kmeans"]
    ].copy()

    output_kmeans[fitur] = (
        output_kmeans[fitur]
        .round(2)
    )

    st.dataframe(
        output_kmeans,
        use_container_width=True,
        hide_index=True,
    )

    # =========================================================
    # OUTPUT K-MEDOIDS
    # =========================================================

    section_title(
        "Output 2: Hasil Clustering K-Medoids"
    )

    output_kmedoids = hasil_df[
        kolom_identitas
        + fitur
        + ["cluster_kmedoids"]
    ].copy()

    output_kmedoids[fitur] = (
        output_kmedoids[fitur]
        .round(2)
    )

    st.dataframe(
        output_kmedoids,
        use_container_width=True,
        hide_index=True,
    )

    # =========================================================
    # VISUALISASI
    # =========================================================

    section_title(
        "Visualisasi Cluster"
    )

    info_card(
        "Keterangan Visualisasi",
        (
            "Scatter plot menggunakan rata-rata enam atribut "
            "nonteknis sebagai sumbu X dan rata-rata delapan "
            "atribut teknis sebagai sumbu Y. Penggunaan dua "
            "rata-rata tersebut hanya untuk visualisasi, "
            "sedangkan proses clustering tetap menggunakan "
            "seluruh 14 atribut."
        ),
    )

    col4, col5 = st.columns(2)

    with col4:
        tampilkan_scatter_plot(
            hasil["data_clustering"],
            hasil_df["cluster_kmeans"],
            "Scatter Plot K-Means",
            pusat_cluster=hasil["centroid_kmeans"],
            nama_pusat="Centroid K-Means",
        )

    with col5:
        tampilkan_scatter_plot(
            hasil["data_clustering"],
            hasil_df["cluster_kmedoids"],
            "Scatter Plot K-Medoids",
            pusat_cluster=hasil["medoid_kmedoids"],
            nama_pusat="Medoid K-Medoids",
        )

    # =========================================================
    # JUMLAH DATA PER CLUSTER
    # =========================================================

    section_title(
        "Ringkasan Jumlah Data per Cluster"
    )

    ringkasan_kmeans = buat_ringkasan_jumlah(
        hasil_df,
        "cluster_kmeans",
        "Cluster K-Means",
    )

    ringkasan_kmedoids = buat_ringkasan_jumlah(
        hasil_df,
        "cluster_kmedoids",
        "Cluster K-Medoids",
    )

    col6, col7 = st.columns(2)

    with col6:
        st.markdown(
            "**K-Means**"
        )

        st.dataframe(
            ringkasan_kmeans,
            use_container_width=True,
            hide_index=True,
        )

    with col7:
        st.markdown(
            "**K-Medoids**"
        )

        st.dataframe(
            ringkasan_kmedoids,
            use_container_width=True,
            hide_index=True,
        )

    # =========================================================
    # KARAKTERISTIK CLUSTER
    # =========================================================

    karakteristik_kmeans = buat_karakteristik_cluster(
        hasil_df,
        "cluster_kmeans",
        fitur,
    )

    karakteristik_kmedoids = buat_karakteristik_cluster(
        hasil_df,
        "cluster_kmedoids",
        fitur,
    )

    section_title(
        "Karakteristik Cluster"
    )

    st.caption(
        "Karakteristik cluster dihitung berdasarkan rata-rata "
        "14 atribut penilaian pada setiap kelompok."
    )

    kolom_ringkasan_kmeans = [
        "cluster_kmeans",
        "jumlah_data",
        "rata_rata_nonteknis",
        "rata_rata_teknis",
        "rata_rata_keseluruhan",
        "kategori_performa",
    ]

    kolom_ringkasan_kmedoids = [
        "cluster_kmedoids",
        "jumlah_data",
        "rata_rata_nonteknis",
        "rata_rata_teknis",
        "rata_rata_keseluruhan",
        "kategori_performa",
    ]

    col8, col9 = st.columns(2)

    with col8:
        st.markdown(
            "**Ringkasan Profil K-Means**"
        )

        st.dataframe(
            karakteristik_kmeans[
                kolom_ringkasan_kmeans
            ].round(2),
            use_container_width=True,
            hide_index=True,
        )

    with col9:
        st.markdown(
            "**Ringkasan Profil K-Medoids**"
        )

        st.dataframe(
            karakteristik_kmedoids[
                kolom_ringkasan_kmedoids
            ].round(2),
            use_container_width=True,
            hide_index=True,
        )

    # Menampilkan profil lengkap 14 atribut.
    with st.expander(
        "Lihat rata-rata lengkap 14 atribut K-Means"
    ):
        st.dataframe(
            karakteristik_kmeans.round(2),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander(
        "Lihat rata-rata lengkap 14 atribut K-Medoids"
    ):
        st.dataframe(
            karakteristik_kmedoids.round(2),
            use_container_width=True,
            hide_index=True,
        )

    # =========================================================
    # INTERPRETASI
    # =========================================================

    section_title(
        "Interpretasi Hasil Cluster"
    )

    st.write(
        (
            "Interpretasi dilakukan berdasarkan rata-rata "
            "enam atribut nonteknis, delapan atribut teknis, "
            "dan rata-rata keseluruhan 14 atribut pada setiap "
            "cluster. Kategori performa bersifat relatif "
            "terhadap kelompok lain dalam hasil algoritma "
            "yang sama."
        )
    )

    teks_kmeans = buat_teks_interpretasi(
        karakteristik_kmeans,
        "cluster_kmeans",
        "K-Means",
    )

    success_card(
        "Interpretasi Cluster K-Means",
        teks_kmeans,
    )

    teks_kmedoids = buat_teks_interpretasi(
        karakteristik_kmedoids,
        "cluster_kmedoids",
        "K-Medoids",
    )

    success_card(
        "Interpretasi Cluster K-Medoids",
        teks_kmedoids,
    )