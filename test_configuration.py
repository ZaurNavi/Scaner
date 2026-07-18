#!/usr/bin/env python3
"""
Полная тестовая матрица Configuration Layer v1.6.9.
Покрывает все 15 требований спецификации ES-1.6.9.
"""

import sys
import time
import tempfile
import json
from pathlib import Path

def main():
    print("=" * 80)
    print("  Configuration Layer v1.6.9 — Full Architecture Verification Test")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    # === ТЕСТ 1: Загрузка конфигурации по умолчанию ===
    print("\n📦 ТЕСТ 1: Загрузка конфигурации по умолчанию...")
    try:
        from configuration import get_config_manager, ConfigurationManager
        # Сброс singleton
        ConfigurationManager._instance = None
        
        config = get_config_manager()
        config.load({})
        config.freeze()
        
        assert config.get("monitor.scan_interval") == 60
        assert config.get("snmp.enabled") == True
        print("   ✅ Конфигурация по умолчанию загружена и заморожена")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # === ТЕСТ 2: Загрузка пользовательской конфигурации ===
    print("\n⚙️  ТЕСТ 2: Загрузка пользовательской конфигурации...")
    try:
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        
        config2 = get_config_manager()
        custom_config = {
            "monitor.scan_interval": 120,
            "snmp.community": "secret_private",
            "fingerprint.minimum_confidence": 0.85
        }
        config2.load(custom_config)
        
        assert config2.get("monitor.scan_interval") == 120
        assert config2.get("snmp.community") == "secret_private"
        assert config2.get("fingerprint.minimum_confidence") == 0.85
        print("   ✅ Пользовательская конфигурация успешно применена")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 3: Проверка типов всех параметров ===
    print("\n🔤 ТЕСТ 3: Проверка типов всех параметров...")
    try:
        config3 = get_config_manager()
        assert isinstance(config3.get("monitor.worker_threads"), int)
        assert isinstance(config3.get("fingerprint.minimum_confidence"), float)
        assert isinstance(config3.get("monitor.console_output"), bool)
        print("   ✅ Типы параметров строго соблюдены")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 4: Проверка валидации значений (диапазоны) ===
    print("\n📏 ТЕСТ 4: Проверка валидации значений (диапазоны)...")
    try:
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        
        config4 = get_config_manager()
        
        # Попытка загрузить значение ниже минимума
        try:
            config4.load({"monitor.worker_threads": 0})  # min_value=1
            print("   ❌ Валидатор не сработал на значение ниже минимума")
            failed += 1
        except Exception as e:
            if "below minimum" in str(e):
                print("   ✅ Валидатор корректно отклонил значение ниже минимума")
                passed += 1
            else:
                raise e
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 5: Проверка freeze() — иммутабельность ===
    print("\n🔒 ТЕСТ 5: Проверка freeze() (изменение после заморозки)...")
    try:
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        
        config5 = get_config_manager()
        config5.load({})
        config5.freeze()
        
        # Попытка загрузить новые данные после freeze
        try:
            config5.load({"monitor.scan_interval": 999})
            print("   ❌ Load после freeze() не вызвал исключение")
            failed += 1
        except Exception as e:
            if "frozen" in str(e).lower():
                print("   ✅ Конфигурация защищена от изменений после freeze()")
                passed += 1
            else:
                raise e
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 6: Проверка производительности ===
    print("\n⚡ ТЕСТ 6: Проверка производительности...")
    try:
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        
        config6 = get_config_manager()
        
        start = time.time()
        config6.load({})
        load_time = (time.time() - start) * 1000
        
        start_access = time.time()
        for _ in range(10000):
            _ = config6.get("monitor.scan_interval")
        access_time = (time.time() - start_access) * 1000
        
        assert load_time <= 100, f"Загрузка заняла {load_time:.2f}ms (> 100ms)"
        assert access_time < 10, f"10000 доступов заняли {access_time:.2f}ms (должно быть < 10ms)"
        
        print(f"   ✅ Производительность: загрузка {load_time:.2f}ms, 10k доступов {access_time:.2f}ms (O(1))")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 7: Проверка получения параметров по группам ===
    print("\n📂 ТЕСТ 7: Проверка получения параметров по группам...")
    try:
        config7 = get_config_manager()
        snmp_group = config7.group("SNMP")
        
        assert "snmp.enabled" in snmp_group
        assert "snmp.community" in snmp_group
        assert "monitor.scan_interval" not in snmp_group
        print("   ✅ Группировка параметров работает корректно")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 8: Проверка неизвестных параметров ===
    print("\n❓ ТЕСТ 8: Проверка обработки неизвестных параметров...")
    try:
        config8 = get_config_manager()
        try:
            config8.get("completely.fake.parameter")
            print("   ❌ Получение неизвестного параметра не вызвало ошибку")
            failed += 1
        except Exception as e:
            if "Unknown parameter" in str(e):
                print("   ✅ Запрос неизвестного параметра корректно отклонён")
                passed += 1
            else:
                raise e
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 9: Проверка сериализации (dump/export/save) ===
    print("\n📦 ТЕСТ 9: Проверка сериализации (dump/export/save)...")
    try:
        config9 = get_config_manager()
        dump_data = config9.dump()
        export_data = config9.export()
        
        assert isinstance(dump_data, dict)
        assert "monitor.scan_interval" in dump_data
        assert isinstance(export_data["monitor.scan_interval"], dict)
        assert "type" in export_data["monitor.scan_interval"]
        assert "description" in export_data["monitor.scan_interval"]
        
        # Тест сохранения в JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        config9.save_to_json(temp_path)
        assert Path(temp_path).exists()
        
        # Загружаем обратно
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        config9_reload = get_config_manager()
        config9_reload.load_from_json(temp_path)
        assert config9_reload.get("monitor.scan_interval") == dump_data["monitor.scan_interval"]
        
        Path(temp_path).unlink()
        
        print("   ✅ Сериализация (dump/export/save) работает корректно")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 10: Проверка Singleton паттерна ===
    print("\n👤 ТЕСТ 10: Проверка Singleton паттерна...")
    try:
        from configuration import get_config_manager, ConfigurationManager
        cfg_a = get_config_manager()
        cfg_b = get_config_manager()
        
        assert cfg_a is cfg_b, "Экземпляры ConfigurationManager должны быть идентичны"
        print("   ✅ ConfigurationManager является строгим Singleton")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 11: Проверка reload() ===
    print("\n🔄 ТЕСТ 11: Проверка reload()...")
    try:
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        
        config11 = get_config_manager()
        config11.load({"monitor.scan_interval": 100})
        config11.freeze()
        
        # После freeze() нельзя load(), но можно reload()
        config11.reload({"monitor.scan_interval": 200})
        assert config11.get("monitor.scan_interval") == 200
        print("   ✅ reload() корректно перезагружает конфигурацию")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 12: Проверка validate() ===
    print("\n✔️  ТЕСТ 12: Проверка validate()...")
    try:
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        
        config12 = get_config_manager()
        config12.load({})
        
        # validate() должен пройти без ошибок
        assert config12.validate() == True
        print("   ✅ validate() работает корректно")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 13: Проверка отключения Engine через enabled = false ===
    print("\n🔌 ТЕСТ 13: Проверка отключения компонентов (enabled = false)...")
    try:
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        
        cfg_13 = get_config_manager()
        cfg_13.load({"snmp.enabled": False, "netflow.enabled": False})
        
        assert cfg_13.get("snmp.enabled") == False
        assert cfg_13.get("netflow.enabled") == False
        print("   ✅ Флаги enabled корректно обрабатываются")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 14: Проверка детерминированности конфигурации ===
    print("\n🎲 ТЕСТ 14: Проверка детерминированности...")
    try:
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        
        cfg_14a = get_config_manager()
        cfg_14a.load({"monitor.scan_interval": 100})
        dump_a = cfg_14a.dump()
        
        ConfigurationManager._instance = None
        cfg_14b = get_config_manager()
        cfg_14b.load({"monitor.scan_interval": 100})
        dump_b = cfg_14b.dump()
        
        assert dump_a == dump_b, "Конфигурация должна быть детерминированной"
        print("   ✅ Конфигурация полностью детерминирована")
        passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ТЕСТ 15: Проверка защиты кэша после freeze() ===
    print("\n🛡️  ТЕСТ 15: Проверка защиты кэша после freeze()...")
    try:
        from configuration import ConfigurationManager
        ConfigurationManager._instance = None
        
        config15 = get_config_manager()
        config15.load({})
        config15.freeze()
        
        # Попытка модифицировать кэш напрямую
        try:
            config15._cache["monitor.scan_interval"] = 999
            print("   ❌ Кэш можно модифицировать после freeze()")
            failed += 1
        except TypeError:
            print("   ✅ Кэш защищён от модификаций после freeze() (MappingProxyType)")
            passed += 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        failed += 1

    # === ИТОГОВАЯ СВОДКА ===
    print("\n" + "=" * 80)
    print(f"📈 ИТОГОВАЯ СВОДКА:")
    print(f"   ✅ Пройдено тестов: {passed}")
    print(f"   ❌ Провалено тестов: {failed}")
    print(f"   📊 Успешность: {(passed / (passed + failed)) * 100:.1f}%")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 Configuration Layer v1.6.9 — ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("   Фундамент платформы завершен. Готов к серии 1.7.x (Intelligence Layer).")
        return 0
    else:
        print(f"\n⚠️  Обнаружено {failed} проблем. Требуется исправление.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
