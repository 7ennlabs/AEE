# aee_bias_detector.py
# AEE v3.0: Bilgi tabanındaki potansiyel yanlılıkları sezmek için sezgisel yöntemler uygular.
# v3.0.4 (Era): Import düzeltildi, Source Diversity'de initial_confidence kullanıldı, Arg Balance check basitleştirildi.

from typing import Dict, List, Optional, Counter
from collections import defaultdict, Counter

# Era sürümündeki DOĞRU sınıfları import et
try:
    from aee_core_classes_era import Proposition, EpistemicData
except ImportError:
    print("Bias Detector Error: Could not import from aee_core_classes_era.py.")
    Proposition = None; EpistemicData = None

# --- Yanlılık Sezme Fonksiyonları ---
def detect_source_diversity_bias(kb: Dict[str, Proposition], subject_threshold: int = 2, confidence_threshold: float = 0.6, diversity_threshold: int = 2):
    if not Proposition: return
    print(f"  Running Source Diversity Check...")
    subjects_of_interest = defaultdict(list)
    for prop_id, prop in kb.items():
        if prop.subject_lemma: subjects_of_interest[prop.subject_lemma].append(prop_id)
    flagged_props_count = 0
    for subject, prop_ids in subjects_of_interest.items():
        if len(prop_ids) >= subject_threshold:
            high_conf_props = []; source_types = set()
            for prop_id in prop_ids:
                prop = kb.get(prop_id)
                # initial_confidence kullanıyoruz (çünkü bu check update'ten önce çalışıyor)
                if prop and prop.epistemic_data.initial_confidence is not None and \
                   prop.epistemic_data.initial_confidence >= confidence_threshold:
                    high_conf_props.append(prop)
                    source_type = prop.epistemic_data.source_type # source_type None olabilir
                    source_types.add(source_type if source_type else "unknown_type") # None ise unknown ata
            if len(source_types) < diversity_threshold and high_conf_props:
                bias_flag = "SOURCE_MONOCULTURE"; print(f"    Potential Bias Detected: Subject '{subject}' low diversity ({len(source_types)}<{diversity_threshold}). Flagging {len(high_conf_props)} props.")
                for prop in high_conf_props:
                    if bias_flag not in prop.epistemic_data.bias_flags: prop.epistemic_data.bias_flags.append(bias_flag); flagged_props_count +=1
    print(f"  Source Diversity Check complete. Flagged {flagged_props_count} propositions.")

def detect_argument_balance_bias(kb: Dict[str, Proposition], confidence_threshold: float = 0.7):
    if not Proposition: return
    print(f"  Running Argument Balance Check...")
    flagged_props_count = 0; bias_flag = "POTENTIAL_UNBALANCED_ARG"
    for prop in kb.values():
        ep_data = prop.epistemic_data
        # computed_confidence kullan (bu check update'ten sonra da anlamlı olabilir, ama şimdilik önce çalışıyor)
        # Basitleştirilmiş kontrol: Listelerin varlığını ve içeriğini direkt kontrol et
        if ep_data.computed_confidence is not None and \
           ep_data.computed_confidence >= confidence_threshold and \
           ep_data.supports and not ep_data.contradicts: # Destek listesi dolu VE Çelişki listesi boş ise
            if bias_flag not in ep_data.bias_flags: ep_data.bias_flags.append(bias_flag); flagged_props_count += 1
    print(f"  Argument Balance Check complete. Flagged {flagged_props_count} propositions.")


def run_bias_detection_v3(kb: Dict[str, Proposition]):
    if not Proposition: print("Error: Cannot run bias detection..."); return
    print("\nRunning v3 Bias Detection Heuristics...")
    if kb: detect_source_diversity_bias(kb); detect_argument_balance_bias(kb)
    else: print("  Skipping bias detection as Knowledge Base is empty.")
    print("Bias Detection Heuristics complete.")

# --- Test Bloğu ---
if __name__ == "__main__":
    # ... (Test bloğu öncekiyle aynı - değişiklik yok) ...
    print("Testing AEE Bias Detector Module (v3.0.4 - Reviewed)...")
    if Proposition and EpistemicData: # EpistemicData kontrolü eklendi
        # ... Test kodunun geri kalanı aynı ...
        print("Creating a mock Knowledge Base for bias testing...")
        kb_test: Dict[str, Proposition] = {}
        ed_ai1=EpistemicData(source_id="techblog1", source_type="blog", initial_confidence=0.8, computed_confidence=0.85); p_ai1 = Proposition("AI is beneficial","AI is beneficial", ed_ai1, "ai","be","beneficial"); kb_test[p_ai1.prop_id]=p_ai1
        ed_ai2=EpistemicData(source_id="techblog2", source_type="blog", initial_confidence=0.7, computed_confidence=0.75); p_ai2 = Proposition("AI improves efficiency","AI improves efficiency", ed_ai2, "ai","improve","efficiency"); kb_test[p_ai2.prop_id]=p_ai2
        ed_ai3=EpistemicData(source_id="techblog3", source_type="blog", initial_confidence=0.9, computed_confidence=0.92); p_ai3 = Proposition("AI creates jobs","AI creates jobs", ed_ai3, "ai","create","job"); kb_test[p_ai3.prop_id]=p_ai3
        ed_cc1=EpistemicData(source_id="science.org", source_type="scientific_paper", initial_confidence=0.95, computed_confidence=0.96); p_cc1 = Proposition("warming is real","warming is real", ed_cc1, "warming","be","real"); kb_test[p_cc1.prop_id]=p_cc1
        ed_cc2=EpistemicData(source_id="news.com", source_type="news", initial_confidence=0.7, computed_confidence=0.72); p_cc2 = Proposition("warming is accelerated","warming is accelerated", ed_cc2, "warming","be","accelerated"); kb_test[p_cc2.prop_id]=p_cc2
        ed_safe=EpistemicData(source_id="safety_report", source_type="report", initial_confidence=0.9, computed_confidence=0.91); p_safe = Proposition("System X is safe","System X is safe", ed_safe, "system x","be","safe"); kb_test[p_safe.prop_id]=p_safe
        ed_support=EpistemicData(source_id="internal_memo", source_type="memo", initial_confidence=0.6, computed_confidence=0.65); p_support = Proposition("System X passed tests","System X passed tests", ed_support, "system x","pass","test"); kb_test[p_support.prop_id]=p_support
        p_safe.epistemic_data.supports.append(p_support.prop_id); print(f"Mock KB created with {len(kb_test)} propositions.")
        run_bias_detection_v3(kb_test)
        print("\n--- Final KB State (Bias Detector Test) ---"); [print(f"ID: {pid[:8]} | Subj: {p.subject_lemma} | InitConf: {p.epistemic_data.initial_confidence:.2f} | Bias: {p.epistemic_data.bias_flags}") for pid,p in kb_test.items()] # initial_confidence kullanıldı
    else: print("Could not run tests because class import failed.")
    print("\nBias Detector module testing complete.")