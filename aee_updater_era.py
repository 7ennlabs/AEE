# aee_updater_era.py
# AEE Era Sürümü: Güven/Güvenilirlik güncellemeleri + Plausibility + Bias/Cycle Ceza
# v1.0.1 (Era): Bias flag kontrolü için debug print eklendi.

import math
from typing import Dict, List, Optional, Set
from collections import defaultdict

try:
    from aee_core_classes_era import Proposition
except ImportError:
    print("Updater Error: Could not import Proposition class from aee_core_classes_era.py.")
    Proposition = None

# --- Sabitler ---
DEFAULT_SOURCE_RELIABILITY = 0.6; RELIABLE_SOURCE_SCORE = 0.75; UNRELIABLE_SOURCE_SCORE = 0.35
MIN_CONFIDENCE = 0.01; MAX_CONFIDENCE = 0.99; MIN_RELIABILITY = 0.1; MAX_RELIABILITY = 1.0
SUPPORT_WEIGHT = 0.10; CONTRADICTION_WEIGHT = 0.35; RELIABILITY_DAMPENING_FACTOR = 0.5
BIAS_PENALTY_MULTIPLIER = 0.85; CIRCULAR_SUPPORT_PENALTY_MULTIPLIER = 0.75
PLAUSIBILITY_WEIGHT_FACTOR = 1.0

# --- Güvenilirlik Hesaplama ---
def calculate_source_reliability_era(source_id: str, kb: Dict[str, Proposition]) -> float:
    # ... (Aynı) ...
    if not Proposition: return DEFAULT_SOURCE_RELIABILITY
    props_from_source = [p for p in kb.values() if p.epistemic_data.source_id == source_id]
    if not props_from_source: return DEFAULT_SOURCE_RELIABILITY
    has_any_contradiction = any(hasattr(prop.epistemic_data, 'contradicts') and prop.epistemic_data.contradicts for prop in props_from_source)
    return UNRELIABLE_SOURCE_SCORE if has_any_contradiction else RELIABLE_SOURCE_SCORE

# --- Döngü Tespiti ---
def detect_circular_support_era(kb: Dict[str, Proposition]):
     # ... (Aynı) ...
    if not Proposition: return
    # print("  Running Circular Support Detection...")
    prop_ids = list(kb.keys()); visited_globally = set(); flagged_props_count = 0; circular_support_flag = "CIRCULAR_SUPPORT"
    for start_node_id in prop_ids:
        if start_node_id not in visited_globally:
            recursion_stack = set(); path = []
            def dfs_visit(current_node_id):
                nonlocal flagged_props_count; visited_globally.add(current_node_id); recursion_stack.add(current_node_id); path.append(current_node_id)
                current_prop = kb.get(current_node_id)
                if not current_prop or not getattr(current_prop.epistemic_data, 'supports', None): recursion_stack.remove(current_node_id); path.pop(); return False
                for neighbour_id in current_prop.epistemic_data.supports:
                    if neighbour_id not in visited_globally:
                        if dfs_visit(neighbour_id): return True
                    elif neighbour_id in recursion_stack:
                        # print(f"    -> Circular Support Detected involving node {neighbour_id[:8]}!")
                        try:
                            cycle_start_index = path.index(neighbour_id); cycle_nodes = path[cycle_start_index:]
                            # print(f"       Cycle: {' -> '.join([p[:8] for p in cycle_nodes])}")
                            for node_id_in_cycle in cycle_nodes:
                                node_prop = kb.get(node_id_in_cycle)
                                if node_prop and circular_support_flag not in node_prop.epistemic_data.bias_flags: node_prop.epistemic_data.bias_flags.append(circular_support_flag); flagged_props_count += 1
                        except ValueError: pass
                        return True
                recursion_stack.remove(current_node_id); path.pop(); return False
            dfs_visit(start_node_id)
    print(f"  Circular Support Detection complete. Flagged {flagged_props_count} propositions.")


# --- Güven Güncelleme (Era - Debug Eklendi) ---
def update_proposition_confidence_era(prop: Proposition, kb: Dict[str, Proposition], source_reliability_scores: Dict[str, float]):
    if not Proposition: return
    ep_data = prop.epistemic_data; initial_conf = ep_data.initial_confidence
    source_reliability = source_reliability_scores.get(ep_data.source_id, DEFAULT_SOURCE_RELIABILITY)
    adjusted_initial_conf = initial_conf * (1 - RELIABILITY_DAMPENING_FACTOR) + (initial_conf * source_reliability) * RELIABILITY_DAMPENING_FACTOR
    current_confidence = adjusted_initial_conf
    total_support_effect = 0.0
    if ep_data.supports:
        for supporter_id in ep_data.supports:
            supporter_prop = kb.get(supporter_id)
            if supporter_prop: total_support_effect += SUPPORT_WEIGHT * supporter_prop.epistemic_data.computed_confidence * (1 - current_confidence)
    current_confidence += total_support_effect
    total_contradiction_effect = 0.0
    if ep_data.contradicts:
        for contradictor_id in ep_data.contradicts:
            contradictor_prop = kb.get(contradictor_id)
            if contradictor_prop: total_contradiction_effect += CONTRADICTION_WEIGHT * contradictor_prop.epistemic_data.computed_confidence * current_confidence
    current_confidence -= total_contradiction_effect

    # !!! YENİ DEBUG PRINT !!!
    print(f"    !!! Checking Bias Flags for Prop {prop.prop_id[:8]} !!! Current Flags: {ep_data.bias_flags}")
    # Bias ve Çıkarım Cezaları
    if ep_data.bias_flags: # Bu kontrol neden False dönüyor?
        print(f"    -> Applying penalty for Bias Flags: {ep_data.bias_flags} to Prop {prop.prop_id[:8]}")
        if "CIRCULAR_SUPPORT" in ep_data.bias_flags:
            current_confidence *= CIRCULAR_SUPPORT_PENALTY_MULTIPLIER
            print(f"      -> Applied CIRCULAR_SUPPORT penalty. Confidence now: {current_confidence:.3f}")
        if any(flag != "CIRCULAR_SUPPORT" for flag in ep_data.bias_flags):
             current_confidence *= BIAS_PENALTY_MULTIPLIER
             print(f"      -> Applied general BIAS penalty. Confidence now: {current_confidence:.3f}")
    # else: # Debug: Neden girmediğini gör
        # print(f"    -> No Bias Flags found for Prop {prop.prop_id[:8]} at update time.")


    # Plausibility Skoru Etkisi
    plausibility = ep_data.plausibility_score
    if plausibility is not None:
        # print(f"    Applying Plausibility ({plausibility:.2f}) to Prop {prop.prop_id[:8]}. Confidence before: {current_confidence:.3f}")
        current_confidence *= (plausibility * PLAUSIBILITY_WEIGHT_FACTOR + (1-PLAUSIBILITY_WEIGHT_FACTOR))
        # print(f"      -> Confidence after plausibility: {current_confidence:.3f}")

    ep_data.computed_confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, current_confidence))

# --- Toplu Güncelleme Fonksiyonu (Era) ---
def run_updates_era(kb: Dict[str, Proposition]) -> Dict[str, Proposition]:
    # ... (Fonksiyonun geri kalanı aynı) ...
    if not Proposition or not kb: print("Knowledge Base is empty or Proposition class not available."); return kb
    print("\nRunning Era Updates (Reliability, Cycle Detection & Confidence Refinement)...")
    print("  Calculating source reliabilities...")
    source_ids = set(p.epistemic_data.source_id for p in kb.values()); source_reliability_scores: Dict[str, float] = {}
    for source_id in source_ids:
        reliability = calculate_source_reliability_era(source_id, kb); source_reliability_scores[source_id] = reliability
        for prop in kb.values():
             if prop.epistemic_data.source_id == source_id: prop.epistemic_data.reliability_score = reliability
    detect_circular_support_era(kb)
    print("  Updating proposition confidences (Era logic)...")
    propositions_to_update = list(kb.values()) # Önce listeye alalım
    for prop in propositions_to_update:
        update_proposition_confidence_era(prop, kb, source_reliability_scores)
    print("Updates complete.")
    return kb

# --- Test Bloğu ---
if __name__ == "__main__":
    # ... (Test bloğu öncekiyle aynı - değişiklik yok) ...
     print("\nTesting AEE Updater Module (Era Version - Bias Flag Check)...")
     # ... (Test kodunun geri kalanı aynı) ...