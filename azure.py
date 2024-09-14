import json
import re
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# Zabezpiecz dane uwierzytelniające w produkcji, np. za pomocą zmiennych środowiskowych.
endpoint = "https://xxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx.azure.com/"
key = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

def format_bounding_box(bounding_box):
    if not bounding_box:
        return "N/A"
    return ", ".join(["[{}, {}]".format(p.x, p.y) for p in bounding_box])

def clean_text(text):
    # Usuń nadmiarowe spacje i nawiasy
    cleaned_text = re.sub(r'\s+', ' ', text)  # Zamień wielokrotne spacje na jedną
    cleaned_text = re.sub(r'[\[\](){}]', '', cleaned_text)  # Usuń nawiasy
    return cleaned_text.strip()

def analyze_read():
    # URL dokumentu do analizy
    formUrl = "http://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.com.pl/temp/x.pdf"

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    poller = document_analysis_client.begin_analyze_document_from_url(
        "prebuilt-read", formUrl)
    result = poller.result()

    # Zbierz dane do zapisu w formacie JSON
    document_data = {
        "content": clean_text(result.content),
        "styles": [
            {
                "is_handwritten": style.is_handwritten
            } for style in result.styles
        ],
        "pages": []
    }

    for page in result.pages:
        page_data = {
            "page_number": page.page_number,
            "width": page.width,
            "height": page.height,
            "unit": page.unit,
            "lines": [],
            "words": []
        }

        for line in page.lines:
            line_data = {
                "text": clean_text(line.content)
            }
            page_data["lines"].append(line_data)

        for word in page.words:
            word_data = {
                "text": clean_text(word.content),
                "confidence": word.confidence
            }
            #page_data["words"].append(word_data)

        document_data["pages"].append(page_data)

    # Zapisz dane do pliku JSON
    with open('document_analysis_result.json', 'w') as json_file:
        json.dump(document_data, json_file, indent=4)

    print("Dane zapisane do pliku document_analysis_result.json")

if __name__ == "__main__":
    analyze_read()
