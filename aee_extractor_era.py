# aee_extractor_era.py
# Metinleri işler ve AEE Projesi için temel önermeleri çıkarır.
# Era Sürümü Adım 2a: Başlangıç güven ataması dilbilimsel ipuçlarını dikkate alır.

import spacy
from spacy.tokens import Doc, Span, Token
from datetime import datetime
from typing import List, Optional, Tuple

# Era sürümündeki DOĞRU sınıfları import et
try:
    from aee_core_classes_era import Proposition, EpistemicData
except ImportError:
     print("Extractor Error: Could not import Proposition/EpistemicData class from aee_core_classes_era.py.")
     Proposition = None; EpistemicData = None

# --- spaCy Model Yükleme ---
NLP_MODEL = None; MODEL_NAME = "en_core_web_md" # Model
try:
    NLP_MODEL = spacy.load(MODEL_NAME)
    # print(f"DEBUG Extractor: spaCy model '{MODEL_NAME}' loaded.") # Debug için açılabilir
except OSError:
    print(f"Extractor Error: spaCy English model '{MODEL_NAME}' not found. Please run: python -m spacy download {MODEL_NAME}")

# --- Bu fonksiyon eksikti ve eklendi: process_with_spacy ---
def process_with_spacy(text: str) -> Optional[Doc]:
    """
    Verilen metni spaCy ile işler ve Doc nesnesini döndürür.
    NLP_MODEL yüklenemezse None döndürür.
    """
    if NLP_MODEL is None:
        print(f"Error: spaCy model not loaded. Cannot process text.")
        return None
    
    try:
        return NLP_MODEL(text)
    except Exception as e:
        print(f"Error processing text with spaCy: {e}")
        return None

# --- Yardımcı Fonksiyonlar ---
def get_token_lemma(token: Optional[Token]) -> Optional[str]:
    """ Verilen Token nesnesinin lemma'sını (kökünü) küçük harfle güvenli bir şekilde alır. """
    return token.lemma_.lower() if token else None

def find_negation(token: Optional[Token], sentence: Span) -> bool:
    """ Verilen Token'a (genellikle fiil) veya ilişkili olduğu ana yapıya bağlı bir negasyon olup olmadığını kontrol eder. """
    if not token: return False
    # Doğrudan bağlı 'neg'
    for child in token.children:
        if child.dep_ == "neg": return True
    # Yardımcı fiile bağlı 'neg' (örn: "is not running")
    if token.head != token and token.head.pos_ == "AUX":
         for child in token.head.children:
              if child.dep_ == "neg": return True
    # 'Be' fiiline bağlı 'neg' (örn: "sky is not blue")
    if token.lemma_ == "be":
         for child in token.children:
             if child.dep_ == "neg": return True
         # Bazen 'not' advmod olabilir (örn: 'is simply not true')
         for child in token.children:
             if child.dep_ == "advmod" and child.lemma_ == "not": return True

    # Cümlenin genelinde negasyon var mı diye daha geniş kontrol (basit)
    # Bu çok güvenilir olmayabilir ama bazı durumları yakalayabilir
    # for sent_token in sentence:
    #     if sent_token.dep_ == "neg": return True
    return False


# --- Güven Hesaplama Yardımcıları (Era.2a) ---
def get_source_based_confidence(source_id: str) -> float:
    """ Kaynak ID'sine göre temel bir başlangıç güven skoru döndürür. """
    source_id_lower = source_id.lower()
    # Daha fazla tür ve daha belirgin skorlar
    if "user" in source_id_lower or "comment" in source_id_lower or "diary" in source_id_lower: return 0.45
    elif "blog" in source_id_lower or "opinion" in source_id_lower or "forum" in source_id_lower: return 0.50
    elif "news" in source_id_lower or any(domain in source_id_lower for domain in [".com", ".org", ".net"]): return 0.65 # Genel web/haber
    elif "wiki" in source_id_lower: return 0.70
    elif "report" in source_id_lower or "fact_sheet" in source_id_lower: return 0.75
    elif "textbook" in source_id_lower or ".edu" in source_id_lower : return 0.80
    elif "science" in source_id_lower or "research" in source_id_lower or "expert" in source_id_lower or "paper" in source_id_lower: return 0.85
    elif "common_knowledge" in source_id_lower: return 0.90
    else: return 0.55 # Bilinmeyen için biraz daha yüksek varsayılan

def calculate_linguistic_confidence_modifier(sent: Span) -> float:
    """ Cümledeki kesinlik/belirsizlik ifadelerine bakarak güven ayarlama çarpanı döndürür. """
    modifier = 1.0 # Varsayılan: Nötr
    uncertainty_markers = {"may", "might", "could", "perhaps", "possibly", "suggest", "appear", "seem", "likely", "probably", "believe", "think", "assume", "sometimes"}
    certainty_markers = {"will", "must", "definitely", "certainly", "undoubtedly", "always", "never", "prove", "confirm", "show", "demonstrate", "fact"} # 'be' fiilleri hariç
    negation_markers = {"not", "n't", "never", "no", "none"} # find_negation bunu zaten yapmalı ama ek kontrol

    has_uncertainty = False
    has_certainty = False
    has_negation_cue = False # Sadece 'not' değil, 'never' gibi kelimeler için

    for token in sent:
        lemma = token.lemma_.lower()
        pos = token.pos_
        dep = token.dep_

        # Belirsizlik İşaretleri
        if (pos in ["AUX", "VERB"] and lemma in uncertainty_markers) or \
           (pos == "ADV" and lemma in uncertainty_markers):
            has_uncertainty = True
            # print(f"  DEBUG LING: Found uncertainty: '{token.text}' ({lemma})")
            break # Bir tane yeterli

    # Eğer belirsizlik yoksa kesinlik ara (birbirini dışlasın şimdilik)
    if not has_uncertainty:
        for token in sent:
            lemma = token.lemma_.lower()
            pos = token.pos_
            if (pos == "ADV" and lemma in certainty_markers) or \
               (pos == "VERB" and lemma in certainty_markers):
                 has_certainty = True
                 # print(f"  DEBUG LING: Found certainty: '{token.text}' ({lemma})")
                 break # Bir tane yeterli

    # Ayarlayıcıyı belirle
    if has_uncertainty:
        modifier = 0.80
    elif has_certainty:
        modifier = 1.15 # Kesinlik etkisini biraz artıralım

    # print(f"  DEBUG LING: Sentence '{sent.text[:30]}...' -> Modifier: {modifier}")
    return modifier

# --- Güven sınırları için sabitler (eksikti) ---
MIN_CONFIDENCE = 0.01
MAX_CONFIDENCE = 0.99

# --- Ana Önerme Çıkarım Fonksiyonu (Era) ---
def extract_propositions_era(doc: Doc, source_id: str) -> List[Proposition]:
    """
    Era Sürümü: Önermeleri çıkarır ve başlangıç güvenini hem kaynağa
    hem de dilbilimsel ifadelere göre ayarlar.
    """
    propositions: List[Proposition] = []
    if not doc or not Proposition or not EpistemicData: return propositions

    for sent in doc.sents:
        # print(f"DEBUG EXTRACT: Processing sentence: '{sent.text}'") # Cümleyi görmek için açılabilir
        root: Token = sent.root
        subject: Optional[Token] = None; prop_object: Optional[Token] = None; attribute: Optional[Token] = None

        # Basit Özne/Nesne/Nitelik çıkarımı
        # Özne bulma (nsubj veya nsubjpass)
        for token in sent:
            if token.dep_ in ["nsubj", "nsubjpass"] and token.head == root:
                subject = token
                break
        if not subject:
            # print("  DEBUG EXTRACT: No subject found for root:", root.text)
            continue # Özne yoksa atla

        # Nesne veya nitelik bulma
        for token in sent:
             if token.head == root:
                 if token.dep_ in ["dobj", "pobj"]: # Direct or prepositional object
                     prop_object = token
                 elif token.dep_ in ["attr", "acomp", "xcomp"]: # Attribute or complement
                     attribute = token
                 # Eğer hem dobj hem attr varsa ne yapmalı? Şimdilik biri yeterli.

        # İlişki ve Değer Belirleme
        relation_lemma = get_token_lemma(root)
        subject_lemma = get_token_lemma(subject)
        value_lemma = None
        value_token = attribute if attribute else prop_object # Nitelik öncelikli olabilir

        if value_token:
            value_lemma = get_token_lemma(value_token)
            # Değere bağlı negasyon var mı? (örn: "not happy")
            is_negated = find_negation(value_token, sent) # Cümleyi de verelim
        else:
             # Eğer değer yoksa (örn: "He runs.") bu yapıyla önerme çıkaramayız
             # print(f"  DEBUG EXTRACT: No value found for S:{subject_lemma} R:{relation_lemma}")
             continue

        # Fiile bağlı negasyonu kontrol et
        if not is_negated: # Eğer değere bağlı negasyon yoksa fiile bağlıyı kontrol et
            is_negated = find_negation(root, sent)


        # Anlamlı bir yapı bulunduysa devam et
        if subject_lemma and relation_lemma and value_lemma:
            # Güven ve Tipi Hesapla
            source_based_conf = get_source_based_confidence(source_id)
            linguistic_modifier = calculate_linguistic_confidence_modifier(sent)
            initial_confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, source_based_conf * linguistic_modifier))

            # Kaynak tipini tahmin et
            source_type = None; sid_lower = source_id.lower()
            # ... (Önceki tip tahmin kodları aynı) ...
            if "user" in sid_lower: source_type = "user"
            elif "news" in sid_lower: source_type = "news"
            # ... (diğerleri) ...
            elif "common" in sid_lower: source_type = "common"
            elif "textbook" in sid_lower: source_type = "textbook"


            # Epistemik veriyi oluştur
            ep_data = EpistemicData(
                source_id=source_id,
                initial_confidence=initial_confidence,
                source_type=source_type
            )

            # Yeni Proposition nesnesini oluştur
            new_prop = Proposition(
                text_span=sent.text, # v1'de tüm cümle, daha sonra geliştirilebilir
                sentence_text=sent.text,
                epistemic_data=ep_data,
                subject_lemma=subject_lemma,
                relation_lemma=relation_lemma,
                value_lemma=value_lemma,
                is_negated=is_negated
            )
            # print(f"  DEBUG EXTRACT: Extracted: {new_prop}") # Çıkarılanı görmek için açılabilir
            propositions.append(new_prop)
        # else:
            # print(f"  DEBUG EXTRACT: Incomplete structure S:{subject_lemma}, R:{relation_lemma}, V:{value_lemma}")


    return propositions

# --- Test Bloğu ---
if __name__ == "__main__":
     print("\nTesting AEE Extractor Module (Era Version - Linguistic Confidence)...")
     
     if not NLP_MODEL:
         print("Cannot run tests because spaCy model is not loaded.")
     else:
         print("Creating test sentences...")
         test_sentences = [
             "The sky is blue.", # Normal doğru cümle
             "The sky is not blue.", # Negasyon
             "The sky might be blue.", # Belirsizlik
             "The sky is definitely blue.", # Kesinlik
             "System A is bigger than System B.", # İlişkisel
         ]
         
         for text in test_sentences:
             print(f"\nProcessing: '{text}'")
             doc = process_with_spacy(text)
             if doc:
                 props = extract_propositions_era(doc, "test_source")
                 for prop in props:
                     print(f"  Extracted: {prop}")
                     print(f"    Subject: {prop.subject_lemma}, Relation: {prop.relation_lemma}, Value: {prop.value_lemma}")
                     print(f"    Negated: {prop.is_negated}, Confidence: {prop.epistemic_data.initial_confidence:.2f}")
             else:
                 print("  Failed to process with spaCy.")