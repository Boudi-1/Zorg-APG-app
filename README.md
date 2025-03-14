# Applicatie Dashboard

Een overkoepelende Flask-applicatie die drie bestaande Flask-applicaties integreert in één dashboard.

## Projectstructuur

```
Applicatie_Dagvaardingen/
│
├── main.py                 # Hoofdapplicatie
├── requirements.txt        # Dependencies
├── README.md               # Dit bestand
│
├── static/                 # Statische bestanden voor de hoofdapplicatie
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
│
├── templates/              # Templates voor de hoofdapplicatie
│   ├── layout.html
│   └── index.html
│
├── app1/                   # Eerste Flask-applicatie (ongewijzigd)
│   ├── main.py             # Hoofdbestand van app1
│   ├── process.py          # Verwerkingslogica van app1
│   ├── index.html          # Template van app1
│   ├── success.html        # Template van app1
│   └── ...
│
├── app2/                   # Tweede Flask-applicatie (ongewijzigd)
│   ├── app.py              # Hoofdbestand van app2
│   ├── index.html          # Template van app2
│   ├── success.html        # Template van app2
│   └── ...
│
└── app3/                   # Derde Flask-applicatie (ongewijzigd)
    ├── deel_3.py           # Hoofdbestand van app3
    ├── main.py             # Ondersteunend bestand van app3
    ├── mapping.py          # Ondersteunend bestand van app3
    ├── placeholders.py     # Ondersteunend bestand van app3
    ├── index.html          # Template van app3
    ├── success.html        # Template van app3
    └── ...
```

## Installatie

1. Maak een virtuele omgeving aan:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

2. Installeer de benodigde dependencies:

```bash
pip install -r requirements.txt
```

## Gebruik

Start de applicatie met:

```bash
python main.py
```

Open vervolgens je browser en ga naar `http://localhost:5000` om het dashboard te zien.

## Hoe het werkt

De hoofdapplicatie (main.py) integreert de drie bestaande Flask-applicaties als Blueprints:

1. **App1**: Verwerkt documenten en dagvaardingen
2. **App2**: Analyseert en visualiseert data
3. **App3**: Beheert en organiseert tabellen en databases

Elke app behoudt zijn eigen functionaliteit, routes, templates en statische bestanden. De hoofdapplicatie biedt een dashboard met navigatie naar elk van de drie apps.

## Belangrijke opmerkingen

- Elke app heeft zijn eigen uploads en output mappen binnen zijn eigen directory
- De code van de drie bestaande apps is niet gewijzigd
- Alle routes van de apps zijn beschikbaar onder hun respectievelijke prefixes (/app1, /app2, /app3)
- Je kunt altijd terugkeren naar het dashboard via de navigatiebalk of de "Terug naar Dashboard" knop

## Troubleshooting

Als je problemen ondervindt met het starten van de applicatie:

1. Controleer of alle dependencies correct zijn geïnstalleerd
2. Controleer of de mappenstructuur correct is
3. Controleer of de virtuele omgeving is geactiveerd
4. Controleer de console-output voor eventuele foutmeldingen #   Z o r g - A P G - a p p  
 