#!/usr/bin/env python3
"""
测试effects更新修复
验证当服务器发送包含空effects的state时，本地effects能否被正确保留
"""

import sys
sys.path.insert(0, '/Users/macbook.silan.tech/Documents/GitHub/Notebook-BCC')

from stores.ai_context_store import AIContextStore, AIContext

def test_effects_preservation():
    """测试effects在state sync时能否被保留"""

    print("=" * 60)
    print("测试effects保留功能")
    print("=" * 60)

    # 1. 创建AIContextStore并添加一些effects
    store = AIContextStore()
    print("\n1. 添加本地effects...")
    store.add_effect("Output 1: Data loaded successfully")
    store.add_effect("Output 2: 2930 rows, 82 columns")

    context = store.get_context()
    print(f"   当前effects: {context.effect}")

    # 2. 模拟服务器发送的state（包含空effects）
    print("\n2. 模拟服务器state sync（包含空effects）...")
    server_state = {
        'variables': {'csv_file_path': 'test.csv'},
        'effects': {'current': [], 'history': []},  # 服务器发送的空effects
        'section_progress': {
            'current_section_id': None,
            'completed_sections': []
        }
    }

    # 3. 模拟script_store.py中的merge逻辑
    print("\n3. 执行merge（保留本地effects）...")
    merged_state = {**server_state, 'effects': context.effect}
    print(f"   merged_state['effects']: {merged_state['effects']}")

    # 4. 应用merged state
    print("\n4. 应用merged state...")
    store.set_context(merged_state)

    # 5. 验证effects是否被保留
    print("\n5. 验证effects...")
    final_context = store.get_context()
    print(f"   最终effects: {final_context.effect}")

    # 检查结果
    expected_effects = {
        'current': [
            "Output 1: Data loaded successfully",
            "Output 2: 2930 rows, 82 columns"
        ],
        'history': []
    }

    success = final_context.effect == expected_effects

    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！Effects被正确保留")
    else:
        print("❌ 测试失败！Effects未被保留")
        print(f"   期望: {expected_effects}")
        print(f"   实际: {final_context.effect}")
    print("=" * 60)

    return success

def test_backward_compatibility():
    """测试向后兼容性：支持'effect'（单数）字段名"""

    print("\n\n" + "=" * 60)
    print("测试向后兼容性（'effect'单数形式）")
    print("=" * 60)

    store = AIContextStore()

    # 使用旧的'effect'字段名
    old_format_state = {
        'variables': {'test': 'value'},
        'effect': {'current': ['Old format output'], 'history': []}
    }

    print("\n应用旧格式state...")
    store.set_context(old_format_state)

    context = store.get_context()
    print(f"最终effects: {context.effect}")

    success = context.effect == {'current': ['Old format output'], 'history': []}

    print("\n" + "=" * 60)
    if success:
        print("✅ 向后兼容性测试通过")
    else:
        print("❌ 向后兼容性测试失败")
    print("=" * 60)

    return success

if __name__ == '__main__':
    test1_pass = test_effects_preservation()
    test2_pass = test_backward_compatibility()

    print("\n\n" + "=" * 60)
    print("总体测试结果")
    print("=" * 60)
    print(f"Effects保留测试: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"向后兼容性测试: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print("=" * 60)

    sys.exit(0 if (test1_pass and test2_pass) else 1)
