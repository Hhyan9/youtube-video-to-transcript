thonimport csv
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List

from openpyxl import Workbook
from xml.etree.ElementTree import Element, SubElement, ElementTree

logger = logging.getLogger(__name__)

class ExportManager:
    """
    Handles exporting transcript data into various formats:
    JSON, CSV, Excel, HTML, and XML.
    """

    def export(self, data: List[Dict[str, str]], output_path: Path, fmt: str) -> None:
        if not isinstance(data, list):
            raise TypeError("Data must be a list of dictionaries.")

        fmt = fmt.lower()
        output_path = self._ensure_extension(output_path, fmt)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Exporting data to %s as %s", output_path, fmt)

        if fmt == "json":
            self._export_json(data, output_path)
        elif fmt == "csv":
            self._export_csv(data, output_path)
        elif fmt == "excel":
            self._export_excel(data, output_path)
        elif fmt == "html":
            self._export_html(data, output_path)
        elif fmt == "xml":
            self._export_xml(data, output_path)
        else:
            raise ValueError(f"Unsupported export format: {fmt}")

    @staticmethod
    def _ensure_extension(path: Path, fmt: str) -> Path:
        if path.suffix:
            return path

        ext_map = {
            "json": ".json",
            "csv": ".csv",
            "excel": ".xlsx",
            "html": ".html",
            "xml": ".xml",
        }
        ext = ext_map.get(fmt, "")
        return path.with_suffix(ext)

    @staticmethod
    def _fieldnames(data: Iterable[Dict[str, str]]) -> List[str]:
        names: List[str] = []
        for row in data:
            for key in row.keys():
                if key not in names:
                    names.append(key)
        return names

    @staticmethod
    def _export_json(data: List[Dict[str, str]], path: Path) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _export_csv(self, data: List[Dict[str, str]], path: Path) -> None:
        if not data:
            logger.warning("No data to export; creating an empty CSV file.")
            with path.open("w", encoding="utf-8", newline="") as f:
                f.write("")
            return

        fieldnames = self._fieldnames(data)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    def _export_excel(self, data: List[Dict[str, str]], path: Path) -> None:
        wb = Workbook()
        ws = wb.active
        ws.title = "Transcripts"

        if not data:
            logger.warning("No data to export; creating an empty Excel file.")
            wb.save(path)
            return

        fieldnames = self._fieldnames(data)
        ws.append(fieldnames)

        for row in data:
            ws.append([row.get(field, "") for field in fieldnames])

        wb.save(path)

    def _export_html(self, data: List[Dict[str, str]], path: Path) -> None:
        html_parts: List[str] = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '  <meta charset="UTF-8" />',
            "  <title>YouTube Transcripts</title>",
            "</head>",
            "<body>",
            "  <h1>YouTube Transcripts</h1>",
        ]

        if not data:
            html_parts.append("  <p>No data available.</p>")
            html_parts.append("</body></html>")
            with path.open("w", encoding="utf-8") as f:
                f.write("\n".join(html_parts))
            return

        fieldnames = self._fieldnames(data)
        html_parts.append("  <table border='1' cellspacing='0' cellpadding='4'>")
        html_parts.append("    <thead>")
        html_parts.append("      <tr>")
        for name in fieldnames:
            html_parts.append(f"        <th>{name}</th>")
        html_parts.append("      </tr>")
        html_parts.append("    </thead>")
        html_parts.append("    <tbody>")

        for row in data:
            html_parts.append("      <tr>")
            for name in fieldnames:
                value = row.get(name, "")
                escaped = (
                    str(value)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                html_parts.append(f"        <td>{escaped}</td>")
            html_parts.append("      </tr>")

        html_parts.append("    </tbody>")
        html_parts.append("  </table>")
        html_parts.append("</body>")
        html_parts.append("</html>")

        with path.open("w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))

    @staticmethod
    def _export_xml(data: List[Dict[str, str]], path: Path) -> None:
        root = Element("transcripts")

        for row in data:
            video_el = SubElement(root, "video")
            for key, value in row.items():
                child = SubElement(video_el, key)
                child.text = str(value)

        tree = ElementTree(root)
        tree.write(path, encoding="utf-8", xml_declaration=True)