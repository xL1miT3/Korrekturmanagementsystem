from flask import Flask, render_template, request, redirect, url_for, Blueprint
from flask_sqlalchemy import SQLAlchemy
from time import gmtime, strftime

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

# Tabelle für Benutzer
class Benutzer(db.Model):
    benutzer_ID = db.Column("Benutzer_ID", db.Integer, primary_key=True)
    benutzername = db.Column("Benutzername", db.String(50))
    passwort = db.Column("Passwort", db.String(50))
    # Tutor / Admin -> berechtigt Fehler zu beheben, Student -> nur berechtigt Fehler hinzuzufügen
    status = db.Column("Status", db.String(50))

    def __init__(self, benutzer_ID, benutzername, passwort, status):
        self.benutzer_ID = benutzer_ID
        self.benutzername = benutzername
        self.passwort = passwort
        self.status = status

# Tabelle für Kurse
class Kurse(db.Model):
    kurs_ID = db.Column("Kurs_ID", db.Integer, primary_key=True)
    kursname = db.Column("Kursname", db.String(50))
    kurs_abkuerzung = db.Column("Abkuerzung", db.String(50))

    def __int__(self,  kurs_ID, kursname, kurs_abkuerzung):
        self.kurs_ID = kurs_ID
        self.kursname = kursname
        self.kurs_abkuerzung = kurs_abkuerzung

# Tabelle für belegte Kurse
class Belegte_kurse(db.Model):
    id = db.Column("ID", db.Integer, primary_key=True)
    kurse_ID = db.Column("Kurs_ID", db.Integer, db.ForeignKey("kurse.Kurs_ID"))
    benutzer_ID = db.Column("Benutzer_ID", db.Integer, db.ForeignKey("benutzer.Benutzer_ID"))

    def __int__(self,  kurse_ID, benutzer_ID):
        self.kurse_ID = kurse_ID
        self.benutzer_ID = benutzer_ID

# Tabelle für die Fehlermeldungen
class Fehler(db.Model):
    fehler_ID = db.Column("Fehler_ID", db.Integer, primary_key=True)
    fehlerquelle = db.Column("Fehlerquelle", db.String(50))
    lektion = db.Column("Lektion", db.String(50))
    art_des_fehlers = db.Column("Art_des_Fehlers", db.String(50))
    pos_im = db.Column("Position", db.String(50))
    kommentar = db.Column("Kommentar", db.String(500))
    bearbeitungszustand = db.Column("Bearbeitungszustand", db.String(50))
    kurs_ID = db.Column("Kurs_ID", db.Integer, db.ForeignKey("kurse.Kurs_ID"))
    benutzer_ID = db.Column("Benutzer_ID", db.Integer, db.ForeignKey("benutzer.Benutzer_ID"))
    datum_erstellt = db.Column("Datum_Erstellung", db.String(50))
    datum_erledigt = db.Column("Datum_erledigt", db.String(50))  # fürs erste String, damit es leer gelassen werden kann

    def __init__(self, fehler_ID, fehlerquelle, lektion, art_des_fehlers, pos_im, kommentar, bearbeitungszustand, kurs_ID, benutzer_ID, datum_erstellt, datum_erledigt):
        self.fehler_ID = fehler_ID
        self.fehlerquelle = fehlerquelle
        self.lektion = lektion
        self.art_des_fehlers = art_des_fehlers
        self.pos_im = pos_im
        self.kommentar = kommentar
        self.bearbeitungszustand = bearbeitungszustand
        self.kurs_ID = kurs_ID
        self.benutzer_ID = benutzer_ID
        self.datum_erstellt = datum_erstellt
        self.datum_erledigt = datum_erledigt

# Klasse für alle Masken des Korrekturmanagementsystems
class MyBlueprint(Blueprint):
    def __init__(self, name, import_name):
        super().__init__(name, import_name)

        # Fügt die Routen der URL's zur Blueprint-Klasse hinzu
        self.add_url_rule("/", view_func=self.login, methods=["GET", "POST"])
        self.add_url_rule("/fehlermeldung", view_func=self.fehlermeldungen, methods=["GET", "POST"])
        self.add_url_rule("/fehler_anzeigen", view_func=self.tutor_ansicht, methods=["GET", "POST"])

        self.alle_elemente_vom_fehler = []
        self.fehler_ID = None
        self.fehler = None
        self.abgeschlossen = False
        self.status_person = None
        self.berechtigt = False

    # Logik der Login-Maske
    def login(self):
        # wenn der login Button gedrückt wird, wird überprüft ob der Benutzer existiert und das Passwort übereinstimmt
        if "login_button" in request.form:
            # aus dem GUI werden die Benutzereingaben genommen
            self.username = request.form.get("username")
            self.passwort = request.form.get("password")

            # bekommt den Benutzernamen und das Passwort aus der DB
            benutzername_db = Benutzer.query.filter_by(benutzername=self.username).first()
            passwort_db = Benutzer.query.filter_by(passwort=self.passwort).first()

            try:
                # prüft, ob Benutzername mit Passwort übereinstimmt
                if benutzername_db.benutzer_ID == passwort_db.benutzer_ID:
                    self.status_person = benutzername_db.status
                    self.benutzer_ID = benutzername_db.benutzer_ID
                    # ist der Benutzer Tutor oder Admin, kann er auf dei Tutorenansicht zugreifen
                    if self.status_person == "tutor" or self.status_person == "admin":
                        self.berechtigt = True
                    else:
                        self.berechtigt = False
                    # wenn der login erfolgreich war, wird die Seite Fehlermeldungen aufgerufen
                    return redirect(url_for(".fehlermeldungen"))
            except AttributeError:
                # wurde ein Error gefunden, wird dieser in dem GUI angezeigt
                return render_template("login.html", login_error=True)
        else:
            return render_template("login.html")

    # Logik der Fehlermeldungen-Maske
    def fehlermeldungen(self):
        check = Check_error()
        render = render_template("fehlermeldungen.html", error=check.error, fehlerquelle_error=check.fehlerquelle_error,
                                 fehlerart_error=check.fehlerart_error, kurs_error=check.kurs_error,
                                 lektion_error=check.lektion_error,
                                 pos_in_error=check.pos_in_error, kommentar_error=check.kommentar_error, berechtigt=self.berechtigt)

        # wird der Tutorenansicht Button gedrückt, wird diese Maske aufgerufen
        if "btn_tutorenansicht" in request.form:
            return redirect(url_for(".tutor_ansicht"))

        # wenn der Button für das hinzufügen betätigt wird
        if "btn_bestaetigen" in request.form:
            # bekommt alle Benutzerangaben aus dem GUI
            fehlerquelle = request.form.get("fehlerquelle")
            fehlerart = request.form.get("fehlerart")
            kurs = request.form.get("kurs")
            lektion = request.form.get("lektion")
            pos_in = request.form.get("pos_in")
            kommentar = request.form.get("kommentar")
            check = Check_error()
            # Sucht unbearbeitete Felder
            check.check_if_error(fehlerquelle, fehlerart, kurs, lektion, pos_in, kommentar, self.benutzer_ID)

            # fügt die Fehlermeldung der DB hinzu, wenn es keinen Error gibt
            if not check.error and not check.fehlerquelle_error and not check.fehlerart_error:
                try:
                    # holt sich die höchste ID der Fehler
                    id = Fehler.query.order_by(Fehler.fehler_ID.desc()).first().fehler_ID
                except AttributeError:
                    # falls noch kein Fehler eingetragen ist, wird die id = 0 gesetzt
                    id = 0

                # fügt der DB den Fehler hinzu
                zeit = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                fehler = Fehler(fehler_ID=id + 1, fehlerquelle=fehlerquelle, lektion=lektion, art_des_fehlers=fehlerart,
                                pos_im=pos_in, kommentar=kommentar, bearbeitungszustand="unbearbeitet", kurs_ID=kurs,
                                benutzer_ID="username", datum_erstellt=zeit, datum_erledigt="")
                db.session.add(fehler)
                db.session.commit()

                return render_template("fehlermeldungen.html", fehler_gespeichert=True, berechtigt=self.berechtigt)

            # falls ein Error gefunden wurde, wird das Feld im GUI farbig markiert
            return render_template("fehlermeldungen.html", error=check.error, berechtigt=self.berechtigt, fehlerquelle_error=check.fehlerquelle_error,
                                     fehlerart_error=check.fehlerart_error, kurs_error=check.kurs_error,
                                     lektion_error=check.lektion_error,
                                     pos_in_error=check.pos_in_error, kommentar_error=check.kommentar_error,
                                     fehlerquelle=fehlerquelle, kurs=kurs, fehlerart=fehlerart, lektion=lektion,
                                     pos_in=pos_in, kommentar=kommentar, ausgewählt=fehlerquelle)
        else:
            return render

    # Logik der Tutorenansicht-Maske
    def tutor_ansicht(self):
        neue_fehler = []
        neue_fehler_sortiert = []
        in_bearbeitung = []
        abgeschlossen_oder_abgelehnt = []
        auflistung_fehler = Fehler.query.all()
        modal_open = False

        # Fehler und Verbesserungsvorschläge werden kategorisiert und je nach Bearbeitungszustand angezeigt
        for i in auflistung_fehler:
            if i.bearbeitungszustand == "unbearbeitet":
                neue_fehler.append((i.fehler_ID, i.kurs_ID, i.art_des_fehlers, i.fehlerquelle))
            elif i.bearbeitungszustand == "wird_bearbeitet":
                in_bearbeitung.append((i.fehler_ID, i.kurs_ID, i.art_des_fehlers, i.fehlerquelle))
            elif i.bearbeitungszustand == "abgelehnt" or i.bearbeitungszustand == "abgeschlossen":
                abgeschlossen_oder_abgelehnt.append(f"ID: {i.fehler_ID}, {i.kurs_ID}, {i.art_des_fehlers},  {i.fehlerquelle}")

        # Sortieren der Liste nach der Fehlerkategorie
        neue_fehler_sortiert = self.fehler_sortieren(neue_fehler)
        neue_fehler = []

        # Inhalt der einzelnen Fehler als String im GUI darstellen
        for i in neue_fehler_sortiert:
            neue_fehler.append(f"ID: {i[0]}, {i[1]}, {i[2]}, {i[3]}")

        # Sortieren der Liste nach der Fehlerkategorie
        in_bearbeitung_sortiert = self.fehler_sortieren(in_bearbeitung)
        in_bearbeitung = []

        # Inhalt der einzelnen Fehler als String im GUI darstellen
        for i in in_bearbeitung_sortiert:
            in_bearbeitung.append(f"ID: {i[0]}, {i[1]}, {i[2]}, {i[3]}")

        # angeklickter Fehler wird detailliert in einem Popup (Modal) angezeigt
        if "auflistung" in request.form:
            values = request.form["auflistung"]
            self.fehler_ID = values.split(":")[1].split(",")[0]
            fehler = Fehler.query.get(self.fehler_ID)
            self.alle_elemente_vom_fehler = [fehler.fehler_ID, fehler.fehlerquelle, fehler.art_des_fehlers, fehler.pos_im, fehler.kommentar, fehler.kurs_ID, fehler.datum_erstellt, fehler.datum_erledigt]
            modal_open = True

        # über den zurück-Button geht es zur vorherigen Seite
        if "zurueck" in request.form:
            return redirect(url_for(".fehlermeldungen", berechtigt=self.berechtigt))

        # wenn der Bearbeitungszustand eines Fehlers / Verbesserungsvorschlages geändert wurde,
        # wird dies in der DB gespeichert und in dem GUI neu sortiert
        if "bestätigen" in request.form:
            bearbeitungsstatus = request.form["verschieben_nach"]
            if bearbeitungsstatus != "verschieben":
                fehler = Fehler.query.get(self.fehler_ID)
                fehler.bearbeitungszustand = bearbeitungsstatus

                # wenn der Fehler abgeschlossen oder abgelehnt wurde, wird das Datum hinzugefügt
                if bearbeitungsstatus == "abgeschlossen" or bearbeitungsstatus == "abgelehnt":
                    fehler.datum_erledigt = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                    self.abgeschlossen = True
                else:
                    fehler.datum_erledigt = ""
                    self.abgeschlossen = False

                db.session.commit()
                return redirect(url_for(".tutor_ansicht"))
        # wenn der Benutzer berechtigt ist, kann die Tutorenansicht geladen werden
        if self.berechtigt:
            return render_template("fehler_anzeigen.html", neue_fehler=neue_fehler, in_bearbeitung=in_bearbeitung, abgeschlossen_oder_abgelehnt=abgeschlossen_oder_abgelehnt, modal_open=modal_open, values=self.alle_elemente_vom_fehler, abgeschlossen=self.abgeschlossen)
        else:
            return redirect(url_for(".fehlermeldungen"))

    def fehler_sortieren(self, item):
        liste = []
        # sortiert zuerst die wissenschaftlichen Fehler aus
        for i in item:
            if i[2] == "Wissenschaftlicher Fehler":
                liste.append(i)
        # danach die Audio / Video
        for i in item:
            if i[2] == "Audio/Video Fehler":
                liste.append(i)
        # hinzufügen des Restes
        for i in item:
            if i[2] != "Audio/Video Fehler" and i[2] != "Wissenschaftlicher Fehler":
                liste.append(i)

        return liste

class Check_error:
    # verschiedenen Error Meldungen um das input Kästchen Rot zu färben, falls True
    error = False
    fehlerquelle_error = False
    fehlerart_error = False
    kurs_error = False
    lektion_error = False
    pos_in_error = False
    kommentar_error = False
    benutzer_ID = ""
    # holt die Werte aus den Input Feldern

    def check_if_error(self, fehlerquelle, fehlerart, kurs, lektion, pos_in, kommentar, benutzer_ID):
        self.benutzer_ID = benutzer_ID
        # überprüft, ob eine Fehlerquelle und die Fehlerart ausgewählt wurde
        if fehlerart == "auswahl":
            self.error = True
            self.fehlerart_error = True
        if fehlerquelle == "auswahl":
            self.error = True
            self.fehlerquelle_error = True

        # prüft auf weitere Fehler
        self.check_welche_felder(fehlerquelle, fehlerart, kurs, lektion, pos_in, kommentar)

    def check_welche_felder(self, fehlerquelle, fehlerart, kurs, lektion, pos_in, kommentar):
        self.fehlermeldung = {"Kurs-ID": kurs, "Fehlerquelle": fehlerquelle, "Lektion": lektion,
                              "Fehlerart": fehlerart, "Position": pos_in, "Kommentar": kommentar}

        # prüft, ob in alle Felder etwas eingetragen wurde
        for key, value in self.fehlermeldung.items():
            value.strip()
            if value == "":
                self.error = True
                if key == "Kurs-ID":
                    self.kurs_error = True
                if key == "Lektion":
                    self.lektion_error = True
                if key == "Position":
                    self.pos_in_error = True
                if key == "Kommentar":
                    self.kommentar_error = True

        # prüft, ob die Kurs-ID in der DB existiert
        kurs = Kurse.query.filter_by(kurs_abkuerzung=self.fehlermeldung["Kurs-ID"]).first()

        # wenn der Kurs None ist, gibt es die Abkürzung nicht in der DB
        if kurs is None:
            self.error = True
            self.kurs_error = True

            # damit die Funktion abgebrochen wird
            return 1

        # prüft, ob der Benutzer in dem Kurs eingetragen ist
        kurs_id = kurs.kurs_ID
        benutzer_id = Belegte_kurse.query.filter_by(benutzer_ID=self.benutzer_ID, kurse_ID=kurs_id).first()

        # wenn benutzer_id None ist, ist dieser nicht in den Kurs eingetragen
        if benutzer_id is None:
            self.error = True
            self.kurs_error = True

# Methode, um Benutzer hinzuzufügen
def benutzer_hinzufuegen(benutzername, passwort, status):
    # nur benutzer mit dem Status admin, tutor oder student dürfen hinzufgefügt werden
    if status == "admin" or status == "tutor" or status == "student":
        try:
            # holt sich die höchste ID der Fehler
            id = Benutzer.query.order_by(Benutzer.benutzer_ID.desc()).first().benutzer_ID
        except AttributeError:
            # falls noch kein Fehler eingetragen ist, wird die id = 0 gesetzt
            id = 0

        benutzer = Benutzer(benutzer_ID=id + 1, benutzername=benutzername, passwort=passwort, status=status)
        db.session.add(benutzer)
        db.session.commit()

# Registriere die Blueprint-Klasse bei der Flask-Anwendung
my_blueprint = MyBlueprint("my_blueprint", __name__)
app.register_blueprint(my_blueprint)


if __name__ == '__main__':
    # falls die DB nicht existiert, wird sie erstellt
    with app.app_context():
        db.create_all()
    app.run(debug=True)
