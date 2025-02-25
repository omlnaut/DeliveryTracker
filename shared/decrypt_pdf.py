from io import BufferedReader
from pathlib import Path

from PyPDF2 import PdfFileReader, PdfFileWriter


def remove_password_from_pdf(
    pdf_file: BufferedReader, password: str, output_path: Path | None = None
) -> Path:
    # read to lib
    pdf = PdfFileReader(pdf_file)
    pdf.decrypt(password)

    # decrypt into new object
    pdf_writer = PdfFileWriter()
    for page in pdf.pages:
        pdf_writer.addPage(page)

    # write to file
    if output_path is None:
        output_path = Path(pdf_file.name).with_suffix(".decrypted.pdf")

    with output_path.open("wb") as output_pdf:
        pdf_writer.write(output_pdf)

    return output_path
