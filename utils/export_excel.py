from io import BytesIO

import pandas as pd

from utils.preprocessing import (
    FITUR_NONTEKNIS,
    FITUR_TEKNIS,
)


def tentukan_kategori_performa(nilai_rata_rata):
    """
    Memberikan kategori performa relatif berdasarkan urutan
    rata-rata keseluruhan setiap cluster.
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


def buat_ringkasan_cluster(
    hasil_df,
    kolom_cluster,
    nama_cluster,
):
    """
    Menghitung jumlah siswa pada setiap cluster.
    """
    ringkasan = (
        hasil_df[kolom_cluster]
        .value_counts()
        .sort_index()
        .rename_axis(nama_cluster)
        .reset_index(name="Jumlah Data")
    )

    return ringkasan


def buat_profil_cluster(
    hasil_df,
    fitur,
    kolom_cluster,
    nama_cluster,
):
    """
    Menghitung rata-rata 14 atribut penilaian pada setiap
    cluster beserta rata-rata nonteknis, teknis, dan
    keseluruhan.
    """
    kolom_tidak_ditemukan = [
        kolom
        for kolom in fitur
        if kolom not in hasil_df.columns
    ]

    if kolom_tidak_ditemukan:
        raise ValueError(
            "Atribut clustering berikut tidak ditemukan: "
            + ", ".join(kolom_tidak_ditemukan)
        )

    if kolom_cluster not in hasil_df.columns:
        raise ValueError(
            f"Kolom '{kolom_cluster}' tidak ditemukan "
            "pada hasil clustering."
        )

    data_profil = hasil_df[
        [kolom_cluster] + fitur
    ].copy()

    data_profil[fitur] = data_profil[fitur].apply(
        pd.to_numeric,
        errors="coerce",
    )

    if data_profil[fitur].isna().any().any():
        raise ValueError(
            "Hasil clustering masih memiliki nilai kosong "
            "atau nilai yang tidak dapat dibaca sebagai angka."
        )

    jumlah_anggota = (
        data_profil
        .groupby(kolom_cluster)
        .size()
        .reset_index(name="Jumlah Data")
    )

    profil = (
        data_profil
        .groupby(kolom_cluster, as_index=False)[fitur]
        .mean()
    )

    profil = jumlah_anggota.merge(
        profil,
        on=kolom_cluster,
        how="left",
    )

    profil["Rata-rata Nonteknis"] = (
        profil[FITUR_NONTEKNIS]
        .mean(axis=1)
    )

    profil["Rata-rata Teknis"] = (
        profil[FITUR_TEKNIS]
        .mean(axis=1)
    )

    profil["Rata-rata Keseluruhan"] = (
        profil[fitur]
        .mean(axis=1)
    )

    profil["Kategori Performa"] = (
        tentukan_kategori_performa(
            profil["Rata-rata Keseluruhan"]
        )
    )

    profil = profil.rename(
        columns={
            kolom_cluster: nama_cluster,
        }
    )

    kolom_ringkasan = [
        nama_cluster,
        "Jumlah Data",
        "Rata-rata Nonteknis",
        "Rata-rata Teknis",
        "Rata-rata Keseluruhan",
        "Kategori Performa",
    ]

    profil = profil[
        kolom_ringkasan + fitur
    ]

    return profil


def pilih_kolom_identitas(hasil_df):
    """
    Memilih kolom identitas yang tersedia pada dataset.
    """
    daftar_identitas = [
        "tahun",
        "sumber_sheet",
        "nisn",
        "nama_siswa",
        "nama_sekolah",
        "asal_sekolah",
        "kompetensi_keahlian",
    ]

    return [
        kolom
        for kolom in daftar_identitas
        if kolom in hasil_df.columns
    ]


def buat_ringkasan_proses(hasil, hasil_df, fitur):
    """
    Membuat ringkasan hasil perbandingan K-Means dan
    K-Medoids.
    """
    silhouette_kmeans = float(
        hasil["silhouette_terbaik_kmeans"]
    )

    silhouette_kmedoids = float(
        hasil["silhouette_terbaik_kmedoids"]
    )

    selisih = abs(
        silhouette_kmeans - silhouette_kmedoids
    )

    if selisih <= 1e-12:
        algoritma_terbaik = "K-Means dan K-Medoids Setara"
    elif silhouette_kmeans > silhouette_kmedoids:
        algoritma_terbaik = "K-Means"
    else:
        algoritma_terbaik = "K-Medoids"

    ringkasan = pd.DataFrame({
        "Keterangan": [
            "Jumlah Data",
            "Jumlah Atribut Clustering",
            "Rentang Jumlah Cluster",
            "k Terbaik K-Means",
            "Silhouette Terbaik K-Means",
            "k Terbaik K-Medoids",
            "Silhouette Terbaik K-Medoids",
            "Selisih Silhouette Coefficient",
            "Algoritma dengan Nilai Terbaik",
        ],
        "Nilai": [
            hasil_df.shape[0],
            len(fitur),
            "2 sampai 5",
            hasil["k_terbaik_kmeans"],
            round(silhouette_kmeans, 6),
            hasil["k_terbaik_kmedoids"],
            round(silhouette_kmedoids, 6),
            round(selisih, 6),
            algoritma_terbaik,
        ],
    })

    return ringkasan


def atur_format_sheet(
    writer,
    nama_sheet,
    dataframe,
):
    """
    Mengatur format dasar setiap sheet agar tabel Excel
    lebih mudah dibaca.
    """
    workbook = writer.book
    worksheet = writer.sheets[nama_sheet]

    format_header = workbook.add_format({
        "bold": True,
        "text_wrap": True,
        "valign": "vcenter",
        "align": "center",
        "border": 1,
        "bg_color": "#D9EAF7",
    })

    format_teks = workbook.add_format({
        "valign": "top",
        "border": 1,
    })

    format_integer = workbook.add_format({
        "num_format": "0",
        "valign": "top",
        "border": 1,
    })

    format_desimal = workbook.add_format({
        "num_format": "0.00",
        "valign": "top",
        "border": 1,
    })

    format_silhouette = workbook.add_format({
        "num_format": "0.0000",
        "valign": "top",
        "border": 1,
    })

    worksheet.set_row(
        0,
        30,
        format_header,
    )

    worksheet.freeze_panes(
        1,
        0,
    )

    if len(dataframe.columns) > 0:
        worksheet.autofilter(
            0,
            0,
            len(dataframe),
            len(dataframe.columns) - 1,
        )

    for nomor_kolom, nama_kolom in enumerate(
        dataframe.columns
    ):
        isi_kolom = dataframe[nama_kolom]

        if isi_kolom.empty:
            panjang_isi = 0
        else:
            panjang_isi = int(
                isi_kolom
                .astype(str)
                .map(len)
                .max()
            )

        lebar_kolom = min(
            max(
                len(str(nama_kolom)) + 2,
                panjang_isi + 2,
                12,
            ),
            35,
        )

        if "silhouette" in str(nama_kolom).lower():
            format_kolom = format_silhouette

        elif pd.api.types.is_integer_dtype(
            isi_kolom
        ):
            format_kolom = format_integer

        elif pd.api.types.is_float_dtype(
            isi_kolom
        ):
            format_kolom = format_desimal

        else:
            format_kolom = format_teks

        worksheet.set_column(
            nomor_kolom,
            nomor_kolom,
            lebar_kolom,
            format_kolom,
        )


def buat_file_excel(hasil):
    """
    Membuat file Excel hasil clustering agar dapat diunduh
    melalui aplikasi.

    File Excel berisi ringkasan proses, hasil K-Means,
    hasil K-Medoids, hasil gabungan, evaluasi Silhouette
    Coefficient, jumlah data per cluster, dan profil
    karakteristik setiap cluster.
    """
    if not isinstance(hasil, dict):
        raise TypeError(
            "Hasil clustering harus berbentuk dictionary."
        )

    kunci_wajib = [
        "hasil_df",
        "df_evaluasi",
        "fitur",
        "k_terbaik_kmeans",
        "k_terbaik_kmedoids",
        "silhouette_terbaik_kmeans",
        "silhouette_terbaik_kmedoids",
    ]

    kunci_tidak_ditemukan = [
        kunci
        for kunci in kunci_wajib
        if kunci not in hasil
    ]

    if kunci_tidak_ditemukan:
        raise ValueError(
            "Data hasil clustering belum lengkap. "
            "Kunci yang tidak ditemukan: "
            + ", ".join(kunci_tidak_ditemukan)
        )

    output = BytesIO()

    hasil_df = hasil["hasil_df"].copy()
    df_evaluasi = hasil["df_evaluasi"].copy()
    fitur = list(hasil["fitur"])

    if hasil_df.empty:
        raise ValueError(
            "Hasil clustering tidak memiliki data."
        )

    kolom_cluster_wajib = [
        "cluster_kmeans",
        "cluster_kmedoids",
    ]

    kolom_cluster_tidak_ditemukan = [
        kolom
        for kolom in kolom_cluster_wajib
        if kolom not in hasil_df.columns
    ]

    if kolom_cluster_tidak_ditemukan:
        raise ValueError(
            "Kolom hasil cluster tidak ditemukan: "
            + ", ".join(
                kolom_cluster_tidak_ditemukan
            )
        )

    kolom_identitas = pilih_kolom_identitas(
        hasil_df
    )

    kolom_turunan = [
        kolom
        for kolom in hasil_df.columns
        if (
            kolom.startswith("ratarata_")
            or kolom.startswith("kategori_")
        )
        and kolom not in fitur
    ]

    # Menghilangkan kemungkinan nama kolom yang berulang.
    kolom_identitas = list(
        dict.fromkeys(kolom_identitas)
    )

    kolom_turunan = list(
        dict.fromkeys(kolom_turunan)
    )

    output_kmeans = hasil_df[
        kolom_identitas
        + fitur
        + kolom_turunan
        + ["cluster_kmeans"]
    ].copy()

    output_kmedoids = hasil_df[
        kolom_identitas
        + fitur
        + kolom_turunan
        + ["cluster_kmedoids"]
    ].copy()

    output_gabungan = hasil_df.copy()

    ringkasan_kmeans = buat_ringkasan_cluster(
        hasil_df,
        "cluster_kmeans",
        "Cluster K-Means",
    )

    ringkasan_kmedoids = buat_ringkasan_cluster(
        hasil_df,
        "cluster_kmedoids",
        "Cluster K-Medoids",
    )

    profil_kmeans = buat_profil_cluster(
        hasil_df,
        fitur,
        "cluster_kmeans",
        "Cluster K-Means",
    )

    profil_kmedoids = buat_profil_cluster(
        hasil_df,
        fitur,
        "cluster_kmedoids",
        "Cluster K-Medoids",
    )

    ringkasan_proses = buat_ringkasan_proses(
        hasil,
        hasil_df,
        fitur,
    )

    # Pembulatan hanya dilakukan untuk file laporan.
    for dataframe in [
        output_kmeans,
        output_kmedoids,
        output_gabungan,
    ]:
        kolom_numerik = dataframe.select_dtypes(
            include="number"
        ).columns

        kolom_desimal = [
            kolom
            for kolom in kolom_numerik
            if not kolom.startswith("cluster_")
        ]

        dataframe[kolom_desimal] = (
            dataframe[kolom_desimal]
            .round(2)
        )

    profil_kmeans = profil_kmeans.round(2)
    profil_kmedoids = profil_kmedoids.round(2)

    kolom_silhouette = [
        kolom
        for kolom in df_evaluasi.columns
        if "silhouette" in kolom.lower()
    ]

    for kolom in kolom_silhouette:
        df_evaluasi[kolom] = (
            pd.to_numeric(
                df_evaluasi[kolom],
                errors="coerce",
            )
            .round(4)
        )

    daftar_sheet = {
        "Ringkasan_Proses": ringkasan_proses,
        "Hasil_KMeans": output_kmeans,
        "Hasil_KMedoids": output_kmedoids,
        "Hasil_Gabungan": output_gabungan,
        "Evaluasi_Silhouette": df_evaluasi,
        "Jumlah_KMeans": ringkasan_kmeans,
        "Jumlah_KMedoids": ringkasan_kmedoids,
        "Profil_KMeans": profil_kmeans,
        "Profil_KMedoids": profil_kmedoids,
    }

    try:
        with pd.ExcelWriter(
            output,
            engine="xlsxwriter",
        ) as writer:
            for nama_sheet, dataframe in daftar_sheet.items():
                dataframe.to_excel(
                    writer,
                    sheet_name=nama_sheet,
                    index=False,
                )

                atur_format_sheet(
                    writer,
                    nama_sheet,
                    dataframe,
                )

    except Exception as error:
        raise RuntimeError(
            "File Excel hasil clustering gagal dibuat."
        ) from error

    output.seek(0)

    return output