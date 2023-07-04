#importy mogą rzucać errory w pycharmie gdy nie są zainstalowane lokalnie. Mimo to działają bez zarzutu
from fastapi import FastAPI  # do api/docs
import psycopg2  # polaczenie z baza
from pydantic import BaseModel #do obs klas
from typing import List

app = FastAPI()

#polaczenie z baza
def dbconnect():
    cnxn = psycopg2.connect(dbname='computers',
                            host='postgres2',
                            port=5432,
                            user='nina',
                            password='TestTest01')
    print('Połączono z DB')
    return cnxn.cursor(), cnxn

#stworz tabele jesli nie istnieje
@app.get("/create-table")
def create_table_if_not_exists():

    def create_table(cursor, cnxn):
        query = "CREATE TABLE IF NOT EXISTS laptops(id SERIAL NOT NULL PRIMARY KEY, brand varchar NOT NULL, model varchar NOT NULL, processor_brand varchar NOT NULL, processor_name varchar NOT NULL, processor_gnrtn varchar NOT NULL, ram_gb int NOT NULL, ram_type varchar NOT NULL, ssd int NOT NULL, hdd int NOT NULL, os varchar NOT NULL, os_bit int NOT NULL, graphic_card_gb int NOT NULL, weight varchar NOT NULL, display_size float NOT NULL, warranty int NOT NULL, Touchscreen varchar NOT NULL, msoffice varchar NOT NULL, latest_price int NOT NULL, old_price int NOT NULL, discount int NOT NULL, star_rating float NOT NULL, ratings int NOT NULL, reviews int NOT NULL);"

        try:
            cursor.execute(query)
        except Exception:
            return False
        else:
            cnxn.commit()
            return True

    #bloki try są głównie po to, by wyświetlić error jak coś pójdzie źle.
    #polecenia w bloku try ZAWSZE się wykonają - dlatego jest tam zamknięcie kursora połączenia i samego połączenia
    try:
        cursor, connection = dbconnect()
        return {"create_table_result":create_table(cursor, connection)}
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
    finally:
        cursor.close()
        connection.close()

#jak ma wygladac json wejsciowy - w tym przypadku {"input_json": [/zawartość listy/]}
class InsertData(BaseModel):
    input_json: List

@app.post("/add-records-json")
def add_records(input: InsertData): #nasz input jest typu zadeklarowanego powyżej

    def insert_data(cursor, cnxn, input):
        query = "INSERT INTO laptops VALUES "
        for i, element in enumerate(input.input_json):
        #enumerate to basically iterator, element - w samym for mielibyśmy tylko iterator, a w for .. in ... tylko element. enumerate łączy dwie najlepsze cechy obydwu pętli :^)
            query += f"(default, " #default - postgres w taki sposób dodaje kolejne id
            for key, value in element.items():
                #element- cały słownik
                #element.items() to basically "brand": "ASUS" - słownik

                #jesli wartosc jest typu str to dodaje '', jak nie to daje sama wartosc
                if key != "id":

                    if type(value) == type('str'):
                        query += f"'{value}', "
                    else:
                        query += f"{value}, "
            query = query[:-2] # przecinek i spacja na końcu
            query += f"), " #koniec wartosci jednego rekordu

        query = query[:-2]  # przecinek na końcu i spacja
        cursor.execute(query)
        cnxn.commit()
        return True

    try:
        cursor, connection = dbconnect()
        return {'insert_results': insert_data(cursor,connection, input)}
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
    finally:
        cursor.close()
        connection.close()


#wyswietlenie rekordow w bazie
@app.get("/show-records")
def show_test():

    def get_data(cursor):
        result_query = [] #tu zapisze wyniki
        query = 'SELECT * FROM laptops'
        cursor.execute(query) #wykonaj query
        columns = [column[0] for column in cursor.description]
        for row in cursor.fetchall(): #fetchall - zwróć wszystko
            row_dict = {} #slownik na rekord
            for i, element in enumerate(row):
                row_dict[columns[i]] = element #dla klucza columns[i] (kolejne nazwy kolumn) wstaw element jako wartosc
            result_query.append(row_dict) #dodaj do result_query slownik

        return result_query

    try:
        cursor, connection = dbconnect()
        results = get_data(cursor)
        return {"laptops_list":results}
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
    finally:
        cursor.close()
        connection.close()


#pobranie z bazy i zwrócenie w formie XML
@app.get("/db-to-xml")
def db_xml():

    def get_data(cursor):

        #postgres my beloved - wbudowana funkcja query_to_xml
        query = "SELECT query_to_xml('SELECT * FROM laptops', true, false, '');"
        cursor.execute(query)
        # fetchone() - zwróć jedno. Query zwraca XML w jednej linii, więc nie ma sensu uzywac fetchall()
        xml_string = cursor.fetchone()
        return xml_string

    try:
        cursor, connection = dbconnect()
        results = get_data(cursor)
        return {"XML_laptops_list":results}
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
    finally:
        cursor.close()
        connection.close()