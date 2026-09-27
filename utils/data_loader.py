from pathlib import Path

import pandas as pd


# Lokasi dataset bawaan yang digunakan oleh aplikasi.
DEFAULT_DATASET_PATH = Path(
    "data/dataset_final_14_atribut_2021_2025.xlsx"
)

# Nama sheet utama yang berisi 300 data siswa dan 14 atribut.
DEFAULT_SHEET_NAME = "dataset_final_14_atribut"


def load_default_dataset():
    """
    Fungsi ini digunakan untuk membaca dataset bawaan
    dari folder data.

    Dataset dibaca dari sheet dataset_final_14_atribut.
    Kolom NISN dibaca sebagai teks agar angka nol di bagian
    awal tidak hilang.
    """

    # Memastikan file dataset tersedia.
    if not DEFAULT_DATASET_PATH.exists():
        raise FileNotFoundError(
            "Dataset bawaan tidak ditemukan pada lokasi: "
            f"{DEFAULT_DATASET_PATH}"
        )

    try:
        # Membaca dataset dari sheet utama.
        df = pd.read_excel(
            DEFAULT_DATASET_PATH,
            sheet_name=DEFAULT_SHEET_NAME,
            dtype={
                "nisn": "string",
            },
        )

    except ValueError as error:
        raise ValueError(
            f"Sheet '{DEFAULT_SHEET_NAME}' tidak ditemukan "
            f"pada file {DEFAULT_DATASET_PATH.name}."
        ) from error

    except Exception as error:
        raise RuntimeError(
            "Terjadi kesalahan ketika membaca dataset bawaan."
        ) from error

    # Memastikan dataset tidak kosong.
    if df.empty:
        raise ValueError(
            "Dataset bawaan berhasil dibaca, tetapi tidak memiliki data."
        )

    # Membersihkan spasi pada nama kolom.
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # Membersihkan format kolom NISN.
    if "nisn" in df.columns:
        df["nisn"] = (
            df["nisn"]
            .astype("string")
            .str.strip()
            .str.replace(
                r"\.0$",
                "",
                regex=True,
            )
        )

    return df