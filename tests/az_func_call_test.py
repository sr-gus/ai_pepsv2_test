import requests
import json

# URL de tu Azure Function
url = "https://ai-pepsv2-test-awbufyf6a0egdyc7.centralus-01.azurewebsites.net/api/threadEscalationEngine?code=Ja4LJRtAhxhmJaUzolq8RCOqYjSuOIEnC7b8rtaSNR_WAzFubeiMLg=="

# Ruta del archivo JSON
json_file = "azure_billing_escalation_threads.json"

# Leer el contenido del archivo JSON
with open(json_file, "r", encoding="utf-8") as file:
    payload = json.load(file)

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(
        url,
        headers=headers,
        json=payload[0],
        timeout=30
    )

    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(response.text)

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")