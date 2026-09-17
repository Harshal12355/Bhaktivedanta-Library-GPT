"""
Demo Responses for Testing
Provides mock LLM responses when DeepSeek and Ollama are not available
"""

DEMO_RESPONSES = {
    "dharma": """Dharma, as explained in the Bhagavad Gita, refers to one's duty, righteousness,
and moral obligation. Krishna emphasizes that each person has a specific role to play in society
based on their nature and position. The fulfillment of one's dharma is essential for spiritual
progress and the maintenance of cosmic order (rita).

In the context of the Gita, Krishna teaches Arjuna that he must perform his duty as a warrior
without attachment to the results. This concept of performing one's dharma selflessly is central
to the path of karma yoga (yoga of action).""",

    "yoga": """Yoga, in the context of the Bhagavad Gita, means union - the joining of the individual
soul with the Supreme. Krishna presents multiple paths of Yoga for different types of practitioners:

1. Karma Yoga - the yoga of selfless action without attachment to results
2. Bhakti Yoga - the yoga of devotion and loving service
3. Jnana Yoga - the yoga of knowledge and wisdom
4. Raja Yoga - the yoga of meditation and mental discipline

Krishna teaches that all these paths lead to the same destination - enlightenment and liberation
from the cycle of rebirth.""",

    "bhakti": """Bhakti means devotion - the loving, emotional connection between the soul and the
Supreme Lord Krishna. It is considered the most direct and accessible path to spiritual realization,
as it engages the heart as well as the mind.

In the Gita, Krishna states that among all yogis, those who constantly think of Him with all their
devotion are considered to be the most perfectly situated in yoga. Bhakti involves:

- Loving surrender to Krishna
- Constant remembrance of the divine
- Service with devotion
- Complete trust in Krishna's grace

Krishna promises that anyone who performs Bhakti yoga with sincere devotion will ultimately reach Him.""",

    "duty": """Krishna teaches Arjuna that duty (dharma) is one's prescribed responsibility based on
one's nature, abilities, and position in society. The Gita emphasizes that it is far better to perform
one's own duty imperfectly than to perform another's duty well.

The key to fulfilling duty righteously is to:
- Perform actions without attachment to results
- Act in accordance with spiritual principles
- Maintain inner equanimity whether successful or unsuccessful
- Offer all actions as a sacrifice to the Divine

This path of righteous action leads to purification of the heart and spiritual advancement.""",

    "default": """I appreciate your question about Vedic philosophy. Based on the Bhagavad Gita and
the verses retrieved, here's what I can share with you:

The Bhagavad Gita offers profound teachings on the nature of reality, the path to liberation, and
the various means of spiritual practice. Krishna emphasizes that the ultimate goal is union with the
Supreme, which can be achieved through different paths suited to different individuals.

The key teachings include the importance of duty, the power of devotion, the wisdom of non-attachment,
and the continuous pursuit of spiritual knowledge. These teachings are as relevant today as they were
thousands of years ago.""",
}


def get_demo_response(query: str) -> str:
    """Get a demo response based on query content"""
    query_lower = query.lower()

    if any(word in query_lower for word in ["dharma", "duty", "righteousness", "law"]):
        return DEMO_RESPONSES["dharma"]
    elif any(word in query_lower for word in ["yoga", "meditation", "practice", "discipline"]):
        return DEMO_RESPONSES["yoga"]
    elif any(word in query_lower for word in ["bhakti", "devotion", "love", "krishna"]):
        return DEMO_RESPONSES["bhakti"]
    elif any(word in query_lower for word in ["duty", "responsibility", "action"]):
        return DEMO_RESPONSES["duty"]
    else:
        return DEMO_RESPONSES["default"]
