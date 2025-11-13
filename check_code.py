#!/usr/bin/env python3
"""
Diagnostic script to check if the code has the fix applied.
Run this to verify your local code matches the repository.
"""

print("=" * 70)
print("CODE DIAGNOSTIC CHECK")
print("=" * 70)

# Read the app.py file
with open('app.py', 'r') as f:
    content = f.read()

print("\n[1] Checking for problematic patterns...")
bad_patterns = [
    ('lambda t: resize_func(t)', 'Lambda in resize()'),
    ('lambda t: opacity_func(t)', 'Lambda in set_opacity()'),
    ('lambda t: position_func(t)', 'Lambda in set_position()'),
]

issues = []
for pattern, desc in bad_patterns:
    if pattern in content:
        print(f"  ✗ FOUND: {desc}")
        issues.append(desc)
    else:
        print(f"  ✓ OK: No {desc}")

print("\n[2] Checking for correct patterns...")
good_patterns = [
    ('clip.set_opacity(opacity_func)', 'Direct opacity_func reference'),
    ('clip.resize(resize_func)', 'Direct resize_func reference'),
    ('clip.set_position(position_func)', 'Direct position_func reference'),
]

for pattern, desc in good_patterns:
    count = content.count(pattern)
    if count > 0:
        print(f"  ✓ FOUND {count}x: {desc}")
    else:
        print(f"  ✗ MISSING: {desc}")

print("\n[3] Card transition specific check...")
card_start = content.find('def create_card_transition_clip')
card_end = content.find('def create_filmstrip_transition_clip')

if card_start != -1 and card_end != -1:
    card_func = content[card_start:card_end]
    
    if 'lambda t:' in card_func:
        print("  ✗ ERROR: Card transition has lambda wrapper!")
        print("  This WILL cause the 'function * float' error")
    else:
        print("  ✓ OK: Card transition has no lambda wrappers")
    
    if 'clip.set_opacity(opacity_func)' in card_func:
        print("  ✓ OK: Card transition uses direct opacity_func")
    else:
        print("  ✗ ERROR: Card transition doesn't use correct opacity call")
else:
    print("  ✗ ERROR: Could not find card transition function")

print("\n" + "=" * 70)
print("DIAGNOSIS RESULT")
print("=" * 70)

if issues:
    print("\n❌ CODE HAS ISSUES - ERROR WILL OCCUR")
    print("\nProblems found:")
    for issue in issues:
        print(f"  • {issue}")
    print("\nACTION REQUIRED:")
    print("  1. git pull origin copilot/add-transition-options")
    print("  2. git log --oneline -1  # Should show: fd12a1d")
    print("  3. Restart Flask server")
else:
    print("\n✅ CODE IS CORRECT - ERROR SHOULD NOT OCCUR")
    print("\nIf you're still seeing errors:")
    print("  1. STOP Flask server (Ctrl+C)")
    print("  2. Clear cache: rm -rf __pycache__")
    print("  3. START Flask server: python app.py")
    print("  4. Hard refresh browser (Ctrl+Shift+R)")

print("\n" + "=" * 70)
