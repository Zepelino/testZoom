import sys

import PySimpleGUI as sg
import datetime
from datetime import date
import requests
import webbrowser
from fastapi import FastAPI
import uvicorn
import pyperclip
import asyncio

weekdays = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}

months = {
    "01": "Janeiro",
    "02": "Fevereiro",
    "03": "Março",
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro"
}

def next_day(given_date, weekday):
    day_shift = (weekday - given_date.weekday()) % 7
    return given_date + datetime.timedelta(days=day_shift)

today = date.today()
weekday = today.weekday()

if weekday == weekdays["sunday"] or weekday == weekdays["monday"] or weekday == weekdays["tuesday"]:
    next_meeting_day = next_day(today, weekdays["tuesday"])
else:
    next_meeting_day = next_day(today, weekdays["saturday"])

time_selector = [sg.Spin(list(range(0,24)), "19", readonly = True, key='-HOURS-', s=3), sg.Text(':'),
                sg.Spin(list(range(0,60,5)), "30", readonly = True, key='-MIN-', s=3)]

date_selector = [sg.Input(next_meeting_day.strftime('%d/%m/%Y'), size=(10,0),readonly=True, key='-DAY-'),
                 sg.CalendarButton("Escolha a data", format='%d/%m/%Y')]

title_selector = [sg.Input("Reunião", expand_x=True, size=(15,0), key='-TITLE-'), sg.Checkbox("Incluir data no título", default=True, key="-INCLUDE-")]

create_layout = [
            [sg.Column([[sg.Text("Título da reunião:")]], expand_x=True)],
            [sg.Column([title_selector], expand_x=True)],
            [sg.Column([[sg.Text("Dia da reunião:")]], expand_x=True)],
            [sg.Column([date_selector], element_justification="left", expand_x=True)],
            [sg.Column([[sg.Text("Horário da reunião:")]], expand_x=True)],
            [sg.Column([time_selector], element_justification="left", expand_x=True)],
            [sg.Column([[sg.Text("Duração:")]], expand_x=True)],
            [sg.Column([[sg.Spin(list(range(30,500,5)), "150", size=(5,0),readonly = True, key='-DURATION-')]], expand_x=True)],
            [sg.Button('Cancel'), sg.HSeparator() ,sg.Button('Ok', size=(6,0))]
]



#layout = [[
#    sg.Column(create_layout, visible=True, key='-WIN1-'),
#    sg.Column(msg_layout, visible=False, key='-WIN2-')
#]]
sg.theme("Reddit")

window = sg.Window('Agendador', create_layout, font=("Arial Baltic", 14))

hours = minutes = mt_date = duration = None
title = "Reunião Teste"
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':
        sys.exit()
        break
    if event == 'Ok':
        hours, minutes, mt_date, duration = values["-HOURS-"], values["-MIN-"], values["-DAY-"], values["-DURATION-"]
        title = f"{values['-TITLE-']} {values['-DAY-'] if values['-INCLUDE-'] else ''}"
        break



window.close()
#sg.popup(hours, minutes, mt_date)
#sys.exit()
app = FastAPI()


# Definir as credenciais do OAuth app
CLIENT_ID = "y23hZAm2QrSWJ4DYxdDCKw"# cong: "RjYh00vbQLSsNvq7grWuVQ"
CLIENT_SECRET = "VUFvjcNym6aNim6e5t5n7v1DZKJw0WMI" # cong: "06sXnx5G4gxPZkE2h6VL3WLsFS7t11Xt"
REDIRECT_URI = "http://localhost:8080/auth/zoom"

# Definir os dados da reunião


formated_date = datetime.datetime.strptime(mt_date, '%d/%m/%Y').strftime('%Y-%m-%d')
print(formated_date)
start_time = f"{formated_date}T{hours}:{minutes}:00"
agenda = "Reunião"

# Obter o código de autorização
auth_url = "https://zoom.us/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=user_meetings:create".format(
    CLIENT_ID=CLIENT_ID, REDIRECT_URI=REDIRECT_URI
)

webbrowser.open(auth_url)


@app.api_route("/auth/zoom/", methods=["GET", "POST", "DELETE"])
async def recieve_code(code: str):
    print(code)
    token_url = "https://zoom.us/oauth/token?grant_type=authorization_code&code={code}&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&redirect_uri={REDIRECT_URI}".format(
        code=code, CLIENT_ID=CLIENT_ID, CLIENT_SECRET=CLIENT_SECRET, REDIRECT_URI=REDIRECT_URI
    )

    response = requests.post(token_url)

    access_token = response.json()["access_token"]

    # Criar o os dados da solicitação
    payload = {
        "topic": title,
        "start_time": start_time,
        "duration": duration,
        "agenda": agenda,

    }

    # Enviar a solicitação para a API do Zoom
    response = requests.post(
        "https://api.zoom.us/v2/users/me/meetings",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload,
    )

    meeting_id = None
    msg = ''

    # Verificar o status da resposta
    if response.status_code == 201:
        # A reunião foi criada com sucesso
        meeting_id = response.json()["id"]

        msg_date = formated_date.split("-")
        msg = f"""Central Paulista está lhe convidando para uma reunião Zoom.

Tópico: {title}
Horário: {months[msg_date[1]]} {msg_date[2]}, {msg_date[0]}, {hours}:{minutes}, Recife

Entrar na reunião Zoom
{response.json()["join_url"]}

Meeting ID: {meeting_id}
Senha: {response.json()["password"]}"""


    elif response.status_code == 400:
        # Houve um erro ao criar a reunião
        print("bad request")

    elif response.status_code == 404:
        # Link errado
        print("Link não achado")

    elif response.status_code == 429:
        # Houve um erro ao criar a reunião
        print("Limite diário da API excedido")

    if meeting_id != None:
        #cria os dados da enquete
        payload = {
                    "anonymous": True,
                    "poll_type": 1,
                    "questions":
                    [{
                        "answer_required": True,
                        "answers":
                        [
                            'Já respondi', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'
                        ],
                        "name": "Marque a quantidade de espectadores",
                        "type": "single"
                    }],
                    "title": "Quantos estão assistindo?"
                }

        #Faz a HTTP request para criar a enquete na reunião
        response = requests.post(
            f"https://api.zoom.us/v2/meetings/{meeting_id}/polls",
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
        )

        if response.status_code == 201:
            print("Enquete criada com sucesso")

        elif response.status_code == 400:
            print("Falha ao criar enquete: possivelmente a conta não pode criar pools")

        elif response.status_code == 404:
            print("Falha ao criar enquete: Reunião não encontrada")

    msg_layout = [
        [sg.Text("Convite para a reunião")],
        [sg.Multiline(default_text=msg, size=(40, 20), disabled=True, key="-MSG-")],
        [sg.Button("Fechar"), sg.HSeparator(), sg.Button("Copiar")]
    ]
    window = sg.Window('Agendador', msg_layout, font=("Arial Baltic", 14))
    #window['-MSG-'].update(msg)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Fechar':
            break
        if event == 'Copiar':
            pyperclip.copy(msg)
            pyperclip.paste()
            window["Copiar"].update("Copiado!")

    loop = asyncio.get_event_loop()
    loop.stop()
    window.close()
    sys.exit()
    #return msg

if __name__ == '__main__':
    uvicorn.run(app, port=8080)
