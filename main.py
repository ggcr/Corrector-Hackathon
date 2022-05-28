from flask import Flask, request, redirect, url_for, session,render_template
from flask_session import Session
import requests
import json
import google.oauth2.id_token
import google.auth.transport.requests
import os
from spellchecker import SpellChecker

app = Flask(__name__)

# Obrim una sessió pel client que actuará per a guardar valors de variables
app.secret_key = "Some"
app.config['SESSION_COOKIE_NAME'] = "my_session"

# RUTA (/)
# S'implementa un patró POST-REDIRECT-GET per evitar que cada vegada que es 
# fà un refresh de la pàgina el navegador mostri un avís de "Vols reenviar les dades?"...
@app.route('/', methods=['GET', 'POST'])
def root():
    text_in = ''

    # Si la request es un POST i vé del button 'Corregir'...
    if request.method == 'POST':
        if request.form.to_dict()['submit_button'] == 'Corregir':

            # Llegim input i metode
            text_in = request.form['input'] if len(request.form['input']) > 0 else ''
            method = request.form['method'] if len(request.form['method']) > 0 else ''

            # Guarden en la sessió input i metode
            session['log'] = text_in
            session['method'] = method
        
        # Redirigim al user a aquesta ruta de manera que ara serà un GET
        return redirect(url_for('root'))
    
    # Guardem la frase i el metode del client
    local = session.pop('log', None)
    method = session.pop('method', None)

    # Si tenim input i metode...
    if local is not None:
        if local and len(local)>0:
            if method is not None:
                if method and len(method)>0:
                    if method == "Typewrite":
                        # Criden a la API de Typewise
                        word_D = test_api(local)
                    elif method == "PySpellchecker":
                        # Cridem al packet pyspelllchecker
                        word_D = pyspellchecker(local)
        else:
            local = None
    
    # Fem render, això pasarà els valors al nostre fitxer templates/index.html
    # - variable input: la cadena de text entrada per l'usuari
    #           "Tjis is a test"
    # - variable output: la llista de paraules amb les correccions en llistes anidades
    #           ['Tjis', ['This', ''], 'is', 'a', 'test']
    # - variable method: valor del metode escollit
    #           Typewise: Cridarà API externa amb cloud function
    #           PySpellCheck: Utilitzara el packet de pyspellchecker
    return render_template('index.html', input='' if local is None else local, output='' if local is None else word_D, method=method)


# Aquesta funció farà un POST a la nostra cloud function {url_google_web}/corregir
def test_api(text_in):
    # Es fa un try-catch per avisar al user que no té les credencials.
    try:
        # Per a treballar en local i poder cridar a les cloud func necesitem pasar les nostres credentials
        # Aquesta credential es guarda en una variable d'entorn local per així evitar que es vegi la key
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './corrector-sm-9ef8799680bd.json'
        request = google.auth.transport.requests.Request()
        audience = 'https://europe-west3-corrector-sm.cloudfunctions.net/corregir'
        TOKEN = google.oauth2.id_token.fetch_id_token(request, audience)
        r = requests.post(
            'https://europe-west3-corrector-sm.cloudfunctions.net/corregir', 
            headers={'Authorization': f"Bearer {TOKEN}", "Content-Type": "application/json"},
            data=json.dumps({"message":text_in}),  # Pasem la cadena de input
            verify=False # Evitem SSLErrors
        )

        # En cas que vagi tot bé: HTTP 200 - OK
        if r.status_code == 200:
            # Carreguem la resposta
            json_response = json.loads(r.content.decode("utf-8"))

            # Convertim tot en una llista de paraules amb les sugerencies en llistes anidades
            # ['Hola', 'ke', ['que', 'qué'], 'tal']
            lista_palabras = generarFrase(json_response)

            return lista_palabras
    except:
        print("\n\nERROR: Falten les credencials del google cloud .json! No es podrà cridar a la API de Typewise.\n")
        return ""

    return ""

# Amb aquesta funció fem parse del json i ens quedem amb aquelles paraules que tinguin un bon score
# En cas de tenir un mal score retornem les 3 primeres sugerencies.
# Això ens fà que per a correccions casi 100% segures només mostrem la paraula correcta.
def generarFrase(json_response):
    list_sentence = []
    for word in json_response['tokens']:
        list_sentence += [word['original_word']]
        if len(word['suggestions']) > 0:
            if word['original_word'] != word['suggestions'][0]['correction']:
                list_suggest = []
                # Si la sugerencia es un 75% correcta mostrem només aquesta
                if word['suggestions'][0]['score'] < 0.75:
                    for suggestion in word['suggestions'][:3]:
                        list_suggest += [suggestion['correction']]
                else:
                    list_suggest = [word['suggestions'][0]['correction']]
                list_sentence += [list_suggest]
    
    # Hem passat d'un JSON amb molts detalls a -> ['Hola', 'ke', ['que', 'qué'], 'tal']
    return list_sentence

def pyspellchecker(local):
    # Iniciem l'objecte SpellChecker amb 3 llenguatges:
    spell = SpellChecker(language=['es', 'en', 'de'], case_sensitive=True)

    # Mirem quines paraules están malament
    misspelled = spell.unknown(local.split())

    output = []
    l = []
    # Construim la llista amb el mateix format que ho fem amb la API externa
    for word in local.split():
        output.append(word)
        if word.lower() in misspelled:
            if word not in misspelled:
                l = [spell.correction(word).capitalize()]
                output.append(l)
            else:
                output.append([spell.correction(word)])
    # Hem passat d'un input 'Hola ke tal' a -> ['Hola', 'ke', ['que', 'qué'], 'tal']
    return output

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)