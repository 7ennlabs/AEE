# aee_updater.py
# AEE v2.0: Kaynak güvenilirliğini ve önerme güven skorlarını dinamik olarak günceller.
# v2.0.1: Kaynak güvenilirliği hesaplama mantığı düzeltildi/basitleştirildi.

import math
from typing import Dict, List, Optional
from collections import defaultdict

# v2.0 klasöründeki sınıfları import et
from aee_core_classes import Proposition

# --- Yardımcı Sabitler ve Parametreler ---
DEFAULT_SOURCE_RELIABILITY = 0.6 # Varsayılanı biraz artıralım
RELIABLE_SOURCE_SCORE = 0.75    # Çelişkisi olmayan kaynak skoru
UNRELIABLE_SOURCE_SCORE = 0.35  # Çelişkisi olan kaynak skoru
MIN_CONFIDENCE = 0.01
MAX_CONFIDENCE = 0.99
# MIN/MAX_RELIABILITY artık doğrudan atanıyor

# Güven güncelleme formülü için ağırlıklar (aynı)
SUPPORT_WEIGHT = 0.10
CONTRADICTION_WEIGHT = 0.35
RELIABILITY_DAMPENING_FACTOR = 0.5

# --- Kaynak Güvenilirliği Hesaplama (Düzeltilmiş/Basitleştirilmiş Mantık) ---
def calculate_source_reliability_v2(source_id: str, kb: Dict[str, Proposition]) -> float:
    """
    Belirli bir kaynağın güvenilirliğini, KB'deki o kaynaktan gelen
    önermelerin *herhangi bir çelişkiye karışıp karışmadığına* göre basitçe belirler.
    """
    props_from_source = [p for p in kb.values() if p.epistemic_data.source_id == source_id]

    if not props_from_source:
        return DEFAULT_SOURCE_RELIABILITY

    has_any_contradiction = False
    for prop in props_from_source:
        if prop.epistemic_data.contradicts: # Bu kaynaktan gelen bir önermenin çelişkisi var mı?
            has_any_contradiction = True
            break # Bir tane bulmak yeterli

    if has_any_contradiction:
        # print(f"DEBUG Reliability: Source {source_id} flagged as UNRELIABLE.")
        return UNRELIABLE_SOURCE_SCORE
    else:
        # print(f"DEBUG Reliability: Source {source_id} flagged as RELIABLE.")
        return RELIABLE_SOURCE_SCORE

# --- Önerme Güven Skoru Güncelleme (Aynı kaldı) ---
def update_proposition_confidence_v2(prop: Proposition, kb: Dict[str, Proposition], source_reliability_scores: Dict[str, float]):
    """
    Bir önermenin 'computed_confidence' değerini, başlangıç güveni, kaynak
    güvenilirliği ve destekleyici/çelişkili kanıtların güven skorlarına göre günceller.
    Not: Bu fonksiyon doğrudan prop nesnesini değiştirir.
    """
    ep_data = prop.epistemic_data
    initial_conf = ep_data.initial_confidence
    # Hesaplanan güvenilirliği kullan, yoksa varsayılanı kullan
    source_reliability = source_reliability_scores.get(ep_data.source_id, DEFAULT_SOURCE_RELIABILITY)

    # Güvenilirliği sönümlendirme faktörü ile başlangıç güvenini ayarla
    adjusted_initial_conf = initial_conf * (1 - RELIABILITY_DAMPENING_FACTOR) + \
                             (initial_conf * source_reliability) * RELIABILITY_DAMPENING_FACTOR

    current_confidence = adjusted_initial_conf

    # Destekleyici kanıtların etkisini ekle
    total_support_effect = 0.0
    if ep_data.supports:
        support_count = 0 # Debug
        for supporter_id in ep_data.supports:
            supporter_prop = kb.get(supporter_id)
            if supporter_prop:
                support_count += 1
                support_gain = SUPPORT_WEIGHT * supporter_prop.epistemic_data.computed_confidence * (1 - current_confidence)
                total_support_effect += support_gain
        # print(f"DEBUG Confidence {prop.prop_id[:4]}: Support effect calculated from {support_count} supporters.")
    current_confidence += total_support_effect

    # Çelişkili kanıtların etkisini çıkar
    total_contradiction_effect = 0.0
    if ep_data.contradicts:
        contradiction_count = 0 # Debug
        for contradictor_id in ep_data.contradicts:
            contradictor_prop = kb.get(contradictor_id)
            if contradictor_prop:
                contradiction_count += 1
                contradiction_loss = CONTRADICTION_WEIGHT * contradictor_prop.epistemic_data.computed_confidence * current_confidence
                total_contradiction_effect += contradiction_loss
        # print(f"DEBUG Confidence {prop.prop_id[:4]}: Contradiction effect calculated from {contradiction_count} contradictors.")
    current_confidence -= total_contradiction_effect

    # Güveni sınırlar içinde tut
    ep_data.computed_confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, current_confidence))

    # print(f"DEBUG Confidence {prop.prop_id[:4]}: Final computed confidence: {ep_data.computed_confidence:.3f}")


# --- Toplu Güncelleme Fonksiyonu (Aynı kaldı) ---
def run_updates_v2(kb: Dict[str, Proposition]) -> Dict[str, Proposition]:
    """
    Tüm KB üzerinde kaynak güvenilirliğini hesaplar ve ardından tüm
    önermelerin güven skorlarını günceller. Değiştirilmiş KB'yi döndürür.
    """
    print("\nRunning v2 Updates (Reliability & Confidence)...")
    if not kb:
        print("Knowledge Base is empty. No updates to run.")
        return kb

    # 1. Adım: Tüm kaynakların güvenilirliğini hesapla
    print("  Calculating source reliabilities...")
    source_ids = set(p.epistemic_data.source_id for p in kb.values())
    source_reliability_scores: Dict[str, float] = {}
    for source_id in source_ids:
        reliability = calculate_source_reliability_v2(source_id, kb)
        source_reliability_scores[source_id] = reliability
        # Hesaplanan güvenilirliği ilgili önermelerin EpistemicData'sına da yazalım
        for prop in kb.values():
             if prop.epistemic_data.source_id == source_id:
                  prop.epistemic_data.reliability_score = reliability

    # 2. Adım: Tüm önermelerin güven skorlarını güncelle
    print("  Updating proposition confidences...")
    propositions_to_update = list(kb.values())
    for prop in propositions_to_update:
        update_proposition_confidence_v2(prop, kb, source_reliability_scores)

    print("Updates complete.")
    return kb

# --- Test Bloğu (Aynı kaldı) ---
if __name__ == "__main__":
    # ... (Önceki test bloğu kodu burada - değişiklik yok) ...
    print("\nTesting AEE Updater Module (v2.0.1 - with updated reliability)...")
    from aee_core_classes import EpistemicData # Test için gerekli

    # Test için sahte KB oluşturalım
    kb_test: Dict[str, Proposition] = {}

    # Güvenilir Kaynak 1
    src_reliable = "reliable_source.com"
    ed_r1 = EpistemicData(source_id=src_reliable, initial_confidence=0.9)
    p_r1 = Proposition("sky is blue", "sky is blue", ed_r1, "sky", "be", "blue")
    kb_test[p_r1.prop_id] = p_r1

    ed_r2 = EpistemicData(source_id=src_reliable, initial_confidence=0.85)
    p_r2 = Proposition("grass is green", "grass is green", ed_r2, "grass", "be", "green")
    kb_test[p_r2.prop_id] = p_r2

    # Güvenilmez Kaynak 1
    src_unreliable = "unreliable_source.net"
    ed_u1 = EpistemicData(source_id=src_unreliable, initial_confidence=0.4)
    p_u1 = Proposition("sky is green", "sky is green", ed_u1, "sky", "be", "green")
    kb_test[p_u1.prop_id] = p_u1

    ed_u2 = EpistemicData(source_id=src_unreliable, initial_confidence=0.3)
    p_u2 = Proposition("sky is not blue", "sky is not blue", ed_u2, "sky", "be", "blue", is_negated=True) # p_r1 ile çelişir
    kb_test[p_u2.prop_id] = p_u2

    # Güvenilir Kaynak 2
    src_reliable2 = "another_reliable.org"
    ed_r3 = EpistemicData(source_id=src_reliable2, initial_confidence=0.8)
    p_r3 = Proposition("sky is blue", "reports say sky is blue", ed_r3, "sky", "be", "blue") # p_r1'i destekler
    kb_test[p_r3.prop_id] = p_r3

    print(f"\nInitial KB state (Before Linking & Updates): {len(kb_test)} propositions")

    # Linkleri manuel simüle et
    p_r1.epistemic_data.contradicts.append(p_u2.prop_id)
    p_u2.epistemic_data.contradicts.append(p_r1.prop_id)
    p_r1.epistemic_data.supports.append(p_r3.prop_id)
    p_r3.epistemic_data.supports.append(p_r1.prop_id)

    print("\nSimulated Linking complete.")

    # Güncellemeleri çalıştır
    updated_kb_test = run_updates_v2(kb_test)

    print("\n--- Final KB State (After Updates) ---")
    for prop_id, prop_obj in updated_kb_test.items():
         print(f"ID: {prop_id[:8]} | Src: {prop_obj.epistemic_data.source_id} "
               f"| InitConf: {prop_obj.epistemic_data.initial_confidence:.2f} "
               f"| SrcRel: {prop_obj.epistemic_data.reliability_score:.2f} "
               f"| FinalConf: {prop_obj.epistemic_data.computed_confidence:.3f} "
               f"| Supports: {len(prop_obj.epistemic_data.supports)} "
               f"| Contradicts: {len(prop_obj.epistemic_data.contradicts)}")

    print("\nUpdater module testing complete.")