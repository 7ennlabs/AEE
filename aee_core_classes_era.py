# aee_core_classes_era.py
# AEE Projesi için temel veri yapılarını tanımlar.
# Era Sürümü: EpistemicData'ya plausibility eklendi.

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class EpistemicData:
    """Bir önerme ile ilişkili epistemik (bilgibilimsel) verileri tutar."""
    source_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    initial_confidence: float = 0.5
    computed_confidence: float = 0.5
    source_type: Optional[str] = None
    reliability_score: Optional[float] = None

    # v2+ Bağlantılar
    supports: List[str] = field(default_factory=list)
    contradicts: List[str] = field(default_factory=list)

    # v3+ İşaretler
    bias_flags: List[str] = field(default_factory=list)

    # YENİ ERA Alanları:
    plausibility_score: Optional[float] = None # Önermenin genel makullük/olabilirlik skoru (örn: 0.0-1.0)
    validation_notes: List[str] = field(default_factory=list) # Makullük kontrolünden gelen notlar (örn: ['Contradicts common sense'])

    other_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.computed_confidence = self.initial_confidence

@dataclass
class Proposition:
    """Metinden çıkarılan bir bilgi birimini (önermeyi) temsil eder."""
    # Non-default fields first
    text_span: str
    sentence_text: str
    epistemic_data: EpistemicData # Artık Era uyumlu EpistemicData içerecek

    # Default fields last
    prop_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subject_lemma: Optional[str] = None
    relation_lemma: Optional[str] = None
    value_lemma: Optional[str] = None
    is_negated: bool = False
    other_analysis: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        # Raporlamada kolaylık için __str__ güncellenebilir, şimdilik aynı.
        neg_str = "[NEGATED] " if self.is_negated else ""
        return (f"Prop({self.prop_id[:8]}): {neg_str}"
                f"{self.subject_lemma} - {self.relation_lemma} - {self.value_lemma} "
                f"(Conf: {self.epistemic_data.computed_confidence:.2f}, Src: {self.epistemic_data.source_id})")

# --- Test Bloğu ---
if __name__ == "__main__":
    print("Testing AEE Core Classes (Era Version)...")
    ed1 = EpistemicData(source_id="src_test", initial_confidence=0.7)
    ed1.plausibility_score = 0.9 # Test için manuel atama
    ed1.validation_notes.append("Seems plausible based on initial check.")
    print(f"Created EpistemicData (Era): {ed1}")
    prop1 = Proposition(
        text_span="Test span", sentence_text="Test sentence.", epistemic_data=ed1,
        subject_lemma="test", relation_lemma="be", value_lemma="ok"
    )
    print(f"Created Proposition (Era): {prop1}")
    print(f"  Plausibility: {prop1.epistemic_data.plausibility_score}")
    print(f"  Validation Notes: {prop1.epistemic_data.validation_notes}")
    print("\nCore classes (Era) seem functional.")