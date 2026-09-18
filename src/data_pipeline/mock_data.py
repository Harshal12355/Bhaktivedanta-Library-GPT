"""
Mock Data Generator for testing Phase 0 pipeline
Generates realistic Vedic verse data for pipeline validation
"""

import json
from pathlib import Path

OUTPUT_DIR = Path("./data/pdf_extracted")


def generate_mock_pdf_data():
    """Generate mock Vedic verses from multiple texts for testing"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mock_verses = {
        # Bhagavad Gita verses
        "BG-1.1": {
            "chapter": 1,
            "verse": 1,
            "text": "Dharma-kṣetre kuru-kṣetre / samaveta yuyutsavaḥ",
            "translation": "On the holy field of Kurukṣetra, assembled together, eager to fight...",
            "source": "Bhagavad Gita",
        },
        "BG-1.2": {
            "chapter": 1,
            "verse": 2,
            "text": "Marjayante mahā-bhāgā / bhīṣmaṁ ca droṇam ca mādhavam",
            "translation": "O Sañjaya, after my sons and the sons of Pandu assembled...",
            "source": "Bhagavad Gita",
        },
        "BG-2.47": {
            "chapter": 2,
            "verse": 47,
            "text": "Yogaḥ karmasu kauśalam",
            "translation": "Yoga is skill in action. Perform your duty with detachment, abandoning concern for results.",
            "source": "Bhagavad Gita",
        },
        "BG-3.35": {
            "chapter": 3,
            "verse": 35,
            "text": "Śreyān svabhāvo guṇavān / tat sangas tu sadoṣavat",
            "translation": "It is far better to discharge one's prescribed duty imperfectly than another's duty well.",
            "source": "Bhagavad Gita",
        },
        "BG-4.13": {
            "chapter": 4,
            "verse": 13,
            "text": "Cātur-varṇyaṁ mayā sṛṣṭaṁ / guṇa-karma-vibhāgaśaḥ",
            "translation": "According to the three modes of material nature and the work associated with them, the four divisions of human society are created.",
            "source": "Bhagavad Gita",
        },
        "BG-6.46": {
            "chapter": 6,
            "verse": 46,
            "text": "Yoginām api sarveṣāṁ / mad-gatenāntarātmanā",
            "translation": "And of all yogis, he who always abides in Me with great faith, worshiping Me in transcendental loving service, is most intimately united with Me.",
            "source": "Bhagavad Gita",
        },
        "BG-13.2": {
            "chapter": 13,
            "verse": 2,
            "text": "Kṣetrajñaṁ cāpi māṁ viddhi / sarva-kṣetreṣu bhārata",
            "translation": "O Bharata, you should understand that I am also the knower in all bodies.",
            "source": "Bhagavad Gita",
        },
        "BG-18.66": {
            "chapter": 18,
            "verse": 66,
            "text": "Sarva-dharmān parityajya / mām ekaṁ śaraṇaṁ vraja",
            "translation": "Abandon all varieties of religion and just surrender unto Me. I shall deliver you from all sinful reactions.",
            "source": "Bhagavad Gita",
        },
        # Upanishads
        "Isha-1": {
            "chapter": 1,
            "verse": 1,
            "text": "Īśāvāsyam idaṁ sarvaṁ / yat kiñca jagatyāṁ jagat",
            "translation": "All of this is to be covered by the Lord. Whatever exists in this universe is the property of the Lord.",
            "source": "Isha Upanishad",
        },
        "Katha-2.3.1": {
            "chapter": 2,
            "verse": 3,
            "text": "Ātmānaṁ rathinaṁ viddhi / śarīraṁ ratham eva ca",
            "translation": "Know the self as master of the chariot, and the body as the chariot itself.",
            "source": "Katha Upanishad",
        },
        "Mundaka-2.2.11": {
            "chapter": 2,
            "verse": 11,
            "text": "Brahmavit brahmaiva bhavati",
            "translation": "One who knows Brahman becomes Brahman itself.",
            "source": "Mundaka Upanishad",
        },
        "Chandogya-3.14.1": {
            "chapter": 3,
            "verse": 14,
            "text": "Tat tvam asi",
            "translation": "Thou art That - the ultimate reality is the same as your innermost self.",
            "source": "Chandogya Upanishad",
        },
        # Brahma Sutras
        "BS-1.1.1": {
            "chapter": 1,
            "verse": 1,
            "text": "Athāto brahma-jijñāsā",
            "translation": "Now, therefore, the inquiry into Brahman - the ultimate reality and source of all existence.",
            "source": "Brahma Sutras",
        },
        "BS-1.1.2": {
            "chapter": 1,
            "verse": 2,
            "text": "Janmādy asya yataḥ",
            "translation": "Brahman is that from which all beings are born, by which they live, and into which they finally return.",
            "source": "Brahma Sutras",
        },
    }

    output_file = OUTPUT_DIR / "bhagavad_gita_pdf.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mock_verses, f, ensure_ascii=False, indent=2)

    print(f"✓ Generated mock PDF data: {len(mock_verses)} verses")
    return mock_verses


if __name__ == "__main__":
    generate_mock_pdf_data()
