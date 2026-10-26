with open('frontend/src/app/page.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('setActiveTab("planning")', 'setActiveTab("live")')

with open('frontend/src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated setActiveTab successfully!')
