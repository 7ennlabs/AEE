# aee_era_main.py
# AEE Era Sürümü İşlem Hattını Çalıştıran Ana Script
# Era Extractor ve Linker entegre edildi. (Era Adım 2 Tamamlandı - Proje Kodu Bitti!)

import time
from typing import Dict, List, Optional, Any

# Era sürümü klasöründeki TÜM modülleri import et
try:
    from aee_core_classes_era import Proposition, EpistemicData
    from aee_extractor_era import process_with_spacy, extract_propositions_era, NLP_MODEL # Era Extractor
    from aee_linker_era import find_and_link_evidence_era # Era Linker
    from aee_updater_era import run_updates_era # Era Updater
    from aee_explainer_era import generate_explanation_era # Era Explainer
    from aee_bias_detector import run_bias_detection_v3 # v3 Bias Detector
    from aee_validator import check_plausibility_v_era # Era Validator
    from aee_utils import get_proposition_by_id # Utils
except ImportError as e:
    print(f"Fatal Error: Could not import necessary modules. Check file paths and dependencies in AEE/Era folder.")
    print(f"Import Error: {e}")
    exit()

# --- Raporlama Fonksiyonu (Era) ---
def report_kb_era(kb: Dict[str, Proposition]):
    # ... (Öncekiyle aynı - değişiklik yok) ...
    print("\n" + "="*70); print(" AEE Era Version - Knowledge Base Report (Final Status)"); print("="*70)
    if not kb: print("Knowledge Base is empty."); print("="*70); return
    print(f"Total propositions in KB: {len(kb)}"); print("-"*70)
    propositions_by_source: Dict[str, List[Proposition]] = {};
    def sort_key(prop): conf = prop.epistemic_data.computed_confidence; return conf if conf is not None else -1.0
    sorted_props = sorted(list(kb.values()), key=sort_key, reverse=True)
    for prop in sorted_props: source = prop.epistemic_data.source_id; propositions_by_source.setdefault(source, []).append(prop)
    for source_id in sorted(propositions_by_source.keys()):
        props = propositions_by_source[source_id]; source_reliability = getattr(props[0].epistemic_data, 'reliability_score', None)
        reliability_str = f"{source_reliability:.2f}" if source_reliability is not None else "N/A"
        print(f"\n--- Source: {source_id} (Calculated Reliability: {reliability_str}) ---")
        for prop in props:
            neg_str = "[NEGATED] " if prop.is_negated else ""
            supports_str = ', '.join([pid[:8] for pid in prop.epistemic_data.supports]) if prop.epistemic_data.supports else "None"
            contradicts_str = ', '.join([pid[:8] for pid in prop.epistemic_data.contradicts]) if prop.epistemic_data.contradicts else "None"
            bias_str = ', '.join(prop.epistemic_data.bias_flags) if prop.epistemic_data.bias_flags else "None"
            plausibility_score = prop.epistemic_data.plausibility_score; plausibility_str = f"{plausibility_score:.2f}" if plausibility_score is not None else "N/A"
            validation_notes_str = ', '.join(prop.epistemic_data.validation_notes) if prop.epistemic_data.validation_notes else "None"
            conf_score = prop.epistemic_data.computed_confidence; conf_str = f"{conf_score:.3f}" if conf_score is not None else "N/A"
            init_conf_score = prop.epistemic_data.initial_confidence; init_conf_str = f"{init_conf_score:.2f}" if init_conf_score is not None else "N/A"
            print(f"  Prop ID : {prop.prop_id}")
            print(f"    Struct: {neg_str}{prop.subject_lemma} - {prop.relation_lemma} - {prop.value_lemma}")
            print(f"    Conf. : {conf_str} (Initial: {init_conf_str})") # Initial conf'un değiştiğini göreceğiz
            print(f"    Links : Supports: [{supports_str}] | Contradicts: [{contradicts_str}]")
            print(f"    Biases: [{bias_str}]")
            print(f"    Plaus.: {plausibility_str} | Notes: [{validation_notes_str}]")
    print("\n" + "="*70); print(" End of KB Report "); print("="*70)


# --- Ana İşlem Fonksiyonu (Era - Final) ---
def run_aee_era_pipeline(inputs: List[Dict[str, str]]) -> Dict[str, Proposition]:
    """
    Verilen girdiler için AEE Era işlem hattını tam olarak çalıştırır
    (Era Extract, Plausibility Check, Era Linker, Bias Detect, Era Update).
    """
    if NLP_MODEL is None: print("FATAL ERROR: spaCy model not loaded."); return {}

    print("\nStarting AEE Era Final Pipeline...")
    knowledge_base: Dict[str, Proposition] = {}
    start_time = time.time()

    # 1. Adım: Extract (Era) & Validate Plausibility & Link (Era)
    print("Phase 1: Extracting(Era), Validating Plausibility, and Linking(Era)...")
    all_extracted_props_before_linking: List[Proposition] = []
    for item in inputs:
        source_id = item.get("source_id", f"unknown_source_{int(time.time())}"); text = item.get("text", "")
        if not text: continue
        doc = process_with_spacy(text)
        if doc:
            # ERA EXTRACTOR ÇAĞIRILIYOR
            extracted_props = extract_propositions_era(doc, source_id)
            for prop in extracted_props:
                 plausibility_score, validation_notes = check_plausibility_v_era(prop)
                 if hasattr(prop, 'epistemic_data') and prop.epistemic_data:
                    prop.epistemic_data.plausibility_score = plausibility_score
                    if validation_notes: prop.epistemic_data.validation_notes.extend(validation_notes)
                 all_extracted_props_before_linking.append(prop)
    print(f"  Phase 1a (Extraction(Era) & Validation) complete. Total extracted: {len(all_extracted_props_before_linking)}")

    print("  Phase 1b (Linking(Era))...")
    if find_and_link_evidence_era: # Era linker fonksiyonu
        for new_prop in all_extracted_props_before_linking:
             if new_prop.prop_id not in knowledge_base:
                  # ERA LINKER ÇAĞIRILIYOR
                  find_and_link_evidence_era(new_prop, knowledge_base)
                  knowledge_base[new_prop.prop_id] = new_prop
    else: print("Skipping linking due to import error.")
    print(f"Phase 1 (Extract(Era), Validate, Link(Era)) complete. KB size: {len(knowledge_base)}")

    # 1.5 Adım: Bias Detection (v3)
    print("\nPhase 1.5: Running Bias Detection Heuristics...")
    if run_bias_detection_v3 and knowledge_base: run_bias_detection_v3(knowledge_base)
    else: print("Skipping Bias Detection due to import error or empty KB.")
    print("Phase 1.5 complete.")

    # 2. Adım: Update (Era Mantığı ile)
    print("\nPhase 2: Running Era Updates (Reliability, Cycle Detect, Plausibility-aware Confidence)...")
    if run_updates_era: updated_knowledge_base = run_updates_era(knowledge_base) # ERA Updater
    else: print("Skipping Updates due to import error."); updated_knowledge_base = knowledge_base
    print("Phase 2 complete.")

    end_time = time.time(); print(f"\nPipeline finished in {end_time - start_time:.2f} seconds.")
    return updated_knowledge_base

# --- Ana Çalışma Bloğu ---
if __name__ == "__main__":
    # Era sürümünün tüm yeteneklerini test edecek örnek girdiler
    sample_inputs_era_final = [
         {
            "source_id": "fact_sheet_1", "source_type": "fact",
            "text": "Water is H2O. The sun is hot. Ice is cold." # Yüksek plausibility, basit zıtlık
        },
        {
            "source_id": "opinion_blog_A", "source_type": "blog",
            "text": "Maybe the new policy is good. It could improve things. Perhaps." # Düşük başlangıç güveni (linguistic)
        },
         {
            "source_id": "opinion_blog_B", "source_type": "blog",
            "text": "The new policy is definitely bad! It will undoubtedly harm the economy. It is not good." # Yüksek başlangıç güveni (linguistic) + Zıtlık (good/bad)
        },
        {
             "source_id": "report_X", "source_type": "report",
             "text": "System Alpha is bigger than System Beta. System Beta is not small compared to Alpha." # İlişkisel çelişki?
        },
        {
             "source_id": "another_report", "source_type": "report",
             "text": "System Alpha is large." # 'bigger' ile eşanlamlı? (Synonym desteği için)
        },
         { # Döngü + Plausibility düşük + Kaynak Tekelciliği
             "source_id": "conspiracy_theory.blog", "source_type": "blog",
             "text": "The moon landing was faked because the photos look wrong. The photos look wrong because the shadows are incorrect. The shadows are incorrect because the landing was faked."
              # Extractor muhtemelen bunları çıkaramaz, ama bias/cycle test için dursun.
              # Ekstra düşük plausibility testi:
              "Also, the moon is made of cheese."
         }
    ]

    # İşlem hattını çalıştır
    final_kb_era = run_aee_era_pipeline(sample_inputs_era_final)

    # Genel KB Raporunu yazdır
    report_kb_era(final_kb_era)

    # Örnek Açıklamaları Üret ve Yazdır
    print("\n" + "#"*70)
    print(" AEE Era Version - Generating Explanations")
    print("#"*70)
    if final_kb_era and generate_explanation_era:
        ids_to_explain = list(final_kb_era.keys())
        print(f"\nGenerating explanations for all {len(ids_to_explain)} propositions...\n")
        for prop_id in ids_to_explain:
            explanation = generate_explanation_era(prop_id, final_kb_era) # ERA Explainer
            print(explanation)
            print("-" * 40)
    else: print("Knowledge Base is empty or Explainer not available.")
    print("\n" + "#"*70); print(" Explanation generation step complete."); print("#"*70)

    # PROJE KODLAMASI TAMAMLANDI MESAJI
    print("\n###########################################################################")
    print("# AEE ERA VERSION - ALL PLANNED CORE FEATURE CODING COMPLETE!")
    print("# All modules updated to Era versions where planned.")
    print("# Project includes: Extraction(Era.2a), Validation(Era.1), Linking(Era.2b),")
    print("# Bias Detection(v3), Updates(Era.1d), Explanation(Era.1e).")
    print("#")
    print("# FINAL STEP (FOR YOU): TESTING & EVALUATION!")
    print("# - Run this script: python aee_era_main.py")
    print("# - Examine the report and explanations thoroughly.")
    print("# - Check if initial confidence reflects modality.")
    print("# - Check if more links (support/contradiction) are found.")
    print("# - Check bias flags, plausibility, final confidence.")
    print("# - Try your own texts!")
    print("# - Provide your final feedback and evaluation.")
    print("###########################################################################")