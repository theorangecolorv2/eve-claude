# Правильная функция поиска контейнера - скопируй в cache.py

def find_cache(sanderling: SanderlingService, timeout: float = 5.0) -> Optional[object]:
    """
    Найти Triglavian Cache (Bioadaptive/Biocombinative) в overview.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут поиска (сек)
        
    Returns:
        OverviewEntry контейнера или None
    """
    start = time.time()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        # Ищем контейнер по name или type
        for entry in state.overview:
            name_str = (entry.name or "").lower()
            type_str = (entry.type or "").lower()
            
            # Ищем по ключевым словам
            if any(keyword in name_str or keyword in type_str for keyword in [
                'bioadaptive cache',
                'biocombinative cache'
            ]):
                logger.debug(f"Найден контейнер: '{entry.name}' (type: {entry.type})")
                return entry
        
        time.sleep(0.5)
    
    # Если не нашли - логируем что есть в overview
    logger.warning("Контейнер не найден в overview!")
    state = sanderling.get_state()
    if state and state.overview:
        logger.warning(f"В overview {len(state.overview)} записей:")
        for entry in state.overview[:10]:
            logger.warning(f"  - {entry.name} (type: {entry.type})")
    
    return None


# Правильная функция wait_and_attack - строка 271

        # Найти контейнер в overview
        cache = None
        for e in state.overview:
            name_str = (e.name or "").lower()
            type_str = (e.type or "").lower()
            if any(keyword in name_str or keyword in type_str for keyword in [
                'bioadaptive cache',
                'biocombinative cache'
            ]):
                cache = e
                break


# Правильная функция wait_cache_death - строка 373

        # Проверяем есть ли контейнер в локе
        cache_locked = False
        if state.targets:
            for target in state.targets:
                name_str = (target.name or "").lower()
                type_str = (target.type or "").lower()
                if any(keyword in name_str or keyword in type_str for keyword in [
                    'bioadaptive cache',
                    'biocombinative cache'
                ]):
                    cache_locked = True
                    break
