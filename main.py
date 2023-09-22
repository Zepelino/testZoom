import requests
import webbrowser


from fastapi import FastAPI

app = FastAPI()


# Definir as credenciais do OAuth app
CLIENT_ID = "y23hZAm2QrSWJ4DYxdDCKw"
CLIENT_SECRET = "VUFvjcNym6aNim6e5t5n7v1DZKJw0WMI"
REDIRECT_URI = "http://localhost:8080/auth/zoom"

# Definir os dados da reunião
title = "Reunião de teste"
start_time = "2023-09-23T10:00:00Z"
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
        print(f"Reunião criada com sucesso: {response.content}")
        print(meeting_id)

    elif response.status_code == 400:
        # Houve um erro ao criar a reunião
        print("bad request")

    elif response.status_code == 404:
        # Link errado
        print("Link não achado")

    elif response.status_code == 429:
        # Houve um erro ao criar a reunião
        print("Limite diário da API excedido")

    print("segundo mt: ",meeting_id)
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
                            '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'
                        ],
                        "name": "Marque a quantidade de espectadores",
                        "type": "single"
                    }],
                    "title": "Quantos estão assistindo?"
                }

        print("indo fazer segunda request")
        #Faz a HTTP request para criar a enquete na reunião
        response = requests.post(
            f"https://api.zoom.us/v2/meetings/{meeting_id}/polls",
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
        )

        print("fez segunda request: ", response.content)
        if response.status_code == 201:
            print("Enquete criada com sucesso")

        elif response.status_code == 400:
            print("Falha ao criar enquete: possivelmente a conta não pode criar pools")

        elif response.status_code == 404:
            print("Falha ao criar enquete: Reunião não encontrada")

    return 'OPA'
