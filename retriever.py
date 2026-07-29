

"""Retrieve the policy document most relevant to a customer question."""

from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


POLICIES_DIRECTORY = Path(__file__).with_name("policies")
MIN_RELEVANCE_SCORE = 0.15
TOP_K = 1

def load_policies() -> list[dict[str, str]]:
    """Load every Markdown policy file from the policies directory."""

    policies = []

    for policy_path in sorted(POLICIES_DIRECTORY.glob("*.md")):
        policies.append(
            {
                "name": policy_path.name,
                "content": policy_path.read_text(encoding="utf-8"),
            }
        )

    return policies


def retrieve_policy(question: str) -> dict[str, object] | None:
    """Return the strongest relevant policy, or None when nothing matches."""

    policies = load_policies()
    policy_texts = [policy["content"] for policy in policies]

    vectorizer = TfidfVectorizer(stop_words="english")
    policy_vectors = vectorizer.fit_transform(policy_texts)
    question_vector = vectorizer.transform([question])

    scores = cosine_similarity(question_vector, policy_vectors)[0]
    top_match_indices = scores.argsort()[::-1][:TOP_K]
    best_match_index = int(top_match_indices[0])
    best_score = float(scores[best_match_index])

    if best_score < MIN_RELEVANCE_SCORE:
        return None

    return {
        "name": policies[best_match_index]["name"],
        "content": policies[best_match_index]["content"],
        "score": best_score,
    }