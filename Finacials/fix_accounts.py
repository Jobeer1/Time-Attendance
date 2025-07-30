import re
input_path = 'reports 2_2.csv'
output_path = 'reports 2_2_accounts_fixed.csv'

# Account number rules
rules = [
    (re.compile(r'^(N)(\d{6,})'), 'N'),
    (re.compile(r'^(E)(\d{6,})'), 'E'),
    (re.compile(r'^(U)(\d{6,})'), 'U'),
    (re.compile(r'^(I)(\d{7,})'), 'I'),
    (re.compile(r'^(MT)(\d{5,})'), 'MT'),
]

# Fallback: try to infer prefix from number
fallbacks = [
    (re.compile(r'^(003\d{5,})'), 'N'),
    (re.compile(r'^(027\d{5,})'), 'E'),
    (re.compile(r'^(009\d{5,})'), 'U'),
    (re.compile(r'^(0001\d{4,})'), 'I'),
    (re.compile(r'^(01\d{4,})'), 'MT'),
]

def fix_account(acc):
    acc = acc.strip()
    for rule, prefix in rules:
        if rule.match(acc):
            return acc
    for fb, prefix in fallbacks:
        m = fb.match(acc)
        if m:
            return prefix + m.group(1)
    # If only digits, guess by length
    if acc.isdigit():
        if len(acc) == 8 and acc.startswith('1'):
            return 'N' + acc
        if len(acc) == 7 and acc.startswith('0'):
            return 'N' + acc
        if len(acc) == 7 and acc.startswith('9'):
            return 'U' + acc
        if len(acc) == 7 and acc.startswith('2'):
            return 'E' + acc
        if len(acc) == 8 and acc.startswith('0'):
            return 'E' + acc
    # If already has a prefix but wrong, try to fix
    m = re.match(r'^(\d+)', acc)
    if m:
        num = m.group(1)
        if len(num) == 7 and num.startswith('0'):
            return 'N' + num
    return acc

with open(input_path, encoding='utf-8') as fin, open(output_path, 'w', encoding='utf-8') as fout:
    for i, line in enumerate(fin):
        if i == 0 or not line.strip() or line.startswith('ACCOUNT NAME'):
            fout.write(line)
            continue
        parts = line.split('|')
        if len(parts) < 2:
            fout.write(line)
            continue
        acc = parts[0].strip()
        fixed = fix_account(acc)
        parts[0] = fixed
        fout.write('|'.join([p.strip() for p in parts]))
        if not line.endswith('\n'):
            fout.write('\n')
