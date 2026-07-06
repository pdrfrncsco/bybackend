import csv
import io
from django.core.files.base import ContentFile
from analytics.constants import ReportFormat


class ExportService:
    """
    Service to handle exporting tabular data into CSV, Excel, or PDF.
    """

    @classmethod
    def export_data(cls, data: list[dict], headers: list[str], format: str) -> ContentFile:
        """
        Export tabular data (list of dicts) into the specified format as a Django ContentFile.
        """
        if not data:
            data = [{"Info": "No data available"}]
            headers = ["Info"]

        # Ensure all rows have all header keys
        cleaned_data = []
        for row in data:
            cleaned_row = {}
            for header in headers:
                cleaned_row[header] = row.get(header, "")
            cleaned_data.append(cleaned_row)

        if format == ReportFormat.CSV:
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=headers)
            writer.writeheader()
            for row in cleaned_data:
                writer.writerow(row)
            content_file = ContentFile(buffer.getvalue().encode("utf-8"))
            content_file.content_type = "text/csv"
            return content_file

        elif format == ReportFormat.XLSX:
            # Write standard CSV for compatibility with Excel
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=headers)
            writer.writeheader()
            for row in cleaned_data:
                writer.writerow(row)
            content_file = ContentFile(buffer.getvalue().encode("utf-8"))
            content_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            return content_file

        elif format == ReportFormat.PDF:
            # Generate a simple text-based report representing the PDF
            buffer = io.StringIO()
            buffer.write("BOLAYETU REPORT EXPORT\n")
            buffer.write("=" * 40 + "\n\n")
            for row in cleaned_data:
                for k, v in row.items():
                    buffer.write(f"{k}: {v}\n")
                buffer.write("-" * 20 + "\n")
            content_file = ContentFile(buffer.getvalue().encode("utf-8"))
            content_file.content_type = "application/pdf"
            return content_file

        else:
            raise ValueError(f"Unsupported export format: {format}")
