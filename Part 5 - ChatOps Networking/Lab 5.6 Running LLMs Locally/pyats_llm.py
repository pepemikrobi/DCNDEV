from pyats.topology import loader
from ollama import Client
import sys

tb = loader.load('../pyats/testbed.yaml')
device = tb.devices['POD5_R1']
print('[pyats] Connecting to device...')
device.connect()
print('[pyats] Connected.')

client = Client(host='http://localhost:11434')
try:
    client.list()
    print('[ok] Connected to Ollama.')
except Exception as e:
    print(f'[error] Cannot connect to Ollama at localhost:11434: {e}')
    sys.exit(1)
messages = [{'role': 'system', 'content': 
    'You are a network engineer. When asked to check something, '
    'I will provide pyATS parsed output. Provide a precise answer based on the data, and do not make assumptions beyond it. '}]

parsers = {
    'interfaces': 'show ip interface brief',
    'bgp': 'show bgp all summary',
    'ospf': 'show ip ospf neighbor',
    'routes': 'show ip route',
}

while True:
    query = input('\nWhat do you want to check? (type "exit" to quit) > ')
    if query.strip().lower() in ('exit', 'quit'):
        break
    
    # Collect only parsers relevant to the query (fall back to all if none match)
    query_lower = query.lower()
    selected = {name: cmd for name, cmd in parsers.items() if name in query_lower}
    if not selected:
        selected = parsers

    context = {}
    for name, cmd in selected.items():
        print(f'[pyats] Running: {cmd}')
        try:
            context[name] = device.parse(cmd)
            print(f'[pyats] Done: {cmd}')
        except Exception as e:
            print(f'[warning] Could not parse "{cmd}": {e}')

    messages.append({'role': 'user', 'content': 
        f'Query: {query}\n\nDevice data:\n{context}'})
    
    print('\n[ollama] Thinking...\n')
    answer = ''
    in_thinking = False
    for chunk in client.chat(model='qwen3:14b', messages=messages, stream=True):
        thinking = getattr(chunk.message, 'thinking', None)
        content = chunk.message.content
        if thinking:
            if not in_thinking:
                print('[thinking] ', end='', flush=True)
                in_thinking = True
            print(thinking, end='', flush=True)
        if content:
            if in_thinking:
                print('\n[answer] ', end='', flush=True)
                in_thinking = False
            print(content, end='', flush=True)
            answer += content
    print()
    messages.append({'role': 'assistant', 'content': answer})
