if __name__ == "__main__":
    project_url = input("Enter project GitHub url: ")
    switch = input("Enter switch keyword: ")
    id = input("Enter container id: ")
    print("Enter all the individual tests that you want to run in fully-qualified test name format. One per line.")
    tests = []
    while True:
        try:
            test_raw = input()
            if not test_raw:
                break
            replace_idx = test_raw.rfind('.')
            test_raw_chr_list = list(test_raw)
            test_raw_chr_list[replace_idx] = '#'
            test = ''.join(test_raw_chr_list)
            tests.append(test)
        except EOFError:
            break
    if tests:
        output = f"python3 -u test-manager.py -i 'maven:3.8.3-jdk-8' {project_url} 'mvn -fae -DfailIfNoTests=false -Dtest={','.join(tests)} test' -e '{switch}' --id {id}"
        
    else:
        output = f"python3 -u test-manager.py -i 'maven:3.8.3-jdk-8' {project_url} 'mvn -fae -DfailIfNoTests=false test' -e '{switch}' --id {id}"

    print(output)