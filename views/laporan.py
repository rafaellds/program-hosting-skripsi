import streamlit as st

from components import (
    page_header,
    section_title,
    info_card,
    success_card,
    warning_card,
)

from utils.database import (
    ambil_daftar_proses,
    ambil_hasil_proses,
)

from utils.export_excel import (
    buat_file_excel,
)

from utils.preprocessing import (
    FITUR_CLUSTERING,
)


# ============================================================
# HALAMAN LAPORAN
# ============================================================

def halaman_laporan():
    """
    Menampilkan halaman laporan dan menyediakan
    file Excel hasil clustering berdasarkan riwayat
    proses yang tersimpan di PostgreSQL.
    """

    # ========================================================
    # HAK AKSES
    # ========================================================

    role = st.session_state.get(
        "role"
    )

    if role not in [
        "admin",
        "pimpinan",
    ]:

        st.error(
            "Anda tidak memiliki hak akses "
            "untuk melihat atau mengunduh laporan."
        )

        return

    # ========================================================
    # HEADER
    # ========================================================

    page_header(
        "Laporan",
        (
            "Menu untuk melihat ringkasan dan "
            "mengunduh hasil clustering serta "
            "evaluasi dalam format Excel."
        ),
    )

    # ========================================================
    # MENGAMBIL RIWAYAT PROSES
    # ========================================================

    try:

        daftar_proses = (
            ambil_daftar_proses()
        )

    except Exception as error:

        st.error(
            "Riwayat proses gagal dibaca "
            f"dari database: {error}"
        )

        return

    # ========================================================
    # RIWAYAT BELUM TERSEDIA
    # ========================================================

    if not daftar_proses:

        if role == "admin":

            pesan_laporan = (
                "Belum terdapat proses clustering "
                "yang tersimpan di database. "
                "Silakan jalankan proses melalui menu "
                "Kelola Data Penilaian dan Proses "
                "Clustering dan Evaluasi terlebih dahulu."
            )

        else:

            pesan_laporan = (
                "Belum terdapat hasil proses clustering "
                "yang tersimpan di database. "
                "Laporan akan tersedia setelah Admin "
                "atau Pengelola PKL menjalankan "
                "proses clustering dan evaluasi."
            )

        warning_card(
            "Laporan Belum Tersedia",
            pesan_laporan,
        )

        return

    # ========================================================
    # PILIH RIWAYAT PROSES
    # ========================================================

    section_title(
        "Riwayat Proses Clustering"
    )

    st.write(
        "Pilih riwayat proses yang ingin "
        "digunakan untuk membuat laporan:"
    )

    # Membuat dictionary agar ID proses dapat
    # dipasangkan dengan informasi proses.
    proses_map = {
        proses["id_proses"]: proses
        for proses in daftar_proses
    }

    daftar_id_proses = list(
        proses_map.keys()
    )

    # Jika session masih memiliki ID proses,
    # gunakan sebagai pilihan awal.
    id_proses_session = (
        st.session_state.get(
            "id_proses"
        )
    )

    indeks_default = 0

    if (
        id_proses_session
        in daftar_id_proses
    ):

        indeks_default = (
            daftar_id_proses.index(
                id_proses_session
            )
        )

    # ========================================================
    # FORMAT PILIHAN RIWAYAT
    # ========================================================

    def format_proses(
        id_proses
    ):

        proses = proses_map[
            id_proses
        ]

        tanggal = proses.get(
            "tanggal_proses"
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

        return (
            f"ID Proses {proses['id_proses']} | "
            f"ID Dataset {proses['id_dataset']} | "
            f"{proses['nama_dataset']} | "
            f"{tanggal_teks}"
        )

    # ========================================================
    # SELECTBOX RIWAYAT
    # ========================================================

    id_proses_pilihan = (
        st.selectbox(
            "Pilih riwayat proses:",
            options=daftar_id_proses,
            index=indeks_default,
            format_func=format_proses,
        )
    )

    proses_pilihan = (
        proses_map[
            id_proses_pilihan
        ]
    )

    st.caption(
        "Laporan dibuat dari PostgreSQL. "
        f"ID Proses: "
        f"{proses_pilihan['id_proses']} | "
        f"ID Dataset: "
        f"{proses_pilihan['id_dataset']} | "
        f"Diproses oleh: "
        f"{proses_pilihan['nama_pengguna']}"
    )

    # ========================================================
    # MENGAMBIL HASIL PROSES
    # ========================================================

    try:

        hasil = (
            ambil_hasil_proses(
                id_proses_pilihan
            )
        )

    except Exception as error:

        st.error(
            "Data hasil clustering gagal "
            f"dibaca dari database: {error}"
        )

        return

    # Data dari PostgreSQL tidak menyimpan
    # daftar nama fitur sebagai tabel tersendiri.
    # Karena penelitian menggunakan 14 atribut
    # yang tetap, daftar fitur diambil dari
    # preprocessing.py.
    hasil["fitur"] = list(
        FITUR_CLUSTERING
    )

    # ========================================================
    # VALIDASI DATA LAPORAN
    # ========================================================

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

        st.error(
            "Laporan belum dapat dibuat karena "
            "data hasil clustering belum lengkap. "
            "Data yang tidak ditemukan: "
            + ", ".join(
                kunci_tidak_ditemukan
            )
        )

        return

    # ========================================================
    # DATA HASIL
    # ========================================================

    hasil_df = (
        hasil[
            "hasil_df"
        ].copy()
    )

    fitur = (
        hasil[
            "fitur"
        ]
    )

    if hasil_df.empty:

        st.error(
            "Data hasil clustering tidak ditemukan."
        )

        return

    # ========================================================
    # NILAI EVALUASI
    # ========================================================

    silhouette_kmeans = float(
        hasil[
            "silhouette_terbaik_kmeans"
        ]
    )

    silhouette_kmedoids = float(
        hasil[
            "silhouette_terbaik_kmedoids"
        ]
    )

    selisih_silhouette = abs(
        silhouette_kmeans
        - silhouette_kmedoids
    )

    # Menentukan algoritma dengan
    # nilai Silhouette Coefficient tertinggi.
    if abs(
        silhouette_kmeans
        - silhouette_kmedoids
    ) <= 1e-12:

        algoritma_terbaik = (
            "K-Means dan K-Medoids Setara"
        )

    elif (
        silhouette_kmeans
        > silhouette_kmedoids
    ):

        algoritma_terbaik = (
            "K-Means"
        )

    else:

        algoritma_terbaik = (
            "K-Medoids"
        )

    # ========================================================
    # INFORMASI LAPORAN
    # ========================================================

    info_card(
        "Isi Laporan",
        (
            "File laporan berisi ringkasan proses, "
            "hasil clustering K-Means, hasil clustering "
            "K-Medoids, hasil gabungan, evaluasi "
            "Silhouette Coefficient, jumlah anggota "
            "setiap cluster, serta profil karakteristik "
            "cluster berdasarkan 14 atribut penilaian."
        ),
    )

    # ========================================================
    # RINGKASAN HASIL
    # ========================================================

    section_title(
        "Ringkasan Hasil"
    )

    col1, col2, col3 = (
        st.columns(3)
    )

    with col1:

        st.metric(
            "Jumlah Data",
            hasil_df.shape[0],
        )

    with col2:

        st.metric(
            "Atribut Clustering",
            len(fitur),
        )

    with col3:

        st.metric(
            "Rentang k",
            "2 - 5",
        )

    # ========================================================
    # NILAI SILHOUETTE
    # ========================================================

    col4, col5 = (
        st.columns(2)
    )

    with col4:

        st.metric(
            "Silhouette K-Means",
            f"{silhouette_kmeans:.4f}",
        )

        st.caption(
            "Jumlah cluster terbaik: "
            f"{hasil['k_terbaik_kmeans']}"
        )

    with col5:

        st.metric(
            "Silhouette K-Medoids",
            f"{silhouette_kmedoids:.4f}",
        )

        st.caption(
            "Jumlah cluster terbaik: "
            f"{hasil['k_terbaik_kmedoids']}"
        )

    # ========================================================
    # SELISIH DAN ALGORITMA
    # ========================================================

    col6, col7 = (
        st.columns(2)
    )

    with col6:

        st.metric(
            "Selisih Silhouette",
            f"{selisih_silhouette:.4f}",
        )

    with col7:

        st.metric(
            "Algoritma Terbaik",
            algoritma_terbaik,
        )

    # ========================================================
    # INFORMASI PROSES
    # ========================================================

    section_title(
        "Informasi Proses"
    )

    col8, col9 = (
        st.columns(2)
    )

    with col8:

        st.write(
            f"**ID Proses:** "
            f"{proses_pilihan['id_proses']}"
        )

        st.write(
            f"**ID Dataset:** "
            f"{proses_pilihan['id_dataset']}"
        )

        st.write(
            f"**Nama Dataset:** "
            f"{proses_pilihan['nama_dataset']}"
        )

    with col9:

        tanggal_proses = (
            proses_pilihan.get(
                "tanggal_proses"
            )
        )

        if tanggal_proses is not None:

            if hasattr(
                tanggal_proses,
                "strftime",
            ):

                tanggal_teks = (
                    tanggal_proses.strftime(
                        "%d-%m-%Y %H:%M:%S"
                    )
                )

            else:

                tanggal_teks = str(
                    tanggal_proses
                )

        else:

            tanggal_teks = "-"

        st.write(
            f"**Tanggal Proses:** "
            f"{tanggal_teks}"
        )

        st.write(
            f"**Diproses Oleh:** "
            f"{proses_pilihan['nama_pengguna']}"
        )

    # ========================================================
    # DAFTAR SHEET
    # ========================================================

    section_title(
        "Daftar Sheet Laporan"
    )

    with st.expander(
        "Lihat isi file laporan Excel",
        expanded=False,
    ):

        st.markdown(
            """
1. **Ringkasan_Proses**  
   Ringkasan jumlah data, jumlah atribut, nilai *k* terbaik,
   nilai *Silhouette Coefficient*, selisih nilai,
   dan algoritma terbaik.

2. **Hasil_KMeans**  
   Identitas siswa, 14 atribut penilaian,
   dan hasil cluster K-Means.

3. **Hasil_KMedoids**  
   Identitas siswa, 14 atribut penilaian,
   dan hasil cluster K-Medoids.

4. **Hasil_Gabungan**  
   Seluruh data beserta hasil cluster
   K-Means dan K-Medoids.

5. **Evaluasi_Silhouette**  
   Nilai *Silhouette Coefficient*
   untuk setiap nilai *k* dari 2 sampai 5.

6. **Jumlah_KMeans**  
   Jumlah anggota pada setiap cluster
   K-Means.

7. **Jumlah_KMedoids**  
   Jumlah anggota pada setiap cluster
   K-Medoids.

8. **Profil_KMeans**  
   Karakteristik setiap cluster K-Means
   berdasarkan rata-rata 14 atribut
   penilaian.

9. **Profil_KMedoids**  
   Karakteristik setiap cluster K-Medoids
   berdasarkan rata-rata 14 atribut
   penilaian.
            """
        )

    # ========================================================
    # PEMBUATAN FILE EXCEL
    # ========================================================

    try:

        file_excel = (
            buat_file_excel(
                hasil
            )
        )

        # Mengubah BytesIO menjadi bytes agar
        # stabil ketika digunakan tombol download.
        data_excel = (
            file_excel.getvalue()
        )

    except Exception as error:

        st.error(
            "Laporan Excel gagal dibuat: "
            f"{error}"
        )

        return

    # ========================================================
    # LAPORAN SIAP
    # ========================================================

    success_card(
        "Laporan Siap Diunduh",
        (
            "File Excel hasil perbandingan "
            "K-Means dan K-Medoids telah "
            "berhasil dibuat berdasarkan "
            "riwayat proses yang tersimpan "
            "di PostgreSQL."
        ),
    )

    # ========================================================
    # NAMA FILE
    # ========================================================

    nama_file = (
        "hasil_clustering_"
        f"proses_{id_proses_pilihan}_"
        "kmeans_kmedoids_"
        "14_atribut.xlsx"
    )

    # ========================================================
    # DOWNLOAD
    # ========================================================

    st.download_button(
        label=(
            "Download Laporan "
            "Hasil Clustering"
        ),
        data=data_excel,
        file_name=nama_file,
        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    st.caption(
        "File laporan menggunakan format "
        "Microsoft Excel (.xlsx)."
    )