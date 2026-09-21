import logging
import os
import sys

import pymupdf

from cmj.utils import ProcessoExterno

logger = logging.getLogger(__name__)


class Pdf2PdfA:
    """
    Class responsible for converting PDF files to PDF/A format using ocrmypdf.

    Attributes:
        in_path (str): Path to the input PDF file.
        jobs (int): Number of parallel jobs to run.
        ocr (bool): Whether to perform OCR on the PDF.
        level (int): Processing level for the output PDF/A.
        verbose (int): Verbosity level for logging.
        doc (pymupdf.Document): Opened PDF document.
        folder (str): Folder containing the input PDF.
        filename (str): Filename of the input PDF.
        filename_noext (str): Filename of the input PDF without extension.

        level_0 (int): Level 0 for the output PDF/A.
            Transforma o arquivo em PDF/A com skip-text.
        level_1 (int): Level 1 for the output PDF/A.
            Transforma o arquivo em PDF/A com redo-ocr.
        level_2 (int): Level 2 for the output PDF/A.
            Transforma o arquivo em PDF/A com redo-ocr e compressão adicional.
        level_3 (int): Level 3 for the output PDF/A.
            Transforma o arquivo em PDF/A com force-ocr.
        level_4 (int): Level 4 for the output PDF/A.
            Transforma o arquivo em PDF/A com force-ocr e compressão máxima via multiprocessing.

    """

    def __init__(self, in_path, jobs, ocr=True, level=3, verbose=-1):
        self.in_path = in_path
        self.jobs = jobs
        self.ocr = ocr
        self.level = level
        self.verbose = verbose

        self.doc = pymupdf.open(in_path)

        self.folder = os.path.dirname(in_path)
        self.filename = os.path.basename(in_path)
        self.filename_noext = os.path.splitext(self.filename)[0]

    def execute(self):
        self._convert()

    def _convert(self):

        if self.level == 1:
            self._to_pdfa_levels(extras_params=["--redo-ocr"])
        elif self.level == 2:
            self._to_pdfa_levels(extras_params=["--redo-ocr", "--optimize 2"])
        elif self.level == 3:
            self._to_pdfa_levels(extras_params=["--force-ocr", "--optimize 2"])
        elif self.level == 4:
            self._to_pdfa_high_compress()
        else:
            self._to_pdfa_levels(extras_params=["--skip-text"])

    def _mount_command(self, in_path, out_path, extras_params=[]):
        if not self.ocr:
            extras_params.append("--ocr-engine none")

        cmd = (
            [
                "{}/ocrmypdf".format("/".join(sys.executable.split("/")[:-1])),
                "-l por",
                f"-v {self.verbose}" if self.verbose >= 0 else "-q",
                f"-j {self.jobs}",
                "--output-type pdfa-2",
            ]
            + extras_params
            + [in_path, out_path]
        )

        return cmd

    def _execute_command(self, cmd, timeout=600):
        logger.info("Executing command: %s", cmd)
        p = ProcessoExterno(cmd, logger=logger, silent=self.verbose < 0)
        r, out, err = p.run(timeout=timeout)
        logger.info("Command executed with return code: %s", r)
        if err:
            logger.error("Command Log: %s", err)
        return r, out, err

    def _to_pdfa_levels(self, extras_params=[]):
        logger.info(
            "Converting PDF to PDF/A with level=%s: %s", self.level, self.in_path
        )

        out_path = os.path.join(self.folder, f"{self.filename_noext}_pdfa.pdf")
        cmd = self._mount_command(self.in_path, out_path, extras_params=extras_params)

        r, out, err = self._execute_command(cmd)
        if r != 0:
            logger.error("Failed to convert PDF to PDF/A: %s", self.in_path)
            logger.error("Command output: %s", out)
            logger.error("Command error: %s", err)
            return
        logger.info("Successfully converted PDF to PDF/A: %s", out_path)
        return out_path, r, out, err
