import os
import easyocr
import yaml
from pdf2image import convert_from_path
from PIL import Image
import numpy as np

# YAML z easyocr - te pliki są większe niż yml z drugiego skanera dlatego aby nie wysyłać większych plików do AI, po załadowaniu ich do SQL - kasujemy je

os.environ['OMP_THREAD_LIMIT'] = '4'

# Funkcja do przetwarzania plików PDF przez EasyOCR
def process_pdf_with_easyocr(file_path):
    try:
        reader = easyocr.Reader(['pl'])
        all_extracted_text = []
        pages = convert_from_path(file_path, dpi=300)

        for page_number, page in enumerate(pages, start=1):
            print(f"Przetwarzanie strony {page_number} z PDF przez EasyOCR...")
            # Odczytujemy tekst przy użyciu EasyOCR
            result = reader.readtext(np.array(page), detail=0)

            extracted_text = []
            for text in result:
                extracted_text.append(text)

            all_extracted_text.extend(extracted_text)

        return '\n'.join(all_extracted_text)  # Zwracamy cały rozpoznany tekst z wszystkich stron
    except Exception as e:
        print(f"Wystąpił problem podczas przetwarzania pliku {file_path}: {str(e)}")
        return None

# Funkcja do przetwarzania obrazów przez EasyOCR
def process_image_with_easyocr(file_path):
    try:
        reader = easyocr.Reader(['pl'])
        image = Image.open(file_path)
        result = reader.readtext(np.array(image), detail=0)

        extracted_text = []
        for text in result:
            extracted_text.append(text)

        return '\n'.join(extracted_text)  # Zwracamy cały rozpoznany tekst z obrazu
    except Exception as e:
        print(f"Wystąpił problem podczas przetwarzania pliku {file_path}: {str(e)}")
        return None

# Ścieżki katalogów wejściowego i wyjściowego
input_directory = r'C:\AI_scan\easyocr\scan_test_in'
output_directory_easyocr = r'C:\AI_scan\easyocr\ocr_out'

# Tworzenie katalogu wyjściowego, jeśli nie istnieje
os.makedirs(output_directory_easyocr, exist_ok=True)

# Przetwarzanie wszystkich plików w katalogu wejściowym
for filename in os.listdir(input_directory):
    file_path = os.path.join(input_directory, filename)
    if os.path.isfile(file_path):
        output_filename_easyocr = f"{os.path.splitext(filename)[0]}.yaml"
        output_file_path_easyocr = os.path.join(output_directory_easyocr, output_filename_easyocr)
        
        # Sprawdzenie, czy plik YAML już istnieje w katalogu wyjściowym
        if os.path.exists(output_file_path_easyocr):
            print(f"Plik YAML dla {filename} już istnieje, pomijam przetwarzanie.")
            continue
        
        print(f"Przetwarzanie pliku: {filename}")
        if file_path.lower().endswith('.pdf'):
            # Przetwarzanie przez EasyOCR
            extracted_text_easyocr = process_pdf_with_easyocr(file_path)
            if extracted_text_easyocr is not None:
                # Zapis do pliku YAML przez EasyOCR
                yaml_data_easyocr = {
                    'extracted_text': extracted_text_easyocr
                }
                with open(output_file_path_easyocr, 'w', encoding='utf-8') as file:
                    yaml.dump(yaml_data_easyocr, file, allow_unicode=True)
                print(f"Dane z pliku {filename} przez EasyOCR zostały zapisane do pliku: {output_filename_easyocr}")

        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            # Przetwarzanie przez EasyOCR
            extracted_text_easyocr = process_image_with_easyocr(file_path)
            if extracted_text_easyocr is not None:
                # Zapis do pliku YAML przez EasyOCR
                yaml_data_easyocr = {
                    'extracted_text': extracted_text_easyocr
                }
                with open(output_file_path_easyocr, 'w', encoding='utf-8') as file:
                    yaml.dump(yaml_data_easyocr, file, allow_unicode=True)
                print(f"Dane z pliku {filename} przez EasyOCR zostały zapisane do pliku: {output_filename_easyocr}")

        else:
            print(f"Ignorowanie pliku {filename}: Nieobsługiwany format")

print("Przetwarzanie zakończone.")
