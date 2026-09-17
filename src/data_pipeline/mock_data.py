"""
Mock Data Generator for testing Phase 0 pipeline
Generates realistic Vedic verse data for pipeline validation
"""

import json
from pathlib import Path

OUTPUT_DIR = Path("./data/pdf_extracted")


def generate_mock_pdf_data():
    """Generate mock Bhagavad Gita verses for testing"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mock_verses = {
        "1.1": {
            "chapter": 1,
            "verse": 1,
            "text": "Dharma-kṣetre kuru-kṣetre / samaveta yuyutsavaḥ",
            "translation": "On the holy field of Kurukṣetra, assembled together, eager to fight...",
            "source": "Mock PDF",
        },
        "1.2": {
            "chapter": 1,
            "verse": 2,
            "text": "Marjayante mahā-bhāgā / bhīṣmaṁ ca droṇam ca mādhavam",
            "translation": "O Sañjaya, after my sons and the sons of Pandu assembled...",
            "source": "Mock PDF",
        },
        "2.47": {
            "chapter": 2,
            "verse": 47,
            "text": "Yogaḥ karmasu kauśalam",
            "translation": "Yoga is skill in action.",
            "source": "Mock PDF",
        },
        "3.35": {
            "chapter": 3,
            "verse": 35,
            "text": "Śreyān svabhāvo guṇavān / tat sangas tu sadoṣavat",
            "translation": "It is far better to discharge one's prescribed duty...",
            "source": "Mock PDF",
        },
        "18.66": {
            "chapter": 18,
            "verse": 66,
            "text": "Sarva-dharmān parityajya / mām ekaṁ śaraṇaṁ vraja",
            "translation": "Abandon all varieties of religion and just surrender unto Me...",
            "source": "Mock PDF",
        },
    }

    output_file = OUTPUT_DIR / "bhagavad_gita_pdf.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mock_verses, f, ensure_ascii=False, indent=2)

    print(f"✓ Generated mock PDF data: {len(mock_verses)} verses")
    return mock_verses


if __name__ == "__main__":
    generate_mock_pdf_data()
