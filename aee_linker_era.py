# aee_linker_era.py
# AEE Era Sürümü: Önermeler arasındaki bağlantıları bulur.
# Genişletilmiş zıtlıklar, basit eşanlamlı/ilişki kontrolü içerir.

from typing import Dict, List, Optional, Set
import pprint

# Era sürümündeki sınıfları import et
try:
    from aee_core_classes_era import Proposition
except ImportError:
     print("Linker Error: Could not import Proposition class from aee_core_classes_era.py.")
     Proposition = None

# --- Genişletilmiş Zıtlıklar ve Eşanlamlılar Sözlüğü (Era.2b) ---

# Daha fazla zıtlık ekleyelim
opposites = {
    "hot": "cold", "fast": "slow", "big": "small", "on": "off", "up": "down",
    "large": "small", "tall": "short", "good": "bad", "right": "wrong", "left": "right",
    "true": "false", "correct": "incorrect", "same": "different", "similar":"different",
    "liquid": "solid", "gas": "solid", "liquid": "gas", # Belki daha iyi yönetilmeli
    "open": "closed", "light": "dark", "heavy":"light", "happy": "sad", "rich": "poor",
    "increase": "decrease", "expand": "contract", "allow": "forbid", "permit":"forbid",
    "warm": "cold", "cool":"warm", "cool":"hot", # 'cool' ara değer
    "wet": "dry", "full": "empty", "present": "absent", "alive": "dead",
    "win": "lose", "pass": "fail", "accept": "reject", "remember": "forget",
    "love": "hate", "friend": "enemy", "begin": "end", "start":"finish", "start":"end",
    "always": "never", "often": "rarely", "sometimes":"never", # Frekans
    "safe":"dangerous", "possible":"impossible", "legal":"illegal",
    "essential": "inessential", "beneficial":"harmful", "great":"terrible" # Daha soyut
}
# Çift yönlü yap
bidirectional_opposites = {}
for k, v in opposites.items():
    bidirectional_opposites.setdefault(k, v) # İlk eşleşmeyi koru
    bidirectional_opposites.setdefault(v, k) # Tersini de ekle (varsa üzerine yazma)

# Basit eşanlamlılar (Destek kontrolünde kullanılabilir)
synonyms = {
    "big": "large", "fast": "quick", "rapid": "fast", "begin": "start",
    "finish": "end", "permit": "allow", "great":"good", # Çok basit liste
    "essential": "important", "beneficial": "helpful", "harmful":"dangerous"
}
# Çift yönlü yap
bidirectional_synonyms = synonyms.copy()
for k, v in synonyms.items():
    bidirectional_synonyms.setdefault(k, v)
    bidirectional_synonyms.setdefault(v, k)

# İlişkisel Çelişki Kuralları (Basit)
# Örn: (Subject, Relation, Value)
relational_contradictions = {
    ("be", "bigger"): [("be", "smaller"), ("be", "equal")], # X > Y çelişir X < Y veya X = Y ile
    ("be", "smaller"): [("be", "bigger"), ("be", "equal")],
    ("be", "equal"): [("be", "bigger"), ("be", "smaller"), ("be", "different")],
    # ... daha fazla kural eklenebilir ...
}


# --- Yardımcı Fonksiyon ---
def print_prop_debug_info(p: Proposition, prefix=""):
    if not p: return "None"
    return (f"{prefix}ID:{p.prop_id[:8]}, "
            f"S:'{p.subject_lemma}', R:'{p.relation_lemma}', V:'{p.value_lemma}', "
            f"Neg:{p.is_negated}")

# --- Bağlantı Bulma Fonksiyonu (Era) ---
def find_and_link_evidence_era(new_prop: Proposition, kb: Dict[str, Proposition]):
    """
    Era Sürümü: Önermeler arası bağlantıları bulur (Genişletilmiş Zıtlıklar, Eşanlamlılar, İlişkiler).
    """
    if not kb or not Proposition: return
    new_subj=new_prop.subject_lemma; new_rel=new_prop.relation_lemma; new_val=new_prop.value_lemma; new_neg=new_prop.is_negated; new_id=new_prop.prop_id
    if not all([new_subj, new_rel, new_val]): return

    for old_prop_id, old_prop in kb.items():
        if new_id == old_prop_id: continue
        old_subj=old_prop.subject_lemma; old_rel=old_prop.relation_lemma; old_val=old_prop.value_lemma; old_neg=old_prop.is_negated

        # --- Eşleşme Kontrolleri ---
        is_contradiction = False
        is_support = False

        # 1. Aynı Özne ve İlişki Durumu: Değeri veya Negasyonu kontrol et
        if new_subj is not None and new_subj == old_subj and new_rel is not None and new_rel == old_rel:
            nv = new_val.strip() if isinstance(new_val, str) else new_val
            ov = old_val.strip() if isinstance(old_val, str) else old_val

            # 1a. Doğrudan Çelişki
            if nv == ov and new_neg != old_neg: is_contradiction = True; print(f"[Linker Found]: Direct Contradiction ({new_id[:4]} vs {old_prop_id[:4]})")
            # 1b. Zıt Kavram Çelişkisi
            elif (bidirectional_opposites.get(nv) == ov or bidirectional_opposites.get(ov) == nv) and new_neg == old_neg: is_contradiction = True; print(f"[Linker Found]: Opposing Concept ('{nv}' vs '{ov}') ({new_id[:4]} vs {old_prop_id[:4]})")
            # 1c. Destek (Aynı veya Eşanlamlı Değer)
            elif new_neg == old_neg and (nv == ov or bidirectional_synonyms.get(nv) == ov or bidirectional_synonyms.get(ov) == nv): is_support = True; print(f"[Linker Found]: Support (Same/Synonym Value) ({new_id[:4]} vs {old_prop_id[:4]})")

        # 2. İlişkisel Çelişki Durumu (Aynı Özne ve Değer, farklı ilişki)
        # Örn: X > Y vs X < Y (Burada Y değer oluyor)
        elif new_subj is not None and new_subj == old_subj and new_val is not None and new_val == old_val and new_neg == old_neg:
             rel_key_new = (new_rel, new_val) # (ilişki, değer)
             rel_key_old = (old_rel, old_val) # (ilişki, değer) - değerler aynı

             # TODO: Bu kısım daha genel hale getirilmeli. Şimdilik basit karşılaştırmalar.
             # Örneğin: 'bigger' vs 'smaller' gibi ilişkiler
             if bidirectional_opposites.get(new_rel) == old_rel or bidirectional_opposites.get(old_rel) == new_rel:
                  is_contradiction = True; print(f"[Linker Found]: Opposing Relation ('{new_rel}' vs '{old_rel}') for same Subj/Val ({new_id[:4]} vs {old_prop_id[:4]})")


        # 3. TODO: Daha karmaşık ilişkiler (Entailment vb.) buraya eklenebilir.


        # --- Bağlantıları Güncelle ---
        if is_contradiction:
            if old_prop_id not in new_prop.epistemic_data.contradicts: new_prop.epistemic_data.contradicts.append(old_prop_id)
            if new_id not in old_prop.epistemic_data.contradicts: old_prop.epistemic_data.contradicts.append(new_id)
        elif is_support:
            if old_prop_id not in new_prop.epistemic_data.supports: new_prop.epistemic_data.supports.append(old_prop_id)
            if new_id not in old_prop.epistemic_data.supports: old_prop.epistemic_data.supports.append(new_id)


# --- Test Bloğu ---
if __name__ == "__main__":
    print("Testing AEE Linker Module (Era Version - Enhanced Relations)...")
    if Proposition:
        from aee_core_classes_era import EpistemicData
        kb_test: Dict[str, Proposition] = {}
        print("\nCreating Mock Propositions...")
        # Örnekler
        ed1=EpistemicData(source_id="src1"); p1 = Proposition("A > B", "A is bigger than B", ed1, "a", "be", "bigger", False); kb_test[p1.prop_id]=p1
        ed2=EpistemicData(source_id="src2"); p2 = Proposition("A < B", "A is smaller than B", ed2, "a", "be", "smaller", False) # p1 ile çelişmeli (ilişki)
        ed3=EpistemicData(source_id="src3"); p3 = Proposition("C is fast", "C runs fast", ed3, "c", "run", "fast", False)
        ed4=EpistemicData(source_id="src4"); p4 = Proposition("C is quick", "C is quick", ed4, "c", "be", "quick", False) # p3 ile eşanlamlı değer (ilişki farklı) - BULAMAZ
        ed5=EpistemicData(source_id="src5"); p5 = Proposition("D is large", "D is large", ed5, "d", "be", "large", False)
        ed6=EpistemicData(source_id="src6"); p6 = Proposition("D is big", "D is big", ed6, "d", "be", "big", False) # p5 ile eşanlamlı değer (destek)
        ed7=EpistemicData(source_id="src7"); p7 = Proposition("E is hot", "E is hot", ed7, "e", "be", "hot", False)
        ed8=EpistemicData(source_id="src8"); p8 = Proposition("E is not cold", "E is not cold", ed8, "e", "be", "cold", True) # p7 ile çelişmeli (zıt + negasyon)

        # Linklemeyi Çalıştır
        print("\nRunning Linker...")
        props_to_link = [p2, p3, p4, p5, p6, p7, p8]
        for prop in props_to_link:
            find_and_link_evidence_era(prop, kb_test) # Era linker'ı çağır
            kb_test[prop.prop_id] = prop # Sonra KB'ye ekle

        # Sonuçları Yazdır
        print("\n--- Final KB State (Enhanced Linker Test) ---")
        for prop_id, prop_obj in kb_test.items():
             supports_str = ', '.join([pid[:4] for pid in prop_obj.epistemic_data.supports]) if prop_obj.epistemic_data.supports else "None"
             contradicts_str = ', '.join([pid[:4] for pid in prop_obj.epistemic_data.contradicts]) if prop_obj.epistemic_data.contradicts else "None"
             print(f"ID: {prop_id[:8]} ({prop_obj.subject_lemma} {prop_obj.relation_lemma} {prop_obj.value_lemma}) | Supports: [{supports_str}] | Contradicts: [{contradicts_str}]")

    else: print("Could not run tests due to import error.")
    print("\nEnhanced Linker module testing complete.")