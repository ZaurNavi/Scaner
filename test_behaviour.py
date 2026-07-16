#!/usr/bin/env python3
"""
Изолированный тест Behaviour Engine.
Проверяет извлечение метрик, оценку правил и формирование фактов.
"""

import sys
from pathlib import Path
from storage.archivist import DatabaseManager, Repository
from history import HistoryService
from identity import IdentityService, IdentityRepository
from session import SessionEngine
from behaviour import BehaviourService

def main():
    print("=" * 60)
    print("  Behaviour Engine: Internal Logic Verification")
    print("=" * 60)

    # 1. Инициализация БД и сервисов
    db_path = Path("storage/archivist/sisu.db")
    if not db_path.exists():
        print("❌ База данных не найдена. Запустите сначала monitor.py")
        return 1

    db = DatabaseManager(db_path)
    conn = db.get_connection()
    
    # Берем первый попавшийся device_id из таблицы identity для теста
    cursor = conn.cursor()
    cursor.execute("SELECT device_id FROM identity LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print("❌ В базе нет устройств. Запустите monitor.py для сбора данных.")
        return 1
    
    device_id = row[0]
    print(f"\n🎯 Тестируем устройство: {device_id}")
    print("-" * 60)

    # 2. Инициализация зависимостей (ИСПРАВЛЕНО: используем правильный Repository)
    history_service = HistoryService(conn)
    identity_repo = IdentityRepository(db)
    identity_service = IdentityService(history_service, identity_repo)
    
    repo = Repository(db)
    session_engine = SessionEngine(history_service, repo)
    
    # 3. Запуск Behaviour Engine
    print("⚙️  Запуск Behaviour Engine...")
    behaviour_service = BehaviourService(history_service, identity_service, session_engine)
    
    # Получаем профиль и отладочную информацию
    profile = behaviour_service.get_profile(device_id)
    debug_info = behaviour_service.debug(device_id)

    if not profile or not debug_info:
        print("❌ Не удалось получить профиль или debug_info.")
        return 1

    # 4. Вывод сырых метрик (FeatureSet)
    print("\n📊 1. Извлеченные сырые метрики (FeatureSet):")
    features = profile.features
    for attr in ['average_session_duration', 'session_count', 'total_traffic', 
                 'idle_ratio', 'active_ratio', 'ap_changes', 'ssid_changes', 'lifetime_seconds']:
        val = getattr(features, attr, None)
        status = "✅" if val is not None and val != 0 else "⚠️"
        print(f"   {status} {attr:<25}: {val}")

    # 5. Вывод сработавших фактов (Facts)
    print(f"\n🧠 2. Сформированные факты (Detected Facts: {len(profile.facts)}):")
    if profile.facts:
        for fact in profile.facts:
            print(f"   ✅ [{fact.category.value.upper()}]")
            print(f"      • Метрика:   {fact.feature} = {fact.measured_value}")
            print(f"      • Порог:     {fact.threshold}")
            print(f"      • Оценка:    Score={fact.score}, Confidence={fact.confidence:.1f}%")
            print(f"      • Правило:   {fact.rule_id} ({', '.join(fact.matched_rules)})")
    else:
        print("   ⚠️ Факты не сформированы (ни одно правило не сработало).")

    # 6. Вывод пропущенных правил (Skipped Rules)
    print(f"\n🚫 3. Пропущенные правила (Skipped Rules: {len(debug_info.skipped_rules)}):")
    if debug_info.skipped_rules:
        for skipped in debug_info.skipped_rules[:5]: # Показываем первые 5
            print(f"   • {skipped}")
        if len(debug_info.skipped_rules) > 5:
            print(f"   ... и ещё {len(debug_info.skipped_rules) - 5} правил")
    else:
        print("   ✅ Все правила были оценены (ничего не пропущено).")

    # 7. Итоговая сводка
    print("\n" + "=" * 60)
    print("📈 ИТОГОВАЯ СВЕРКА:")
    print(f"   • Feature Coverage:  {profile.feature_coverage:.1f}%")
    print(f"   • Rule Match Ratio:  {profile.rule_match_ratio:.1f}%")
    print(f"   • Время выполнения:  {debug_info.computation_time_ms:.2f} мс")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
