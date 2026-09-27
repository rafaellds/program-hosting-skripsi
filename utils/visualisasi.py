import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from utils.preprocessing import (
    FITUR_CLUSTERING,
    FITUR_NONTEKNIS,
    FITUR_TEKNIS,
)


def siapkan_data_plot(data_clustering):
    """
    Fungsi ini digunakan untuk menyiapkan dua dimensi
    yang akan ditampilkan pada scatter plot.

    Sumbu X merupakan rata-rata enam atribut nonteknis,
    sedangkan sumbu Y merupakan rata-rata delapan atribut teknis.

    Perhitungan rata-rata ini hanya digunakan untuk visualisasi.
    Proses clustering tetap menggunakan seluruh 14 atribut.
    """
    if not isinstance(data_clustering, pd.DataFrame):
        raise TypeError(
            "Data clustering untuk visualisasi harus berupa "
            "pandas DataFrame."
        )

    # Memastikan seluruh atribut tersedia.
    kolom_tidak_ditemukan = [
        kolom
        for kolom in FITUR_CLUSTERING
        if kolom not in data_clustering.columns
    ]

    if kolom_tidak_ditemukan:
        raise ValueError(
            "Data visualisasi tidak memiliki kolom berikut: "
            + ", ".join(kolom_tidak_ditemukan)
        )

    # Mengambil 14 atribut clustering.
    data_plot = data_clustering[
        FITUR_CLUSTERING
    ].copy()

    # Mengubah nilai menjadi numerik.
    data_plot = data_plot.apply(
        pd.to_numeric,
        errors="coerce",
    )

    # Memastikan tidak terdapat nilai kosong.
    if data_plot.isna().any().any():
        raise ValueError(
            "Data visualisasi masih memiliki nilai kosong "
            "atau nilai yang tidak dapat dikonversi menjadi numerik."
        )

    # Menghitung rata-rata atribut nonteknis untuk sumbu X.
    data_plot["rata_nonteknis_plot"] = data_plot[
        FITUR_NONTEKNIS
    ].mean(axis=1)

    # Menghitung rata-rata atribut teknis untuk sumbu Y.
    data_plot["rata_teknis_plot"] = data_plot[
        FITUR_TEKNIS
    ].mean(axis=1)

    return data_plot


def siapkan_pusat_plot(pusat_cluster):
    """
    Fungsi ini digunakan untuk mengubah centroid atau medoid
    yang terdiri dari 14 atribut menjadi dua dimensi visualisasi.

    Dimensi pertama merupakan rata-rata atribut nonteknis.
    Dimensi kedua merupakan rata-rata atribut teknis.
    """
    pusat_array = np.asarray(
        pusat_cluster,
        dtype=float,
    )

    # Mengubah data satu dimensi menjadi dua dimensi.
    if pusat_array.ndim == 1:
        pusat_array = pusat_array.reshape(1, -1)

    if pusat_array.ndim != 2:
        raise ValueError(
            "Data pusat cluster harus berupa array dua dimensi."
        )

    # Memastikan jumlah kolom pusat cluster sama dengan 14 atribut.
    if pusat_array.shape[1] != len(FITUR_CLUSTERING):
        raise ValueError(
            "Jumlah atribut pusat cluster tidak sesuai. "
            f"Ditemukan {pusat_array.shape[1]} atribut, "
            f"sedangkan yang dibutuhkan adalah "
            f"{len(FITUR_CLUSTERING)} atribut."
        )

    # Mengubah pusat cluster menjadi DataFrame.
    df_pusat = pd.DataFrame(
        pusat_array,
        columns=FITUR_CLUSTERING,
    )

    # Menghitung posisi pusat cluster pada sumbu visualisasi.
    pusat_nonteknis = df_pusat[
        FITUR_NONTEKNIS
    ].mean(axis=1)

    pusat_teknis = df_pusat[
        FITUR_TEKNIS
    ].mean(axis=1)

    return pusat_nonteknis, pusat_teknis


def tampilkan_scatter_plot(
    data_clustering,
    label_cluster,
    judul,
    pusat_cluster=None,
    nama_pusat="Pusat Cluster",
):
    """
    Fungsi ini digunakan untuk menampilkan scatter plot
    hasil clustering K-Means atau K-Medoids.

    Parameter:
        data_clustering:
            Data nilai siswa yang berisi 14 atribut clustering.

        label_cluster:
            Label cluster hasil K-Means atau K-Medoids.

        judul:
            Judul grafik yang ditampilkan.

        pusat_cluster:
            Centroid K-Means atau medoid K-Medoids dalam
            skala nilai asli.

        nama_pusat:
            Nama titik pusat yang ditampilkan pada legenda.
    """

    # Menyiapkan dua dimensi visualisasi.
    data_plot = siapkan_data_plot(
        data_clustering
    )

    # Mengubah label menjadi array NumPy satu dimensi.
    label_cluster = np.asarray(
        label_cluster
    ).reshape(-1)

    # Memastikan jumlah label sesuai dengan jumlah data.
    if len(data_plot) != len(label_cluster):
        raise ValueError(
            "Jumlah data visualisasi tidak sesuai dengan "
            "jumlah label cluster."
        )

    # Membuat area grafik.
    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    # Menampilkan data siswa berdasarkan label cluster.
    scatter = ax.scatter(
        data_plot["rata_nonteknis_plot"],
        data_plot["rata_teknis_plot"],
        c=label_cluster,
        alpha=0.75,
        s=55,
    )

    # Menampilkan centroid atau medoid apabila tersedia.
    if pusat_cluster is not None:
        (
            pusat_nonteknis,
            pusat_teknis,
        ) = siapkan_pusat_plot(
            pusat_cluster
        )

        ax.scatter(
            pusat_nonteknis,
            pusat_teknis,
            marker="X",
            s=180,
            edgecolors="black",
            linewidths=1,
            label=nama_pusat,
        )

    # Mengatur judul dan nama sumbu.
    ax.set_title(
        judul,
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Rata-rata Nilai Nonteknis / Soft Skill"
    )

    ax.set_ylabel(
        "Rata-rata Nilai Teknis / Hard Skill"
    )

    # Menampilkan garis bantu.
    ax.grid(
        True,
        linestyle="--",
        alpha=0.4,
    )

    # Menampilkan legenda label cluster.
    legenda_cluster = ax.legend(
        *scatter.legend_elements(),
        title="Cluster",
        loc="best",
    )

    ax.add_artist(
        legenda_cluster
    )

    # Menampilkan legenda centroid atau medoid.
    if pusat_cluster is not None:
        ax.legend(
            loc="upper right"
        )

    # Mengatur tata letak grafik.
    fig.tight_layout()

    # Menampilkan grafik pada Streamlit.
    st.pyplot(fig)

    # Menutup objek grafik untuk menghindari penggunaan memori berlebih.
    plt.close(fig)