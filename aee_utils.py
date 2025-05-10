# aee_utils.py
# AEE Projesi için genel yardımcı fonksiyonlar.
# v1.0.2 (Era): Import aee_core_classes_era olarak düzeltildi.

from typing import Dict, List, Optional, Any

# Era sürümündeki DOĞRU sınıfı import et
try:
    from aee_core_classes_era import Proposition # Düzeltildi!
except ImportError:
    print("Utils Error: Could not import Proposition class from aee_core_classes_era.py.")
    Proposition = None

# ... (Fonksiyonların geri kalanı aynı) ...
def get_proposition_by_id(prop_id: str, kb: Dict[str, Proposition]) -> Optional[Proposition]:
    if not Proposition: return None
    return kb.get(prop_id)

def get_linked_propositions(prop_id: str, kb: Dict[str, Proposition], link_type: str = 'all') -> List[Proposition]:
    linked_props: List[Proposition] = []
    if not Proposition: return linked_props
    main_prop = get_proposition_by_id(prop_id, kb)
    if not main_prop: return linked_props
    link_ids: List[str] = []
    if hasattr(main_prop, 'epistemic_data') and main_prop.epistemic_data:
        if link_type == 'supports' or link_type == 'all':
            if hasattr(main_prop.epistemic_data, 'supports') and main_prop.epistemic_data.supports: link_ids.extend(main_prop.epistemic_data.supports)
        if link_type == 'contradicts' or link_type == 'all':
            if hasattr(main_prop.epistemic_data, 'contradicts') and main_prop.epistemic_data.contradicts: link_ids.extend(main_prop.epistemic_data.contradicts)
    processed_ids = set()
    for linked_id in link_ids:
        if linked_id not in processed_ids:
            linked_prop = get_proposition_by_id(linked_id, kb)
            if linked_prop: linked_props.append(linked_prop)
            processed_ids.add(linked_id)
    return linked_props

if __name__ == "__main__":
    print("aee_utils.py loaded...") # Kısaltıldı
    if Proposition: print("Proposition class imported successfully from aee_core_classes_era.")
    else: print("Proposition class could not be imported.")