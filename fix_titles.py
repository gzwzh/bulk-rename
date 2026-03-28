import json
import glob
import os

zh_titles = {
    "regex": "Regex (1)",
    "replace": "Replace (3)",
    "remove": "Remove (5)",
    "add": "Add (7)",
    "auto_date": "Auto Date (8)",
    "numbering": "Numbering (10)",
    "name": "File Name (2)",
    "case": "Case (4)",
    "move_copy": "Move/Copy (6)",
    "folder_name": "Folder Name (9)",
    "extension": "Extension (11)",
    "selection": "Selection (12)",
    "new_location": "New Location (13)"
}

for f in glob.glob('locales/*.json'):
    if 'zh_CN' in f:
        continue
        
    try:
        with open(f, 'r', encoding='utf-8') as file:
            d = json.load(file)
            
        rules = d.get('main_window', {}).get('rules', {})
        changed = False
        
        for k, v in rules.items():
            if 'title' not in v and k in zh_titles:
                v['title'] = zh_titles[k]
                changed = True
                
        if changed:
            with open(f, 'w', encoding='utf-8') as file:
                json.dump(d, file, ensure_ascii=False, indent=2)
            print(f"Updated {f}")
    except Exception as e:
        print(f"Error processing {f}: {e}")
