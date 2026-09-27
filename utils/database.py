import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from decimal import Decimal


# ============================================================
# KONEKSI DATABASE
# ============================================================

def get_connection():
    """
    Membuat koneksi ke database PostgreSQL Neon.
    Connection string dibaca dari environment variable DATABASE_URL.
    """

    try:
        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            raise ValueError(
                "DATABASE_URL belum dikonfigurasi."
            )

        connection = psycopg2.connect(
            database_url,
            connect_timeout=10
        )

        return connection

    except Exception as error:
        print(
            f"Koneksi database gagal: {error}"
        )
        return None


# ============================================================
# FUNGSI PENDUKUNG
# ============================================================

def normalisasi_nisn(value):
    """
    Membersihkan dan menyeragamkan format NISN
    menjadi 10 digit.
    """

    nisn = str(value).strip()

    # Menghapus .0 apabila terbaca sebagai angka dari Excel.
    if nisn.endswith(".0"):
        nisn = nisn[:-2]

    # Mengembalikan angka 0 di bagian depan.
    nisn = nisn.zfill(10)

    return nisn


def ke_decimal(value):
    """
    Mengubah nilai numerik menjadi Decimal
    agar sesuai dengan tipe NUMERIC PostgreSQL.
    """

    return Decimal(
        str(value)
    )


# ============================================================
# SIMPAN DATASET
# ============================================================

def simpan_dataset(
    df,
    id_pengguna,
    nama_dataset,
    sumber_data="PT FNI Teknologi Digital"
):
    """
    Menyimpan dataset ke PostgreSQL Neon secara efisien.

    Perbaikan versi hosting:
    1. Mencegah dataset yang sama tersimpan berulang.
    2. Menggunakan batch insert untuk siswa dan penilaian.
    3. Seluruh proses tetap berada dalam satu transaksi.
    4. Mengembalikan ID dataset yang sudah ada apabila
       dataset yang sama sebelumnya telah tersimpan.
    """

    if df is None or df.empty:
        raise ValueError(
            "Dataset kosong dan tidak dapat disimpan ke database."
        )

    if id_pengguna is None:
        raise ValueError(
            "ID pengguna tidak ditemukan."
        )

    kolom_wajib = [
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

    kolom_tidak_ditemukan = [
        kolom for kolom in kolom_wajib
        if kolom not in df.columns
    ]

    if kolom_tidak_ditemukan:
        raise ValueError(
            "Dataset belum memiliki seluruh kolom yang diperlukan "
            "database. Kolom yang tidak ditemukan: "
            + ", ".join(kolom_tidak_ditemukan)
        )

    data = df.copy()
    data["nisn"] = data["nisn"].apply(normalisasi_nisn)

    if data["nisn"].duplicated().any():
        nisn_duplikat = (
            data.loc[
                data["nisn"].duplicated(keep=False),
                "nisn"
            ]
            .unique()
            .tolist()
        )
        raise ValueError(
            "Ditemukan NISN duplikat pada dataset: "
            + ", ".join(nisn_duplikat)
        )

    conn = get_connection()
    if conn is None:
        raise ConnectionError(
            "Koneksi ke database PostgreSQL gagal."
        )

    cursor = None

    try:
        cursor = conn.cursor()

        # Mengunci transaksi berdasarkan pengguna + nama dataset.
        # Jika tombol Simpan terpanggil lebih dari sekali, request
        # berikutnya menunggu transaksi pertama selesai lalu akan
        # menemukan dataset yang sudah tersimpan.
        kunci_dataset = f"{int(id_pengguna)}:{str(nama_dataset)}"
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s)::bigint)",
            (kunci_dataset,)
        )

        # Cegah duplikasi dataset yang sama. Untuk aplikasi ini,
        # kombinasi pengguna + nama file + jumlah data digunakan
        # sebagai identitas penyimpanan dataset.
        cursor.execute(
            """
            SELECT id_dataset
            FROM dataset
            WHERE id_pengguna = %s
              AND nama_dataset = %s
              AND jumlah_data = %s
            ORDER BY id_dataset DESC
            LIMIT 1
            """,
            (
                int(id_pengguna),
                str(nama_dataset),
                int(len(data)),
            )
        )

        dataset_lama = cursor.fetchone()

        if dataset_lama is not None:
            id_dataset = int(dataset_lama[0])

            cursor.execute(
                """
                SELECT id_penilaian, nisn
                FROM penilaian
                WHERE id_dataset = %s
                """,
                (id_dataset,)
            )

            penilaian_tersimpan = {
                normalisasi_nisn(nisn): id_penilaian
                for id_penilaian, nisn in cursor.fetchall()
            }

            # Dataset dianggap lengkap hanya jika seluruh baris
            # penilaian memang sudah tersimpan.
            if len(penilaian_tersimpan) == len(data):
                id_penilaian_map = {
                    index: penilaian_tersimpan[
                        normalisasi_nisn(row["nisn"])
                    ]
                    for index, row in data.iterrows()
                }

                conn.commit()

                return {
                    "id_dataset": id_dataset,
                    "jumlah_data": len(data),
                    "id_penilaian_map": id_penilaian_map,
                    "sudah_ada": True,
                }

        # 1. Simpan informasi dataset.
        cursor.execute(
            """
            INSERT INTO dataset (
                id_pengguna,
                nama_dataset,
                jumlah_data,
                sumber_data
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id_dataset
            """,
            (
                int(id_pengguna),
                str(nama_dataset),
                int(len(data)),
                str(sumber_data),
            )
        )

        id_dataset = int(cursor.fetchone()[0])

        # 2. Simpan / perbarui siswa sekaligus dalam satu batch.
        data_siswa = [
            (
                normalisasi_nisn(row["nisn"]),
                str(row["nama_siswa"]).strip(),
                str(row["nama_sekolah"]).strip(),
                str(row["kompetensi_keahlian"]).strip(),
            )
            for _, row in data.iterrows()
        ]

        execute_values(
            cursor,
            """
            INSERT INTO siswa (
                nisn,
                nama_siswa,
                nama_sekolah,
                kompetensi_keahlian
            )
            VALUES %s
            ON CONFLICT (nisn)
            DO UPDATE SET
                nama_siswa = EXCLUDED.nama_siswa,
                nama_sekolah = EXCLUDED.nama_sekolah,
                kompetensi_keahlian = EXCLUDED.kompetensi_keahlian
            """,
            data_siswa,
            page_size=max(len(data_siswa), 1),
        )

        # 3. Simpan seluruh penilaian dalam satu batch.
        data_penilaian = []

        for _, row in data.iterrows():
            data_penilaian.append((
                id_dataset,
                normalisasi_nisn(row["nisn"]),
                int(row["tahun"]),
                str(row["sumber_sheet"]).strip(),
                ke_decimal(row["nilai_kedisiplinan"]),
                ke_decimal(row["nilai_kerjasama"]),
                ke_decimal(row["nilai_inisiatif"]),
                ke_decimal(row["nilai_kerajinan"]),
                ke_decimal(row["nilai_tanggung_jawab"]),
                ke_decimal(row["nilai_sikap_perilaku"]),
                ke_decimal(row["nilai_ms_word"]),
                ke_decimal(row["nilai_ms_excel"]),
                ke_decimal(row["nilai_mikrotik"]),
                ke_decimal(row["nilai_kabel_lan"]),
                ke_decimal(row["nilai_fiber_optic"]),
                ke_decimal(row["nilai_hardware"]),
                ke_decimal(row["nilai_perakitan_cpu"]),
                ke_decimal(row["nilai_windows"]),
                ke_decimal(row["ratarata_nonteknis"]),
                ke_decimal(row["ratarata_teknis"]),
                ke_decimal(row["ratarata_keseluruhan"]),
                str(row["kategori_nonteknis"]).strip(),
                str(row["kategori_teknis"]).strip(),
                str(row["kategori_keseluruhan"]).strip(),
            ))

        execute_values(
            cursor,
            """
            INSERT INTO penilaian (
                id_dataset,
                nisn,
                tahun,
                sumber_sheet,
                nilai_kedisiplinan,
                nilai_kerjasama,
                nilai_inisiatif,
                nilai_kerajinan,
                nilai_tanggung_jawab,
                nilai_sikap_perilaku,
                nilai_ms_word,
                nilai_ms_excel,
                nilai_mikrotik,
                nilai_kabel_lan,
                nilai_fiber_optic,
                nilai_hardware,
                nilai_perakitan_cpu,
                nilai_windows,
                ratarata_nonteknis,
                ratarata_teknis,
                ratarata_keseluruhan,
                kategori_nonteknis,
                kategori_teknis,
                kategori_keseluruhan
            )
            VALUES %s
            RETURNING id_penilaian, nisn
            """,
            data_penilaian,
            page_size=max(len(data_penilaian), 1),
        )

        penilaian_baru = {
            normalisasi_nisn(nisn): id_penilaian
            for id_penilaian, nisn in cursor.fetchall()
        }

        id_penilaian_map = {
            index: penilaian_baru[
                normalisasi_nisn(row["nisn"])
            ]
            for index, row in data.iterrows()
        }

        conn.commit()

        return {
            "id_dataset": id_dataset,
            "jumlah_data": len(data),
            "id_penilaian_map": id_penilaian_map,
            "sudah_ada": False,
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


# ============================================================
# SIMPAN PROSES CLUSTERING
# ============================================================

def simpan_proses_clustering(
    hasil,
    id_dataset,
    id_pengguna,
):
    """
    Menyimpan proses clustering, evaluasi,
    dan hasil cluster ke PostgreSQL.

    Versi hosting:
    1. Satu dataset + pengguna hanya memiliki satu proses.
    2. Proses lama digunakan kembali jika sudah tersedia.
    3. Evaluasi diperbarui menggunakan batch insert.
    4. Hasil clustering disimpan menggunakan batch insert.
    5. Mengurangi jumlah query ke Neon.
    """

    if hasil is None:
        raise ValueError(
            "Hasil clustering tidak ditemukan."
        )

    if id_dataset is None:
        raise ValueError(
            "ID dataset tidak ditemukan."
        )

    if id_pengguna is None:
        raise ValueError(
            "ID pengguna tidak ditemukan."
        )

    conn = get_connection()

    if conn is None:
        raise ConnectionError(
            "Koneksi ke database PostgreSQL gagal."
        )

    cursor = None

    try:
        cursor = conn.cursor()

        # ====================================================
        # 1. KUNCI PROSES
        # ====================================================

        kunci_proses = (
            f"clustering:{int(id_dataset)}:"
            f"{int(id_pengguna)}"
        )

        cursor.execute(
            "SELECT pg_advisory_xact_lock("
            "hashtext(%s)::bigint"
            ")",
            (kunci_proses,)
        )

        # ====================================================
        # 2. CEK PROSES YANG SUDAH ADA
        # ====================================================

        cursor.execute(
            """
            SELECT id_proses
            FROM proses_clustering
            WHERE id_dataset = %s
              AND id_pengguna = %s
            ORDER BY id_proses ASC
            LIMIT 1
            """,
            (
                int(id_dataset),
                int(id_pengguna),
            )
        )

        proses_lama = cursor.fetchone()

        if proses_lama is None:

            # Belum ada proses -> buat proses baru.
            cursor.execute(
                """
                INSERT INTO proses_clustering (
                    id_dataset,
                    id_pengguna,
                    k_terbaik_kmeans,
                    k_terbaik_kmedoids
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id_proses
                """,
                (
                    int(id_dataset),
                    int(id_pengguna),
                    int(
                        hasil["k_terbaik_kmeans"]
                    ),
                    int(
                        hasil["k_terbaik_kmedoids"]
                    ),
                )
            )

            id_proses = int(
                cursor.fetchone()[0]
            )

            sudah_ada = False

        else:

            # Proses sudah ada -> gunakan ID yang sama.
            id_proses = int(
                proses_lama[0]
            )

            sudah_ada = True

            # Perbarui hasil k terbaik.
            cursor.execute(
                """
                UPDATE proses_clustering
                SET
                    k_terbaik_kmeans = %s,
                    k_terbaik_kmedoids = %s,
                    tanggal_proses = CURRENT_TIMESTAMP
                WHERE id_proses = %s
                """,
                (
                    int(
                        hasil["k_terbaik_kmeans"]
                    ),
                    int(
                        hasil["k_terbaik_kmedoids"]
                    ),
                    id_proses,
                )
            )

            # Hapus hasil lama sebelum diganti hasil terbaru.
            cursor.execute(
                """
                DELETE FROM hasil_clustering
                WHERE id_proses = %s
                """,
                (id_proses,)
            )

            cursor.execute(
                """
                DELETE FROM evaluasi
                WHERE id_proses = %s
                """,
                (id_proses,)
            )

        # ====================================================
        # 3. SIMPAN EVALUASI SECARA BATCH
        # ====================================================

        df_evaluasi = (
            hasil["df_evaluasi"].copy()
        )

        data_evaluasi = []

        for _, row in df_evaluasi.iterrows():

            data_evaluasi.append(
                (
                    id_proses,
                    int(
                        row["Jumlah Cluster (k)"]
                    ),
                    ke_decimal(
                        row["Silhouette K-Means"]
                    ),
                    ke_decimal(
                        row["Silhouette K-Medoids"]
                    ),
                )
            )

        if data_evaluasi:

            execute_values(
                cursor,
                """
                INSERT INTO evaluasi (
                    id_proses,
                    jumlah_cluster,
                    silhouette_kmeans,
                    silhouette_kmedoids
                )
                VALUES %s
                """,
                data_evaluasi,
                page_size=max(
                    len(data_evaluasi),
                    1
                ),
            )

        # ====================================================
        # 4. AMBIL ID PENILAIAN SEKALIGUS
        # ====================================================

        hasil_df = (
            hasil["hasil_df"].copy()
        )

        if "nisn" not in hasil_df.columns:
            raise ValueError(
                "Kolom NISN tidak ditemukan "
                "pada hasil clustering."
            )

        cursor.execute(
            """
            SELECT
                id_penilaian,
                nisn
            FROM penilaian
            WHERE id_dataset = %s
            """,
            (int(id_dataset),)
        )

        daftar_penilaian = (
            cursor.fetchall()
        )

        penilaian_map = {}

        for id_penilaian, nisn in daftar_penilaian:

            nisn_normal = normalisasi_nisn(
                nisn
            )

            if nisn_normal in penilaian_map:
                raise ValueError(
                    "Ditemukan lebih dari satu "
                    "data penilaian untuk NISN "
                    f"{nisn_normal} pada dataset "
                    "yang sama."
                )

            penilaian_map[
                nisn_normal
            ] = int(id_penilaian)

        # ====================================================
        # 5. SIAPKAN HASIL CLUSTERING
        # ====================================================

        data_hasil = []

        for _, row in hasil_df.iterrows():

            nisn = normalisasi_nisn(
                row["nisn"]
            )

            if nisn not in penilaian_map:
                raise ValueError(
                    "Data penilaian tidak ditemukan "
                    f"untuk NISN {nisn}."
                )

            data_hasil.append(
                (
                    id_proses,
                    penilaian_map[nisn],
                    int(
                        row["cluster_kmeans"]
                    ),
                    int(
                        row["cluster_kmedoids"]
                    ),
                )
            )

        # ====================================================
        # 6. SIMPAN HASIL CLUSTERING SECARA BATCH
        # ====================================================

        if data_hasil:

            execute_values(
                cursor,
                """
                INSERT INTO hasil_clustering (
                    id_proses,
                    id_penilaian,
                    cluster_kmeans,
                    cluster_kmedoids
                )
                VALUES %s
                """,
                data_hasil,
                page_size=max(
                    len(data_hasil),
                    1
                ),
            )

        # ====================================================
        # 7. COMMIT
        # ====================================================

        conn.commit()

        return {
            "id_proses": id_proses,
            "jumlah_evaluasi": len(
                df_evaluasi
            ),
            "jumlah_hasil": len(
                hasil_df
            ),
            "sudah_ada": sudah_ada,
        }

    except Exception:

        conn.rollback()
        raise

    finally:

        if cursor is not None:
            cursor.close()

        conn.close()


# ============================================================
# AMBIL DAFTAR RIWAYAT PROSES
# ============================================================

def ambil_daftar_proses():
    """
    Mengambil daftar proses clustering yang
    telah tersimpan di PostgreSQL.
    """

    conn = get_connection()

    if conn is None:
        raise ConnectionError(
            "Koneksi ke database PostgreSQL gagal."
        )

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                pc.id_proses,
                pc.id_dataset,
                d.nama_dataset,
                pc.tanggal_proses,
                pc.k_terbaik_kmeans,
                pc.k_terbaik_kmedoids,
                u.nama_pengguna

            FROM proses_clustering pc

            JOIN dataset d
                ON d.id_dataset =
                   pc.id_dataset

            JOIN pengguna u
                ON u.id_pengguna =
                   pc.id_pengguna

            ORDER BY
                pc.id_proses DESC
            """
        )

        rows = (
            cursor.fetchall()
        )

        daftar_proses = []

        for row in rows:

            daftar_proses.append({
                "id_proses": row[0],
                "id_dataset": row[1],
                "nama_dataset": row[2],
                "tanggal_proses": row[3],
                "k_terbaik_kmeans": row[4],
                "k_terbaik_kmedoids": row[5],
                "nama_pengguna": row[6],
            })

        return daftar_proses

    finally:
        if cursor is not None:
            cursor.close()

        conn.close()


# ============================================================
# AMBIL HASIL PROSES DARI DATABASE
# ============================================================

def ambil_hasil_proses(
    id_proses
):
    """
    Mengambil hasil clustering dan evaluasi
    berdasarkan ID proses.
    """

    conn = get_connection()

    if conn is None:
        raise ConnectionError(
            "Koneksi ke database PostgreSQL gagal."
        )

    cursor = None

    try:
        cursor = conn.cursor()

        # ====================================================
        # 1. INFORMASI PROSES
        # ====================================================

        cursor.execute(
            """
            SELECT
                id_proses,
                id_dataset,
                k_terbaik_kmeans,
                k_terbaik_kmedoids,
                tanggal_proses

            FROM proses_clustering

            WHERE id_proses = %s
            """,
            (
                int(id_proses),
            )
        )

        proses = (
            cursor.fetchone()
        )

        if proses is None:
            raise ValueError(
                f"Proses dengan ID "
                f"{id_proses} "
                "tidak ditemukan."
            )

        # ====================================================
        # 2. HASIL EVALUASI
        # ====================================================

        cursor.execute(
            """
            SELECT
                jumlah_cluster,
                silhouette_kmeans,
                silhouette_kmedoids

            FROM evaluasi

            WHERE id_proses = %s

            ORDER BY
                jumlah_cluster
            """,
            (
                int(id_proses),
            )
        )

        rows_evaluasi = (
            cursor.fetchall()
        )

        df_evaluasi = (
            pd.DataFrame(
                rows_evaluasi,
                columns=[
                    "Jumlah Cluster (k)",
                    "Silhouette K-Means",
                    "Silhouette K-Medoids",
                ],
            )
        )

        for kolom in [
            "Silhouette K-Means",
            "Silhouette K-Medoids",
        ]:

            df_evaluasi[
                kolom
            ] = (
                pd.to_numeric(
                    df_evaluasi[
                        kolom
                    ],
                    errors="coerce",
                )
            )

        # ====================================================
        # 3. HASIL CLUSTERING + SISWA
        # ====================================================

        cursor.execute(
            """
            SELECT
                p.tahun,
                p.sumber_sheet,
                s.nama_siswa,
                s.nama_sekolah,
                s.kompetensi_keahlian,
                s.nisn,

                p.nilai_kedisiplinan,
                p.nilai_kerjasama,
                p.nilai_inisiatif,
                p.nilai_kerajinan,
                p.nilai_tanggung_jawab,
                p.nilai_sikap_perilaku,

                p.nilai_ms_word,
                p.nilai_ms_excel,
                p.nilai_mikrotik,
                p.nilai_kabel_lan,
                p.nilai_fiber_optic,
                p.nilai_hardware,
                p.nilai_perakitan_cpu,
                p.nilai_windows,

                hc.cluster_kmeans,
                hc.cluster_kmedoids

            FROM hasil_clustering hc

            JOIN penilaian p
                ON p.id_penilaian =
                   hc.id_penilaian

            JOIN siswa s
                ON s.nisn =
                   p.nisn

            WHERE
                hc.id_proses = %s

            ORDER BY
                p.id_penilaian
            """,
            (
                int(id_proses),
            )
        )

        rows_hasil = (
            cursor.fetchall()
        )

        kolom_hasil = [
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

            "cluster_kmeans",
            "cluster_kmedoids",
        ]

        hasil_df = (
            pd.DataFrame(
                rows_hasil,
                columns=kolom_hasil,
            )
        )

        # 14 atribut penilaian.
        kolom_nilai = [
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
        ]

        if not hasil_df.empty:

            hasil_df[
                kolom_nilai
            ] = (
                hasil_df[
                    kolom_nilai
                ]
                .apply(
                    pd.to_numeric,
                    errors="coerce",
                )
            )

        # ====================================================
        # 4. NILAI SILHOUETTE TERBAIK
        # ====================================================

        k_terbaik_kmeans = int(
            proses[2]
        )

        k_terbaik_kmedoids = int(
            proses[3]
        )

        baris_kmeans = (
            df_evaluasi[
                df_evaluasi[
                    "Jumlah Cluster (k)"
                ]
                == k_terbaik_kmeans
            ]
        )

        baris_kmedoids = (
            df_evaluasi[
                df_evaluasi[
                    "Jumlah Cluster (k)"
                ]
                == k_terbaik_kmedoids
            ]
        )

        if baris_kmeans.empty:
            raise ValueError(
                "Nilai evaluasi terbaik "
                "K-Means tidak ditemukan."
            )

        if baris_kmedoids.empty:
            raise ValueError(
                "Nilai evaluasi terbaik "
                "K-Medoids tidak ditemukan."
            )

        silhouette_terbaik_kmeans = float(
            baris_kmeans.iloc[0][
                "Silhouette K-Means"
            ]
        )

        silhouette_terbaik_kmedoids = float(
            baris_kmedoids.iloc[0][
                "Silhouette K-Medoids"
            ]
        )

        # ====================================================
        # 5. MENGEMBALIKAN HASIL
        # ====================================================

        return {
            "id_proses": (
                proses[0]
            ),
            "id_dataset": (
                proses[1]
            ),
            "tanggal_proses": (
                proses[4]
            ),

            "hasil_df": (
                hasil_df
            ),

            "df_evaluasi": (
                df_evaluasi
            ),

            "k_terbaik_kmeans": (
                k_terbaik_kmeans
            ),

            "k_terbaik_kmedoids": (
                k_terbaik_kmedoids
            ),

            "silhouette_terbaik_kmeans": (
                silhouette_terbaik_kmeans
            ),

            "silhouette_terbaik_kmedoids": (
                silhouette_terbaik_kmedoids
            ),
        }

    finally:
        if cursor is not None:
            cursor.close()

        conn.close()