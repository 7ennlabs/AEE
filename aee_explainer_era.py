# aee_explainer_era.py
# AEE Era Sürümü: Önermenin epistemik durumu hakkında plausibility dahil açıklama üretir.

from typing import Dict, List, Optional, Any

# Era sürümündeki sınıfları ve utils'i import et
try:
    from aee_core_classes_era import Proposition
    from aee_utils import get_proposition_by_id, get_linked_propositions
except ImportError:
    print("Error: Could not import dependencies from aee_core_classes_era.py or aee_utils.py.")
    Proposition = None

# --- Açıklama Üretme Fonksiyonu (Era) ---

def generate_explanation_era(prop_id: str, kb: Dict[str, Proposition]) -> str:
    """
    Verilen ID'ye sahip önermenin epistemik durumu hakkında (Plausibility dahil)
    insan tarafından okunabilir bir açıklama metni üretir.
    """
    if not Proposition: return "Error: Proposition class not available."

    prop = get_proposition_by_id(prop_id, kb)
    if not prop:
        return f"Error: Proposition with ID '{prop_id}' not found in the Knowledge Base."

    ep_data = prop.epistemic_data

    # Bağlantıları al
    supporters = get_linked_propositions(prop_id, kb, link_type='supports')
    contradictors = get_linked_propositions(prop_id, kb, link_type='contradicts')

    # Metin parçalarını oluştur (Era versiyonu)
    explanation_lines = []
    explanation_lines.append(f"--- Epistemic Explanation (Era) for Proposition ID: {prop.prop_id[:8]} ---")
    explanation_lines.append(f"Statement        : '{prop.text_span}'")
    explanation_lines.append(f"Extracted Struct : {'[NEGATED] ' if prop.is_negated else ''}"
                             f"{prop.subject_lemma} - {prop.relation_lemma} - {prop.value_lemma}")
    explanation_lines.append("-" * 20)
    explanation_lines.append(f"Source           : {ep_data.source_id} (Type: {ep_data.source_type or 'N/A'})")
    explanation_lines.append(f"Timestamp        : {ep_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    explanation_lines.append(f"Source Reliability: {ep_data.reliability_score:.2f}" if ep_data.reliability_score is not None else "N/A")
    # Plausibility bilgilerini ekle
    explanation_lines.append(f"Plausibility Score: {ep_data.plausibility_score:.2f}" if ep_data.plausibility_score is not None else "N/A")
    explanation_lines.append(f"Validation Notes : [{', '.join(ep_data.validation_notes) if ep_data.validation_notes else 'None'}]")
    explanation_lines.append(f"Confidence Score : {ep_data.computed_confidence:.3f} (Initial: {ep_data.initial_confidence:.2f})")
    explanation_lines.append("-" * 20)
    explanation_lines.append(f"Supporting Props ({len(supporters)}): "
                             f"[{', '.join([p.prop_id[:8] for p in supporters]) if supporters else 'None'}]")
    explanation_lines.append(f"Contradicting Props ({len(contradictors)}): "
                             f"[{', '.join([p.prop_id[:8] for p in contradictors]) if contradictors else 'None'}]")
    explanation_lines.append("-" * 20)
    explanation_lines.append(f"Potential Bias Flags: "
                             f"[{', '.join(ep_data.bias_flags) if ep_data.bias_flags else 'None'}]")
    explanation_lines.append("--- End of Explanation ---")

    return "\n".join(explanation_lines)


# --- Test Bloğu ---
if __name__ == "__main__":
    print("Testing AEE Explainer Module (Era Version)...")

    if Proposition:
        from aee_core_classes_era import EpistemicData # Era class'ını import et
        print("Creating a mock Knowledge Base for Era explainer testing...")
        kb_test: Dict[str, Proposition] = {}

        # Örnek önermeler (plausibility ve notlar dahil)
        ed1 = EpistemicData(source_id="src1:news.com", initial_confidence=0.8, computed_confidence=0.85, reliability_score=0.7, source_type='news')
        prop1 = Proposition("sky is blue", "sky is blue", ed1, "sky", "be", "blue", False)
        prop1.epistemic_data.plausibility_score = 0.95 # Manuel test plausibility

        ed2 = EpistemicData(source_id="src2:user_blog", initial_confidence=0.4, computed_confidence=0.2, reliability_score=0.3, source_type='blog')
        prop2 = Proposition("sky is green", "sky is green", ed2, "sky", "be", "green", False)
        prop2.epistemic_data.plausibility_score = 0.15 # Manuel test plausibility
        prop2.epistemic_data.validation_notes.append("Low plausibility based on common knowledge")
        prop2.epistemic_data.bias_flags.append("UNCOMMON_CLAIM")

        # Manuel link ekleyelim (örnek amaçlı)
        prop1.epistemic_data.contradicts.append(prop2.prop_id) # Gerçekte bunlar çelişmez ama test için ekleyelim
        prop2.epistemic_data.contradicts.append(prop1.prop_id)

        kb_test[prop1.prop_id] = prop1
        kb_test[prop2.prop_id] = prop2
        print(f"Mock KB created with {len(kb_test)} propositions.")

        # Test 1: Açıklama üretme (prop1 için)
        print("\n--- Generating Explanation for Prop 1 (Era) ---")
        explanation1 = generate_explanation_era(prop1.prop_id, kb_test)
        print(explanation1)

        # Test 2: Açıklama üretme (prop2 için - plausibility düşük)
        print("\n--- Generating Explanation for Prop 2 (Era - Low Plausibility) ---")
        explanation2 = generate_explanation_era(prop2.prop_id, kb_test)
        print(explanation2)
    else:
        print("Could not run tests because Proposition class import failed.")

    print("\nExplainer module (Era) testing complete.")