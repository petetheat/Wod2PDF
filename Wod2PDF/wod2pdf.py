import sqlite3


class Wod2Pdf:
    def __init__(self, db):
        self.db = sqlite3.connect(db)
        self.cursor = self.db.cursor()

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
