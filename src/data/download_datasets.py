#!/usr/bin/env python3
"""Download and prepare the project's public waste-image datasets."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Optional

import requests
from tqdm import tqdm


TRASHNET_ARCHIVE_URL = (
    "https://github.com/garythung/trashnet/archive/refs/heads/master.zip"
)
TACO_ANNOTATIONS_URL = (
    "https://raw.githubusercontent.com/pedropro/TACO/master/data/annotations.json"
)
KAGGLE_DATASET = "techsash/waste-classification-data"
KAGGLE_SETUP_MESSAGE = (
    "Kaggle credentials are not configured. Create an API token in Kaggle "
    "account settings, then save kaggle.json to ~/.kaggle/kaggle.json and run "
    "'chmod 600 ~/.kaggle/kaggle.json', or export both KAGGLE_USERNAME and "
    "KAGGLE_KEY. Kaggle download skipped."
)


def positive_int(value: str) -> int:
    """Parse a positive integer for the optional TACO sample limit."""
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if result <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result


def download_file(
    session: requests.Session,
    url: str,
    destination: Path,
    description: str,
    show_progress: bool = True,
) -> None:
    """Stream a URL to disk and atomically replace the destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_name(destination.name + ".part")
    try:
        with session.get(url, stream=True, timeout=(15, 90)) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0)) or None
            progress = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=description,
                disable=not show_progress,
            )
            try:
                with temporary_path.open("wb") as output_file:
                    for chunk in response.iter_content(chunk_size=1024 * 64):
                        if chunk:
                            output_file.write(chunk)
                            progress.update(len(chunk))
            finally:
                progress.close()
        temporary_path.replace(destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def safe_extract_zip(archive_path: Path, destination: Path) -> None:
    """Extract a ZIP only when every member remains inside destination."""
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            member_path = PurePosixPath(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(
                    "Unsafe path in ZIP archive: {}".format(member.filename)
                )
            extracted_path = (destination / Path(*member_path.parts)).resolve()
            if os.path.commonpath(
                (str(destination_root), str(extracted_path))
            ) != str(destination_root):
                raise ValueError(
                    "Unsafe path in ZIP archive: {}".format(member.filename)
                )
        archive.extractall(destination)


def download_trashnet(output_dir: Path, session: requests.Session) -> None:
    """Download and extract the upstream TrashNet GitHub repository archive."""
    dataset_dir = output_dir / "trashnet"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".trashnet-download-", dir=str(output_dir)
    ) as temporary_dir:
        temporary_root = Path(temporary_dir)
        archive_path = temporary_root / "trashnet.zip"
        extraction_dir = temporary_root / "extracted"
        download_file(
            session,
            TRASHNET_ARCHIVE_URL,
            archive_path,
            "Downloading TrashNet",
        )
        safe_extract_zip(archive_path, extraction_dir)

        children = list(extraction_dir.iterdir())
        source_dir = (
            children[0]
            if len(children) == 1 and children[0].is_dir()
            else extraction_dir
        )
        shutil.copytree(source_dir, dataset_dir, dirs_exist_ok=True)
    print("TrashNet is available at {}".format(dataset_dir))


def taco_image_destination(images_dir: Path, file_name: str) -> Path:
    """Resolve a COCO relative file name without allowing path traversal."""
    normalized_name = file_name.replace("\\", "/")
    relative_path = PurePosixPath(normalized_name)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Unsafe TACO image path: {}".format(file_name))
    destination = images_dir.joinpath(*relative_path.parts).resolve()
    images_root = images_dir.resolve()
    if os.path.commonpath((str(images_root), str(destination))) != str(images_root):
        raise ValueError("Unsafe TACO image path: {}".format(file_name))
    return destination


def download_taco(
    output_dir: Path,
    session: requests.Session,
    limit: Optional[int] = None,
) -> None:
    """Download TACO's COCO annotations and referenced images."""
    taco_dir = output_dir / "taco"
    taco_dir.mkdir(parents=True, exist_ok=True)
    annotations_path = taco_dir / "annotations.json"
    download_file(
        session,
        TACO_ANNOTATIONS_URL,
        annotations_path,
        "Downloading TACO annotations",
    )
    with annotations_path.open("r", encoding="utf-8") as annotation_file:
        annotations = json.load(annotation_file)

    images = annotations.get("images")
    if not isinstance(images, list):
        raise ValueError("TACO annotations JSON does not contain an images list")
    if limit is not None:
        images = images[:limit]

    images_dir = taco_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    print("Downloading {} TACO images".format(len(images)))
    with tqdm(total=len(images), unit="image", desc="TACO images") as progress:
        for image in images:
            file_name = image.get("file_name")
            image_url = image.get("flickr_url") or image.get("coco_url")
            if not file_name or not image_url:
                raise ValueError(
                    "TACO image record is missing file_name or image URL"
                )
            destination = taco_image_destination(images_dir, file_name)
            if destination.is_file() and destination.stat().st_size > 0:
                progress.update(1)
                continue
            download_file(
                session,
                image_url,
                destination,
                "Downloading {}".format(file_name),
                show_progress=False,
            )
            progress.update(1)

    print("TACO data is available at {}".format(taco_dir))


def has_kaggle_credentials() -> bool:
    """Return whether Kaggle's standard token file or environment keys exist."""
    token_file = Path.home() / ".kaggle" / "kaggle.json"
    environment_credentials = bool(
        os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")
    )
    return token_file.is_file() or environment_credentials


def download_kaggle(output_dir: Path) -> bool:
    """Download and extract the Kaggle dataset when credentials are available."""
    if not has_kaggle_credentials():
        print(KAGGLE_SETUP_MESSAGE, file=sys.stderr)
        return False

    kaggle_dir = output_dir / "kaggle"
    kaggle_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "kaggle",
        "datasets",
        "download",
        "-d",
        KAGGLE_DATASET,
        "-p",
        str(kaggle_dir),
        "--unzip",
    ]
    subprocess.run(command, check=True)
    print("Kaggle data is available at {}".format(kaggle_dir))
    return True


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Download TACO, TrashNet, and Kaggle waste datasets."
    )
    parser.add_argument(
        "--dataset",
        choices=("all", "trashnet", "taco", "kaggle"),
        default="all",
        help="Dataset to download (default: all).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory for downloaded datasets (default: data/raw).",
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        help="Maximum number of TACO images to download; applies to taco/all.",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.dataset not in ("all", "taco"):
        parser.error("--limit can only be used with --dataset taco or all")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    datasets = (
        ("trashnet", "taco", "kaggle")
        if args.dataset == "all"
        else (args.dataset,)
    )

    try:
        with requests.Session() as session:
            session.headers.update(
                {"User-Agent": "TrashNet-Germany dataset downloader"}
            )
            for dataset in datasets:
                if dataset == "trashnet":
                    download_trashnet(output_dir, session)
                elif dataset == "taco":
                    download_taco(output_dir, session, args.limit)
                else:
                    download_kaggle(output_dir)
    except (
        requests.RequestException,
        OSError,
        ValueError,
        zipfile.BadZipFile,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        print("Dataset download failed: {}".format(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
