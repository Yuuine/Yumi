#!/usr/bin/env python3
"""批量修复后端测试文件的导入问题"""

from pathlib import Path

test_dir = Path(__file__).parent / "tests"

for test_file in test_dir.glob("test_*.py"):
    print(f"处理文件: {test_file}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original_lines = lines.copy()
    new_lines = []
    
    # 添加路径设置
    path_setup_added = False
    for line in lines:
        if 'sys.path.insert' in line:
            path_setup_added = True
            break
    
    if not path_setup_added:
        # 找到合适的位置插入路径设置
        insert_pos = 0
        # 跳过开头的文档字符串
        in_docstring = False
        for i, line in enumerate(lines):
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                else:
                    in_docstring = False
                    insert_pos = i + 1
                    break
            elif not line.strip() or line.strip().startswith('#'):
                continue
            else:
                insert_pos = i
                break
        
        new_lines = lines[:insert_pos]
        new_lines.append('import sys\n')
        new_lines.append('from pathlib import Path\n')
        new_lines.append('\n')
        new_lines.append('sys.path.insert(0, str(Path(__file__).parent.parent))\n')
        new_lines.append('\n')
        new_lines.extend(lines[insert_pos:])
    else:
        new_lines = lines
    
    # 替换 from backend. 和 import backend.
    modified_lines = []
    for line in new_lines:
        line = line.replace('from backend.', 'from ')
        line = line.replace('import backend.', 'import ')
        modified_lines.append(line)
    
    if modified_lines != original_lines:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
        print(f"  ✓ 已更新")
    else:
        print(f"  - 无需修改")

print("\n✅ 所有测试文件处理完成！")

