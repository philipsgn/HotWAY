with open('frontend/src/app/demo/page.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('from "../components/', 'from "../../components/')

with open('frontend/src/app/demo/page.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated imports in demo/page.tsx successfully!')
