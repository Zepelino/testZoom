import PySimpleGUI as sg
import datetime
from datetime import date
import requests
import webbrowser
from fastapi import FastAPI
from enum import Enum

class weekdays(Enum):
    monday = 0
    tuesday = 1
    wednesday = 2
    thursday = 3
    friday = 4
    saturday = 5
    sunday = 6

app = FastAPI()

def next_day(given_date, weekday):
    day_shift = (weekday - given_date.weekday()) % 7
    return given_date + datetime.timedelta(days=day_shift)

today = date.today()
weekday = today.weekday()
if  weekday == weekdays.sunday or weekday == weekdays.monday or weekday == weekdays.tuesday:
    midWeek = True

layout = [
            [sg.Input(date.today().strftime('%d/%m/%Y'), readonly=True, expand_x=True, key='rd_InpImgPath'), sg.CalendarButton("Escolha a data", format='%d/%m/%Y')],
            [sg.Spin(list(range(0,24)), "19", key='-HOURS-', s=3), sg.Text(':'),
                sg.Spin(list(range(0,60,5)), "30", key='-MIN-', s=3), ],
            [sg.Button('Ok'), sg.Button('Cancel')]
        ]

window = sg.Window('Time Entry', layout, font='Courier 15')

hours = minutes = None

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break
    if event == 'Ok':
        hours, minutes = values["-HOURS-"], values["-MIN-"]
        break

window.close()
sg.popup(hours, minutes)

# Definir as credenciais do OAuth app
CLIENT_ID = "y23hZAm2QrSWJ4DYxdDCKw"# cong: "RjYh00vbQLSsNvq7grWuVQ"
CLIENT_SECRET = "VUFvjcNym6aNim6e5t5n7v1DZKJw0WMI" # cong: "06sXnx5G4gxPZkE2h6VL3WLsFS7t11Xt"
REDIRECT_URI = "http://localhost:8080/auth/zoom"

# Definir os dados da reunião
title = "Reunião de teste"
start_time = "2023-09-29T13:00:00"
duration = "30"
agenda = "Reunião de teste para testar a API do Zoom"

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

    # Verificar o status da resposta
    if response.status_code == 201:
        # A reunião foi criada com sucesso
        meeting_id = response.json()["id"]

        msg = f"""
            Central Paulista está lhe convidando para uma reunião Zoom.
            
            Tópico: {title}
            Horário: Setembro 23, 2023 19:30 Recife
            
            Entrar na reunião Zoom
            {response.json()["join_url"]}
            
            Meeting ID: {meeting_id}
            Senha: {response.json()["password"]}
        """
        print(msg)
        print(f"Reunião criada com sucesso: {response.content}")
        #print(meeting_id)

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


    return msg
