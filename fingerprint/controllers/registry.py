from __future__ import annotations
from typing import List
from .base import BaseControllerCollector
from .omada import OmadaCollector

def get_controller_collectors() -> List[BaseControllerCollector]:
    """Возвращает список включенных контроллерных коллекторов."""
    collectors = []
    
    omada = OmadaCollector()
    if omada.is_enabled():
        collectors.append(omada)
        
    # В будущем здесь легко добавятся:
    # unifi = UniFiCollector()
    # if unifi.is_enabled(): collectors.append(unifi)
    
    return collectors
