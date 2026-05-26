import json

with open("config/config.json", "r") as f:
    content = f.read()

# Fix the accidental removal
content = content.replace('"name": "Never ",\n    }\n  ]\n}', '"name": "Never ",\n      "start_from_date": "2026-04-01"\n    }\n  ]\n}')

try:
    config = json.loads(content)
except Exception as e:
    print(f"Error parsing JSON: {e}")
    exit(1)

new_programs = [
    "Alexei Sayle's Imaginary Sandwich Bar",
    "Simon Evans Goes to Market",
    "The Climate Tipping Points",
    "A Thorough Examination with Drs Chris and Xand",
    "Think with Pinker",
    "Conversations from a Long Marriage",
    "The Now Show",
    "BBC Inside Science",
    "It's a Fair Cop",
    "Mark Steel's in Town",
    "Dead Ringers",
    "You're Dead to Me",
    "More or Less",
    "The News Quiz",
    "The Unbelievable Truth",
    "Tom Wrigglesworth's Hang-Ups",
    "My First Planet",
    "John Finnemore's Souvenir Programme",
    "Cabin Pressure"
]

existing_names = {p['name'] for p in config.get('programmes', [])}

for prog in new_programs:
    if prog not in existing_names:
        config['programmes'].append({
            "name": prog,
            "start_from_date": "2026-04-01"
        })

with open("config/config.json", "w") as f:
    json.dump(config, f, indent=2)

print("Config updated successfully")
