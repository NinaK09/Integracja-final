from flask import Flask, render_template, request, redirect, render_template_string, send_from_directory
import requests
import json
from lxml import etree
import pathlib

app = Flask(__name__)

@app.route('/')
def home_page():
    return render_template('home.html')

#Strony upload-.. są takie same, z wyjątkiem action w form
@app.route('/upload-json')
def upload_file_view():
   return render_template('upload.html')

@app.route('/upload-xml')
def upload_file_view_XML():
   return render_template('upload-xml.html')

#uploader - przyjmuje plik JSON
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file'] #przyjmij plik
        file = f.stream.read() #odczytaj plik file
        # dekodujemy na string by backend zrozumial. uzywam decode() bo plik zwraca znaki w stylu "/n"
        payload = '{"input_json": ' + str(file.decode("utf-8")) + '}'
        # dodajemy rekordy; w body jest payload
        #url - docker back:port_back/dzialanie
        r = requests.post(url="http://backend-api2:8080/add-records-json",
                          data=payload)
        return redirect("/show-db")

#uploader - przyjmuje plik XML
@app.route('/uploader-xml', methods = ['GET', 'POST'])
def upload_to_filesystem():
    if request.method == 'POST':
        f = request.files['file']
        file = f.stream.read()
        #tworzymy plik data-input.xml w katalogu downloads/ dockera frontu, po czym zapisujemy do niego odczytane dane
        with open('downloads/data-input.xml', 'w', encoding='utf-8') as f:
            f.write(str(file.decode("utf-8")))  #dekodowanie by nie było znaków '/n'

        #importowanie danych z pliku data-input.xml
        root = etree.parse("downloads/data-input.xml")
        columns = (
        'brand', 'model', 'processor_brand', 'processor_name', 'processor_gnrtn', 'ram_gb', 'ram_type', 'ssd', 'hdd',
        'os', 'os_bit', 'graphic_card_gb', 'weight', 'display_size', 'warranty', 'touchscreen', 'msoffice',
        'latest_price', 'old_price', 'discount', 'star_rating', 'ratings', 'reviews')
        o_json = []
        for i in root.findall("row"): #znajdz znaczniki <row>
            p = [i.findtext(n) for n in columns] #p - zawartość znaczników dla kolumn
            o_json.append(dict(zip(columns, p))) #robimy słownik

        #w tym momencie o_json zawiera słownik. problem polega na tym, że wszystkie watości są typu string - w bazie kilka kolumn jest typu int lub float. dlatego poniżej jest konwersja

        #kolumny które zawierają wartości int
        columns_int = (
        "ram_gb", "ssd", "hdd", "os_bit", "graphic_card_gb", "warranty", "latest_price", "old_price", "discount",
        "ratings", "reviews")

        # kolumny które zawierają wartości float
        columns_float = ("display_size", "star_rating")

        #proste - jeśli kolumna w pliku nazywa się tak samo jak columns_int/columns_float to rzutujemy typ
        for j in o_json:
            for key, value in j.items():
                if key in columns_int:
                    j[key] = int(value)
                elif key in columns_float:
                    j[key] = float(value)

        #robimy słownik zrozumiały dla backendu
        payload = {"input_json": o_json}

        #dodanie do bazy. konwertujemy payload do jsona za pomocą json.dumps(), bo json to oczekiwany format
        r = requests.post(url="http://backend-api2:8080/add-records-json",
                          data=json.dumps(payload))

        return redirect("/show-db")

#po prostu wyświetlenie wszystkiego z db
@app.route("/show-db")
def select_star():
    #requesty by wyciągnąć zawartość bazy
    r = requests.get(url="http://backend-api2:8080/show-records")
    r_xml = requests.get(url="http://backend-api2:8080/db-to-xml")
    #konwertujemy xml do string, by można było wyświetlić na stronie
    s_xml=r_xml.json()["XML_laptops_list"][0]

    #labels - bierzemy wartości klucza 'laptops_list'
    return render_template('db-table.html', labels=r.json()['laptops_list'], json = r.json(), xml =s_xml)


#pobranie zawartości bazy danych i zapisanie jej do pliku JSON
@app.route("/download-json-db")
def json_from_db():
    #pobieramy dane z bazy
    r = requests.get(url="http://backend-api2:8080/show-records")

    #zapisanie do pliku data.json. funkcja zwraca {laptops_list: val}, więc bierzemy tylko wartosci
    with open('downloads/data.json', 'w', encoding='utf-8') as f:
        json.dump(r.json()["laptops_list"], f, ensure_ascii=False, indent=4)

    #templatka by mozna bylo pobrac plik
    return render_template_string('''
            <a href = '/uploads/data.json' target='_blank'>pobierz plik</a>
            ''')

@app.route("/download-xml")
def download_xml():
    #pobieramy dane z bazy
    r = requests.get(url="http://backend-api2:8080/db-to-xml")

    #konwersja stringa do obiektu biblioteki lxml
    tree = etree.fromstring(r.json()["XML_laptops_list"][0])
    et = etree.ElementTree(tree)

    #zapisujemy do pliku data.xml
    with open('downloads/data.xml', 'wb') as f:
        et.write(f, encoding="utf-8", xml_declaration=True, pretty_print=True)

    return render_template_string('''
            <a href = '/uploads/data.xml' target='_blank'>pobierz plik</a>
            ''')

#funkcja do zapisu pliku
@app.route("/uploads/<path:name>")
def download_file(name):
    name2 = 'downloads/'+name #ścieżka do pliku - wszystkie pliki json i xml w dockerze frontu są w katalogu downloads/
    uploads = pathlib.Path(name2).parent.absolute() #ścieżka absolutna - inaczej się NIE pobierze
    return send_from_directory(
        uploads, name, as_attachment=True
    )

#funkcja do stworzenia tabeli 'laptops', jeśli ona nie istnieje
@app.route("/create-table")
def create_empty_table():
    r = requests.get(url="http://backend-api2:8080/create-table")
    if r.json()["create_table_result"]: #jeśli func zwróciła true
        return render_template_string('''
            <p>Wykonano polecenie CREATE TABLE IF NOT EXISTS</p>
            <a href='/upload_json'>
			    <button>dodaj rekordy do bazy plikiem json</button>
		    </a>
		    
		    <a href='/upload-xml'>
			<button>dodaj do bazy plikiem XML</button>
		</a>
		
		    <a href='/'>
			<button>wroc do home</button>
		    </a>
        ''')
    else: #jeśli func zwróciła false
        return render_template_string('''
        <p>Nie wykonano polecenia</p>
        <a href='/'>
			<button>wroc do home</button>
		</a>
		<a href='/create-table'>
			<button>sprobuj ponownie</button>
		</a>
        ''')

if __name__ == "__main__":
    app.run(debug=True)
