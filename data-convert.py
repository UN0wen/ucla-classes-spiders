import json

with open("data/deptclasses.json", "r") as f:
    data = json.load(f)
    dept_code = []
    code_name_meta = []
    for dept in data:
        dept_name = dept['department']
        classes = dept['classes']
        for cl in classes:
            code = cl['class_id']
            name = cl['class_name']
            meta = cl['class_meta']
            dept_code.append(dict(department=dept_name, class_id=code))
            code_name_meta.append(dict(class_id=code, class_name=name, class_meta=meta))
    
    with open("data/dept_code.json", "w") as f2:
        f2.write(json.dumps(dept_code, indent=2))

    with open("data/code_name_meta.json", "w") as f2:
        f2.write(json.dumps(code_name_meta, indent=2))    