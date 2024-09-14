import os
import requests
import base64
import yaml
import json
from pdf2image import convert_from_path
from tempfile import gettempdir

# Funkcja do wczytywania konfiguracji z pliku YAML
def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config

with open('wynik.json', 'r', encoding='utf-8') as file:
    wynik = file.read()

# Wczytanie konfiguracji
config = load_config('vision_config.yaml')
api_key = config['api_key']
base_url = config['base_url']
model_name = config['model_name']
max_tokens = config['max_tokens']
temperature = config['temperature']   
top_p = config['top_p']
n = config['n']
stop = config['stop']
presence_penalty = config['presence_penalty']
frequency_penalty = config['frequency_penalty']
input_folder = config['input_folder']

# Funkcja do kodowania obrazów w base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_image

# Funkcja do konwertowania PDF do obrazów JPG
def convert_pdf_to_images(pdf_path, output_folder):
    print(f"Konwertowanie PDF do obrazów: {pdf_path}")
    images = convert_from_path(pdf_path, dpi=300)
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f"page_{i + 1}.jpg")
        image.save(image_path, "JPEG")
        image_paths.append(image_path)
    return image_paths, len(images)

# Funkcja do przetwarzania obrazów JPG
def process_jpg_image(image_path):
    print(f"Przetwarzanie pliku JPG: {image_path}")
    return [image_path], 1

# Funkcja do przetwarzania wszystkich plików w folderze
def process_files_in_folder(folder_path):
    output_folder = gettempdir()

    # Utworzenie folderu input, jeśli nie istnieje
    input_folder_path = os.path.join(folder_path, input_folder)
    if not os.path.exists(input_folder_path):
        os.makedirs(input_folder_path)
        print(f"Utworzono folder: {input_folder_path}")

    # Iterowanie przez pliki w folderze input
    for filename in os.listdir(input_folder_path):
        file_path = os.path.join(input_folder_path, filename)
        if filename.lower().endswith('.pdf'):
            print(f"Przetwarzanie pliku PDF: {filename}")
            image_paths, num_pages = convert_pdf_to_images(file_path, output_folder)
        elif filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')): 
            print(f"Przetwarzanie pliku JPG: {filename}")
            image_paths, num_pages = process_jpg_image(file_path)
        else:
            print(f"Nieobsługiwany plik: {filename}")
            continue

        messages = [
            {
                "role": "system",
                "content": "You are a professional OCR AI that analyzes  documents."
            },
            {
                "role": "user",
                "content": f"OCR recognized text from the document: {wynik}"
            }
        ]

        # Dodanie obrazów z wyraźnym wskazaniem kolejności stron
        for i, image_path in enumerate(image_paths, start=1):
            encoded_image = encode_image_to_base64(image_path)
            image_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Strona {i} dokumentu:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            }
            messages.append(image_message)

 
        # Dodanie instrukcji do przetworzenia danych
        messages.append({
            "role": "user",
            "content": "Verify that the .............YOUR INSTRUCTION HERE................."
        })
        messages.append({
            "role": "user",
            "content": "Please return the data in JSON format reflecting the following structure of the.... YOUR INSTRUCTION HERE ......................."
        })

        # Przygotowanie payload
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stop" : stop, 
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty
        }

        # Nagłówki żądania
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Wysłanie żądania POST do API
        print("messages", messages)
        response = requests.post(base_url, json=payload, headers=headers)

        # Sprawdzenie odpowiedzi
        if response.status_code == 200:
            response_json = response.json()
            content = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
            total_tokens = response_json.get('usage', {}).get('total_tokens', 0)

            # Zapis odpowiedzi do pliku
            output_file_path = os.path.splitext(file_path)[0] + ".txt"
            with open(output_file_path, "w", encoding="utf-8") as output_file:
                output_file.write(content)
                output_file.write(f"\n\nLiczba stron w dokumencie: {num_pages}")
                output_file.write(f"\nZużyte tokeny: {total_tokens}")
                print('TT', total_tokens)

            print(f"Odpowiedź zapisana w pliku: {output_file_path}")
        else:
            print(f"Żądanie nie powiodło się. Status code: {response.status_code}")
            print("Treść błędu:", response.text)

        # Usunięcie tymczasowych plików JPEG
        for image_path in image_paths:
            os.remove(image_path)
            print(f"Usunięto plik: {image_path}")

# Uruchomienie przetwarzania plików w folderze
if __name__ == "__main__":
    process_files_in_folder(os.path.dirname(__file__))
