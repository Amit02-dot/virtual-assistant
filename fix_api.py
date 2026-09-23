import re

MODEL = 'gemini-3.6-flash'

files = [
    'main.py',
    'core/autonomous_agent.py',
    'core/planner.py',
]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Replace all model name strings
    content = re.sub(r'gemini-[\d.]+-flash', MODEL, content)

    # 2. Replace  <client>.models.generate_content(model=..., contents=X)
    #    with      <client>.chats.create(model=MODEL).send_message(X)
    #
    # We need to capture:
    #   - optional leading whitespace
    #   - the client reference (gemini_client or self.gemini_client)
    #   - the contents value (may be multi-line list or string)
    #
    # Strategy: find the block between .generate_content( and its matching )
    # by counting parens.

    pattern = re.compile(
        r'([ \t]*)((?:self\.)?gemini_client)\.models\.generate_content\(',
        re.MULTILINE
    )

    result = []
    last_end = 0
    for m in pattern.finditer(content):
        result.append(content[last_end:m.start()])
        indent = m.group(1)
        client_ref = m.group(2)
        # Find matching closing paren
        start = m.end()  # position right after '('
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
            i += 1
        inner = content[start:i-1]  # everything between the outer parens
        last_end = i

        # Parse model= and contents= from inner
        model_match = re.search(r'model\s*=\s*["\']([^"\']+)["\']', inner)
        # contents= is everything after 'contents='
        contents_match = re.search(r'contents\s*=\s*([\s\S]+)', inner)

        if contents_match:
            contents_val = contents_match.group(1).strip().rstrip(',').strip()
            used_model = model_match.group(1) if model_match else MODEL
            replacement = f'{indent}{client_ref}.chats.create(model="{used_model}").send_message({contents_val})'
        else:
            # Fallback: leave unchanged
            replacement = m.group(0) + inner + ')'

        result.append(replacement)

    result.append(content[last_end:])
    content = ''.join(result)

    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[UPDATED] {fpath}')
    else:
        print(f'[NO CHANGE] {fpath}')

print('\nAll done! Testing a quick API call...')

# Quick sanity test
try:
    from google import genai
    client = genai.Client(api_key="YOUR_API_KEY_HERE")
    r = client.chats.create(model=MODEL).send_message("Say OK")
    print(f"API test SUCCESS: {r.text.strip()}")
except Exception as e:
    print(f"API test FAILED: {e}")
