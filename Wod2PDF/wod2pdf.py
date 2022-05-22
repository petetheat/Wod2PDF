import sqlite3
from fpdf import FPDF
import os

import numpy as np

from datetime import datetime
import locale


locale.setlocale(locale.LC_ALL, "german")


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
        wod_type = wod_data[4]
        if 'AMRAP' in wod_type:
            wod_header = f'{wod_data[5]}min {wod_type}'
        elif wod_type == 'RFT Varying Reps':
            wod_header = wod_type
        elif 'RFT' in wod_type:
            wod_header = f'{wod_data[5]} {wod_type}'
        elif wod_type == 'FGB':
            wod_header = f'{wod_type}: 3 rounds, 1min per station'
        else:
            wod_header = wod_type

        self.cursor.execute(f"SELECT * from wodplannerapp_strengthmovement WHERE wod_id=={wid}")
        strength_data = self.cursor.fetchall()
        header_strength = [i[0] for i in self.cursor.description]

        self.cursor.execute(f"SELECT * from wodplannerapp_wodmovement WHERE wod_id=={wid}")
        wod_contents = self.cursor.fetchall()

        header.extend(header_strength)
        wod_data.extend(strength_data)

        header_date = datetime.strptime(wod_data[1], '%Y-%m-%d %H:%M:%S')
        strength_comment = wod_data[3] if wod_data[3] != '-' else ''
        wod_comment = wod_data[6] if wod_data[6] != '-' else ''

        return datetime.strftime(header_date, '%d. %B %Y'), strength_data, strength_comment, wod_comment, wod_header, \
               wod_contents

    @classmethod
    def write_pdf(cls, db, filename):
        wod = cls(db)
        pdf = PDF()
        for i, wod_id in enumerate(wod.ids):
            header_date, strength_data, strength_comment, wod_comment, wod_type, wod_data = wod._get_wod(wod_id)
            pdf.write_wods(i+1, header_date, strength_data, strength_comment, wod_comment, wod_type, wod_data)
        pdf.output(filename, 'F')


def get_cell_width(data):
    cell1_length = 0
    cell2_length = 0
    cell3_length = 0
    for i in data:
        cell1_length = len(str(i[2])) if len(str(i[2])) > cell1_length else cell1_length
        cell2_length = len(str(i[1])) if len(str(i[1])) > cell2_length else cell2_length
        cell3_length = len(str(i[3])) if len(str(i[3])) > cell3_length else cell3_length

    cell1_width = int(cell1_length*3) if cell1_length > 0 else 1
    cell2_width = int(cell2_length * 3) if cell2_length > 0 else 1
    cell3_width = int(cell3_length * 3) if cell3_length > 0 else 1

    return cell1_width, cell2_width, cell3_width


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
        self.cell(0, 10, f'Seite {str(self.page_no())}', 0, 0, 'C')

    def wod_title(self, num, label):
        # Arial 12
        self.set_font('Arial', 'B', 16)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, 'Workout %d: %s' % (num, label), 0, 1, 'L', 1)
        # Line break
        self.ln(4)

    def wod_strength(self, strength_data, strength_comment):
        self.set_font('Arial', 'B', 14)
        self.cell(10, 6, 'Strength/Skill:', 0, 0, 'L', 0)
        self.set_font('Arial', '', 12)
        c1, c2, c3 = get_cell_width(strength_data)
        for movement_data in strength_data:
            self.ln()
            self.cell(c1, 6, f'{movement_data[2]}', 0, 0, 'L', 0)
            self.cell(c2, 6, f'{movement_data[1]}', 0, 0, 'L', 0)
        self.ln()
        self.set_font('Arial', 'I', 12)
        self.multi_cell(0, 6, f'{strength_comment}', 0, 0, 'L', 0)
        self.ln()

    def wod_wod(self, wod_type, wod_data, wod_comment):
        self.set_font('Arial', 'B', 14)
        self.cell(10, 6, 'WOD:', 0, 0, 'L', 0)
        self.set_font('Arial', '', 12)
        self.ln()
        self.cell(10, 6, f'{wod_type}', 0, 0, 'L', 0)

        c1, c2, c3 = get_cell_width(wod_data)

        for movement_data in wod_data:
            self.ln()
            self.cell(c1, 6, f'{movement_data[2]}', 0, 0, 'L', 0)
            self.cell(c2, 6, f'{movement_data[1]}', 0, 0, 'L', 0)
            weight = movement_data[3] if movement_data[3] != '-' else ''
            self.cell(c3, 6, f'{weight}', 0, 0, 'L', 0)
        self.ln()
        # self.cell(10, 6, f'{wod_comment}', 0, 0, 'L', 0)
        self.set_font('Arial', 'I', 12)
        self.multi_cell(0, 6, f'{wod_comment}', 0, 0, 'L', 0)
        self.ln()

    def write_wods(self, wod_i, header_date, strength_data, strength_comment, wod_comment, wod_type, wod_data):
        self.add_page()
        self.wod_title(wod_i, header_date)
        self.wod_strength(strength_data, strength_comment)
        self.wod_wod(wod_type, wod_data, wod_comment)


if __name__ == '__main__':
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Times', '', 12)
    for l in range(1, 41):
        pdf.cell(0, 10, 'Printing line number ' + str(l), 0, 1)
    pdf.output('tuto2.pdf', 'F')
