"""
Quick diagnostic script to check module imports and backend status.
"""
import sys
import importlib.util

def check_module(module_path, module_name):
    """Check if a module exists and where it's being imported from"""
    spec = importlib.util.find_spec(module_path)
    if spec:
        print(f"✓ {module_name}: {spec.origin}")
        return True
    else:
        print(f"✗ {module_name}: NOT FOUND")
        return False

print("=" * 60)
print("Backend Module Diagnostic")
print("=" * 60)

# Check new modular structure
print("\n[New Modules]")
check_module("app.services.script", "Script Package")
check_module("app.services.script.generator", "ScriptGenerator")
check_module("app.services.tts", "TTS Package")
check_module("app.config", "Config")
check_module("app.utils.state_manager", "StateManager")

# Check old modules (should not exist)
print("\n[Old Modules - Should NOT exist]")
old_script = check_module("app.services.script_generator", "OLD script_generator")
old_tts = check_module("app.services.tts_service", "OLD tts_service")

if old_script or old_tts:
    print("\n⚠️  WARNING: Old modules still importable!")
    print("   Please rename them to .old extension")
else:
    print("\n✓ Old modules successfully disabled")

print("\n" + "=" * 60)
