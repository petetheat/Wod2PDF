import sqlite3
from fpdf import FPDF
import os

import numpy as np

from datetime import datetime


class Wod2Pdf:
    def __init__(self, db):
        self.db = sqlite3.connect(db)
        self.cursor = self.db.cursor()
        self.ids = self.get_sorted_id()

    def get_sorted_id(self):
        self.cursor.execute("SELECT * from wodplannerapp_wod;")
        all_data = self.cursor.fetchall()

        ids = np.array([i[0] for i in all_data])
        dates = np.array([datetime.strptime(i[1], '%Y-%m-%d %H:%M:%S') for i in all_data])

        idx_sorted = np.argsort(dates)

        return ids[idx_sorted]

    def _get_wod(self, wid):
        self.cursor.execute(f"SELECT * from wodplannerapp_wod WHERE id={wid};")
        wod_data = list(self.cursor.fetchone())
        header = [i[0] for i in self.cursor.description]

        self.cursor.execute(f"SELECT * from wodplannerapp_strengthmovement WHERE wod_id=={wid}")
        strength_data = self.cursor.fetchall()
        header_strength = [i[0] for i in self.cursor.description]

        header.extend(header_strength)
        wod_data.extend(strength_data)

        return dict(zip(header, wod_data))


    @classmethod
    def write_pdf(cls, db, filename):
        cls(db)


class PDF(FPDF):
    def header(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        self.image(os.path.join(file_path, 'images/carabao_logo.png'), 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(80, 10, 'Carabao WODs', 0, 0, 'C')
        # Line break
        self.ln(20)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Seite ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def wod_title(self, num, label):
        # Arial 12
        self.set_font('Arial', '', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, 'Chapter %d : %s' % (num, label), 0, 1, 'L', 1)
        # Line break
        self.ln(4)

    def write_wods(self, wod_i):
        pass


if __name__ == '__main__':
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Times', '', 12)
    for l in range(1, 41):
        pdf.cell(0, 10, 'Printing line number ' + str(l), 0, 1)
    pdf.output('tuto2.pdf', 'F')
