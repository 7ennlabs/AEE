# aee_validator.py
# AEE Era Sürümü: Önermelerin makullüğünü/gerçekliğini kontrol eder.

from typing import Dict, List, Optional, Tuple

try:
    # Era sürümündeki sınıfları import et
    from aee_core_classes_era import Proposition
except ImportError:
    print("Error: Could not import Proposition class from aee_core_classes_era.py.")
    Proposition = None

# --- Makullük Kontrol Fonksiyonu ---

def check_plausibility_v_era(proposition: Proposition) -> Tuple[Optional[float], List[str]]:
    """
    Verilen bir önermenin genel makullüğünü/olabilirliğini değerlendirir.
    Era sürümünde bu fonksiyon, harici bilgiye (simüle edilmiş veya gerçek)
    başvurarak daha akıllı hale getirilecektir.
    Şimdilik basit bir varsayılan değer döndürür.

    Returns:
        Tuple[Optional[float], List[str]]: (Plausibility Score [0.0-1.0], Validation Notes List)
                                            Score None ise kontrol yapılamadı demektir.
    """
    if not Proposition or not proposition:
        return None, ["Error: Invalid proposition input."]

    plausibility_score: Optional[float] = None
    validation_notes: List[str] = []

    # --- BURASI ERA SÜRÜMÜNÜN ÖRTÜK BİLGİ KULLANIM NOKTASI ---
    # Gerçek uygulamada burada:
    # 1. Önerme analiz edilir (örn: "gökyüzü", "renk", "yeşil").
    # 2. Harici bilgi kaynağına sorgu gönderilir (örn: Web search, Knowledge Graph,
    #    veya benim tarafımdan eğitilmiş/değerlendirilmiş bir model).
    # 3. Gelen sonuca göre skor ve notlar belirlenir.

    # Şimdilik (Subtlety için ve adım adım gitmek için):
    # Varsayılan olarak makul kabul edelim (1.0) ve not bırakmayalım.
    # Ana script'teki örnekler için manuel skorları SİMÜLE EDEBİLİRİZ.
    # VEYA basit anahtar kelime kontrolleri eklenebilir:
    subject = proposition.subject_lemma
    value = proposition.value_lemma
    if subject == "sky" and value not in ["blue", "grey", "gray", "black", "red", "orange", "pink", "purple"]: # Bilinen gökyüzü renkleri dışındaysa?
        plausibility_score = 0.2
        validation_notes.append("Value is an uncommon color for the sky.")
    elif subject == "water" and value in ["solid", "liquid", "gas", "steam", "ice"]: # Bilinen su halleri
         plausibility_score = 0.9
    # ... başka basit sağduyu kuralları eklenebilir ...
    else:
        # Diğer durumlar için varsayılan skor
        plausibility_score = 0.8 # Bilinmeyen durumlar için biraz daha düşük?

    # --- KONTROL BİTTİ ---

    # Skorun sınırlar içinde olduğundan emin ol (eğer atandıysa)
    if plausibility_score is not None:
        plausibility_score = max(0.0, min(1.0, plausibility_score))

    # print(f"DEBUG Validator: Prop '{proposition.prop_id[:8]}' Plausibility: {plausibility_score}, Notes: {validation_notes}")
    return plausibility_score, validation_notes


# --- Test Bloğu ---
if __name__ == "__main__":
    print("Testing AEE Validator Module (Era Version)...")

    if Proposition:
        from aee_core_classes_era import EpistemicData # Test için gerekli
        print("Creating mock propositions for validator testing...")

        # Örnek 1: Makul
        ed1 = EpistemicData(source_id="test1")
        prop1 = Proposition("sky is blue", "sky is blue", ed1, "sky", "be", "blue")
        score1, notes1 = check_plausibility_v_era(prop1)
        print(f"\nProp: {prop1.subject_lemma} - {prop1.value_lemma}")
        print(f"  Plausibility Score: {score1}, Notes: {notes1}")

        # Örnek 2: Makul Değil
        ed2 = EpistemicData(source_id="test2")
        prop2 = Proposition("sky is green", "sky is green", ed2, "sky", "be", "green")
        score2, notes2 = check_plausibility_v_era(prop2)
        print(f"\nProp: {prop2.subject_lemma} - {prop2.value_lemma}")
        print(f"  Plausibility Score: {score2}, Notes: {notes2}")

        # Örnek 3: Bilinmeyen Konu
        ed3 = EpistemicData(source_id="test3")
        prop3 = Proposition("Xyz is Fgh", "Xyz is Fgh", ed3, "xyz", "be", "fgh")
        score3, notes3 = check_plausibility_v_era(prop3)
        print(f"\nProp: {prop3.subject_lemma} - {prop3.value_lemma}")
        print(f"  Plausibility Score: {score3}, Notes: {notes3}")

    else:
        print("Could not run tests because Proposition class import failed.")

    print("\nValidator module testing complete.")