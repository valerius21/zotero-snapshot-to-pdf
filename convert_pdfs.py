import shutil
from pathlib import Path
from typing import assert_type

import tomllib
import watchfiles
from cachier import cachier
from loguru import logger
from pychromepdf import ChromePDF
from pyzotero import zotero


class Converter:
    def __init__(
        self,
        library_id: str,
        zotero_api_key: str,
        library_type="user",
        chrome_path=r"/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome",
        tmp_dir="/tmp/zotero-converter",
    ) -> None:
        self.library_id = library_id
        self.zotero_api_key = zotero_api_key
        self.library_type = library_type
        self.chrome_path = chrome_path
        self.tmp_dir = tmp_dir
        self.zot = zotero.Zotero(library_id, library_type, zotero_api_key)

    def __repr__(self) -> str:
        return f"{self.library_id} {self.library_type} {self.zotero_api_key} {self.chrome_path} {self.tmp_dir}"

    def create_tmp_dirs(self) -> None:
        logger.info("Initializsing")
        # create tempdir, when not exisitent
        path = Path(self.tmp_dir)
        path.mkdir(exist_ok=True)

    def cleanup(self) -> None:
        logger.info("Cleaning up local directories")
        path = Path(self.tmp_dir)
        shutil.rmtree(path)
        shutil.rmtree("~/.temp/.cache")

    @cachier(cache_dir="~/.temp/.cache")
    def write_file_to_pdf(self, key, file_href) -> tuple[str, Path]:
        logger.info(f"Writing file to PDF {key} {file_href}")
        *_, file_id = file_href.split("/")
        cpdf = ChromePDF(self.chrome_path)

        file_data = self.zot.file(file_id)
        html_contents = str(file_data)[2:].replace("\\n", "")

        logger.info(f"converting {key}")
        file_path = f"{self.tmp_dir}/generated_{key}.pdf"
        with open(file_path, "w") as file:
            if cpdf.html_to_pdf(html_contents, file):
                logger.info(f"success {key}")
            else:
                raise Exception("error writing file")
        return (key, Path(file_path))

    @cachier(cache_dir="~/.temp/.cache")
    def upload_file_to_zotero(self, key: str, file_path: Path) -> None:
        logger.info(f"Uploading PDF to Zotero {key} {file_path}")
        res = self.zot.attachment_simple([str(file_path)], key)
        logger.info(res)

    @staticmethod
    def is_html(data: dict) -> bool:
        return data["contentType"] == "text/html"

    @cachier(cache_dir="~/.temp/.cache")
    def find_html_link(self, elements: dict[str, str]) -> str | None:
        links = [(e["href"], e["type"]) for e in elements.values()]
        for link, _type in links:
            if _type == "text/html":
                return link.replace("/file", "")
        return None

    def discover_html_attachments(self) -> None:
        logger.info(f"Discovering files in online Zotero library {self.library_id}")
        for item in self.zot.items(itemType="attachment"):
            assert_type(item, dict)
            data = item["data"]
            if not Converter.is_html(data):
                continue
            parent_item = data["parentItem"]
            link = self.find_html_link(item["links"])
            if not link:
                continue
            try:
                (key, path) = self.write_file_to_pdf(parent_item, link)
                logger.info("Uploading")
                self.upload_file_to_zotero(key, path)
            except Exception as e:
                logger.error(e)
                logger.error(f"{item}")


def load_toml() -> dict:
    """load toml config"""
    with open("config.toml", "rb") as f:
        toml_data: dict = tomllib.load(f)
        return toml_data


def create_converter(zotero_cfg: dict, system_cfg: dict) -> Converter:
    """Creates a converter with the given config objects"""
    return Converter(
        library_id=zotero_cfg["library_id"],
        zotero_api_key=zotero_cfg["zotero_api_key"],
        chrome_path=system_cfg["path_to_chrome_exe"],
        tmp_dir=system_cfg["save_dir"],
    )


def get_watch_dir(zotero_cfg: dict) -> Path:
    """Figures out, where the Zotero directory is"""
    return Path(zotero_cfg["zotero_directory"])


def get_config() -> tuple[dict, dict]:
    """Loads the config into fitting objects"""
    config = load_toml()
    zotero_cfg = config["zotero"]
    system_cfg = config["system"]

    return zotero_cfg, system_cfg


def execute_on_zotero_change(converter: Converter, zotero_cfg: dict) -> None:
    """Runs the converter on every file change after its initial run"""
    converter.discover_html_attachments()
    logger.warn("File watcher is disabled")
    logger.info("done")
    # logger.info("Starting to watch for file changes")
    # watch_path = get_watch_dir(zotero_cfg)
    # for _ in watchfiles.watch(watch_path):
    #     logger.info("File changes detected")
    #     converter.discover_html_attachments()


def main():
    """Entry Point"""
    zotero_cfg, system_cfg = get_config()
    converter = create_converter(zotero_cfg, system_cfg)
    converter.create_tmp_dirs()
    execute_on_zotero_change(converter, zotero_cfg)


if __name__ == "__main__":
    # Display warnings, because they are not part of the program
    logger.warning("Only the first 100 documents are currently supported")
    main()
