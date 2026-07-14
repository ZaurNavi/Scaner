from __future__ import annotations
from typing import List
from .base import BaseControllerCollector
from .omada import OmadaCollector

def get_controller_collectors() -> List[BaseControllerCollector]:
    """Возвращает список включенных контроллерных коллекторов с отчетом о статусе."""
    collectors = []
    
    omada = OmadaCollector()
    if omada.is_enabled():
        print("  [CONTROLLERS] ✅ Omada is ENABLED and configured.")
        collectors.append(omada)
    else:
        print("  [CONTROLLERS] ⚠️ Omada is DISABLED or missing credentials (check .env). Skipping.")
        
    # В будущем здесь легко добавятся:
    # unifi = UniFiCollector()
    # if unifi.is_enabled(): 
    #     print("  [CONTROLLERS] ✅ UniFi is ENABLED and configured.")
    #     collectors.append(unifi)
    # else:
    #     print("  [CONTROLLERS] ⚠️ UniFi is DISABLED. Skipping.")
    
    return collectors
