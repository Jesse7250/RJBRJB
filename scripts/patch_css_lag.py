from pathlib import Path

css = Path('frontend/src/index.css').read_text(encoding='utf-8')

replacements = [
    ("""  filter:
    drop-shadow(0 0 7px rgba(255, 247, 210, 0.75))
    drop-shadow(0 0 18px rgba(251, 191, 36, 0.74))
    drop-shadow(0 0 34px rgba(245, 158, 11, 0.38));""",
     """  filter: drop-shadow(0 0 6px rgba(251, 191, 36, 0.55));"""),

    ("""  filter:
    drop-shadow(0 0 8px rgba(255, 247, 210, 0.6))
    drop-shadow(0 0 24px rgba(251, 191, 36, 0.5));""",
     """  filter: drop-shadow(0 0 6px rgba(251, 191, 36, 0.45));"""),

    ("""  filter:
    drop-shadow(0 0 8px rgba(255, 247, 210, 0.78))
    drop-shadow(0 0 21px rgba(251, 191, 36, 0.74))
    drop-shadow(0 0 38px rgba(245, 158, 11, 0.44));""",
     """  filter: drop-shadow(0 0 6px rgba(251, 191, 36, 0.55));"""),

    ("""  filter:
    drop-shadow(0 0 8px rgba(255, 245, 196, 0.72))
    drop-shadow(0 0 18px rgba(246, 162, 26, 0.72))
    drop-shadow(0 0 32px rgba(216, 132, 0, 0.42));""",
     """  filter: drop-shadow(0 0 6px rgba(246, 162, 26, 0.55));"""),

    ("""  filter:
    drop-shadow(0 0 7px rgba(255, 245, 196, 0.58))
    drop-shadow(0 0 22px rgba(246, 162, 26, 0.64));""",
     """  filter: drop-shadow(0 0 6px rgba(246, 162, 26, 0.45));"""),

    ("""  filter:
    drop-shadow(0 0 10px rgba(255, 245, 196, 0.78))
    drop-shadow(0 0 22px rgba(246, 162, 26, 0.82))
    drop-shadow(0 0 40px rgba(216, 132, 0, 0.48));""",
     """  filter: drop-shadow(0 0 8px rgba(246, 162, 26, 0.6));"""),

    ("""  filter:
    drop-shadow(0 0 2px rgba(255, 255, 255, 0.95))
    drop-shadow(0 0 8px rgba(251, 191, 36, 0.92))
    drop-shadow(0 0 18px rgba(245, 158, 11, 0.62));""",
     """  filter: drop-shadow(0 0 4px rgba(251, 191, 36, 0.7));"""),
]

for old, new in replacements:
    if old not in css:
        print('not found:', old[:60].replace('\n', ' '))
    else:
        css = css.replace(old, new)

Path('frontend/src/index.css').write_text(css, encoding='utf-8')
print('css patched')
