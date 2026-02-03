from http.client import responses

from nicegui import ui
import requests

def fetch_data():
    response = requests.get("http://localhost:8000/api/items")
    return response.json()

@ui.page('/')
def main_page():
    data = fetch_data()
    ui.label("Данные из API")
    for item in data:
        ui.label(item['name'])

ui.run()