"""The Sage: a wise old gentleman (grey hair, beard, monocle) in a wingback chair.

He is drawn as an SVG picture, and his face changes with his mood:
  welcome    - before any run
  pondering  - while the buddy is working
  pleased    - the supplied tests passed
  concerned  - a supplied test failed
  troubled   - something went wrong (tool, model service, timeout, limits)
"""
import base64

SKIN = "#f0c9a4"
SKIN_SHADE = "#e2ad86"
HAIR = "#e4e4e4"
HAIR_SHADE = "#b8b8b8"
BROW = "#a9a9a9"
GOLD = "#d4a64a"
INK = "#2b1d12"

# What the Sage says in his speech bubble for each mood.
SPEECH = {
    "welcome": "Ah, a visitor. Choose a program, and we shall see what the evidence tells us.",
    "pondering": "Hmm... let me consult the code and run the tests. Patience, my friend.",
    "pleased": "Splendid! The supplied tests pass. Remember: passing tests are good evidence, not proof of perfection.",
    "concerned": "A test has failed. Let us understand why before we speak of speed.",
    "troubled": "Something went awry, and it is not proof of a bug in the program. See the note below.",
}

_STYLE = """
.blink{transform-box:fill-box;transform-origin:center;animation:blink 5s infinite}
@keyframes blink{0%,95%,100%{transform:scaleY(1)}97%{transform:scaleY(.1)}}
.glint{animation:glint 3.5s infinite}
@keyframes glint{0%,70%,100%{opacity:0}80%{opacity:.95}}
.twinkle{transform-box:fill-box;transform-origin:center;animation:tw 1.6s infinite ease-in-out}
.d2{animation-delay:.5s}.d3{animation-delay:1s}
@keyframes tw{0%,100%{transform:scale(.6);opacity:.5}50%{transform:scale(1.15);opacity:1}}
.dot{animation:dot 1.8s infinite}
@keyframes dot{0%,100%{opacity:.2}50%{opacity:1}}
.drop{animation:drop 2s infinite}
@keyframes drop{0%{transform:translateY(0);opacity:1}100%{transform:translateY(12px);opacity:0}}
"""


def _star(x, y, cls=""):
    return (f'<path class="twinkle {cls}" fill="{GOLD}" d="M{x} {y-9} L{x+2} {y-2} L{x+9} {y} '
            f'L{x+2} {y+2} L{x} {y+9} L{x-2} {y+2} L{x-9} {y} L{x-2} {y-2} Z"/>')


def _brows(left, right):
    return (f'<path d="{left}" stroke="{BROW}" stroke-width="5" stroke-linecap="round" fill="none"/>'
            f'<path d="{right}" stroke="{BROW}" stroke-width="5" stroke-linecap="round" fill="none"/>')


_DOT_EYES = (f'<g class="blink"><circle cx="95" cy="95" r="3.8" fill="{INK}"/>'
             f'<circle cx="125" cy="95" r="3.8" fill="{INK}"/></g>')

# Each mood: eyes, eyebrows, mouth, and extra decorations.
_FACES = {
    "welcome": {
        "eyes": _DOT_EYES,
        "brows": _brows("M86 82 Q95 77 104 81", "M116 81 Q125 77 134 82"),
        "mouth": f'<path d="M100 129 Q110 136 120 129" stroke="{INK}" stroke-width="2.5" fill="none" stroke-linecap="round"/>',
        "extras": "",
    },
    "pondering": {
        "eyes": (f'<g class="blink"><circle cx="97" cy="91" r="3.8" fill="{INK}"/>'
                 f'<circle cx="127" cy="91" r="3.8" fill="{INK}"/></g>'),
        "brows": _brows("M86 84 Q95 82 104 84", "M116 76 Q125 69 134 75"),
        "mouth": f'<path d="M103 131 L118 129" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>',
        "extras": (
            # hand stroking the beard
            f'<path d="M150 260 Q150 200 132 176" stroke="#2f3b2a" stroke-width="16" fill="none" stroke-linecap="round"/>'
            f'<ellipse cx="128" cy="170" rx="11" ry="8" fill="{SKIN}" stroke="{SKIN_SHADE}"/>'
            # thought bubbles
            f'<circle class="dot" cx="166" cy="60" r="4" fill="#f3e6c8"/>'
            f'<circle class="dot d2" cx="180" cy="43" r="6" fill="#f3e6c8"/>'
            f'<circle class="dot d3" cx="198" cy="22" r="10" fill="#f3e6c8"/>'
        ),
    },
    "pleased": {
        "eyes": (f'<path d="M89 97 Q95 89 101 97" stroke="{INK}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
                 f'<path d="M119 97 Q125 89 131 97" stroke="{INK}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'),
        "brows": _brows("M86 79 Q95 71 104 76", "M116 76 Q125 71 134 79"),
        "mouth": f'<path d="M98 128 Q110 141 122 128" stroke="{INK}" stroke-width="2.6" fill="none" stroke-linecap="round"/>',
        "extras": (
            '<ellipse cx="86" cy="110" rx="7" ry="4" fill="#e88a7a" opacity=".45"/>'
            '<ellipse cx="134" cy="110" rx="7" ry="4" fill="#e88a7a" opacity=".45"/>'
            + _star(36, 44) + _star(190, 60, "d2") + _star(178, 22, "d3")
        ),
    },
    "concerned": {
        "eyes": _DOT_EYES,
        "brows": _brows("M86 79 L104 86", "M116 86 L134 79"),
        "mouth": f'<path d="M100 134 Q110 127 120 134" stroke="{INK}" stroke-width="2.5" fill="none" stroke-linecap="round"/>',
        "extras": (f'<text class="twinkle" x="176" y="60" font-family="Georgia,serif" font-size="38" '
                   f'font-weight="bold" fill="{GOLD}">!</text>'),
    },
    "troubled": {
        "eyes": (f'<circle cx="95" cy="95" r="6" fill="#fff"/><circle cx="95" cy="95" r="3" fill="{INK}"/>'
                 f'<circle cx="125" cy="95" r="6" fill="#fff"/><circle cx="125" cy="95" r="3" fill="{INK}"/>'),
        "brows": _brows("M86 85 L104 78", "M116 78 L134 85"),
        "mouth": f'<ellipse cx="110" cy="131" rx="4" ry="5" fill="{INK}"/>',
        "extras": '<path class="drop" d="M152 62 Q145 73 152 78 Q159 73 152 62 Z" fill="#9fd3ff"/>',
    },
}


def sage_svg(mood):
    face = _FACES.get(mood, _FACES["welcome"])
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 260">'
        f'<style>{_STYLE}</style>'
        # wingback armchair
        '<path d="M40 260 L40 90 Q40 30 110 28 Q180 30 180 90 L180 260 Z" fill="#5c1d1d" stroke="#3a1010" stroke-width="3"/>'
        '<g fill="#3f1212"><circle cx="70" cy="68" r="3"/><circle cx="110" cy="50" r="3"/>'
        '<circle cx="150" cy="68" r="3"/><circle cx="60" cy="120" r="3"/><circle cx="160" cy="120" r="3"/></g>'
        '<path d="M26 260 L26 145 Q26 112 54 110 L54 260 Z" fill="#6b2222" stroke="#3a1010" stroke-width="2"/>'
        '<path d="M194 260 L194 145 Q194 112 166 110 L166 260 Z" fill="#6b2222" stroke="#3a1010" stroke-width="2"/>'
        # smoking jacket, lapels, shirt
        '<path d="M50 260 Q52 182 110 168 Q168 182 170 260 Z" fill="#2f3b2a"/>'
        '<path d="M110 172 L88 260 L76 260 Q74 200 96 174 Z" fill="#7a2e1d"/>'
        '<path d="M110 172 L132 260 L144 260 Q146 200 124 174 Z" fill="#7a2e1d"/>'
        '<path d="M98 172 L110 215 L122 172 Z" fill="#f4ecd8"/>'
        # ears and head
        f'<ellipse cx="70" cy="100" rx="8" ry="12" fill="{SKIN_SHADE}"/>'
        f'<ellipse cx="150" cy="100" rx="8" ry="12" fill="{SKIN_SHADE}"/>'
        f'<ellipse cx="110" cy="96" rx="40" ry="45" fill="{SKIN}"/>'
        # long grey beard
        f'<path d="M72 108 Q70 162 110 196 Q150 162 148 108 Q138 128 110 126 Q82 128 72 108 Z" '
        f'fill="{HAIR}" stroke="{HAIR_SHADE}" stroke-width="1.5"/>'
        f'<path d="M96 150 Q101 166 105 182 M120 150 Q117 166 113 184 M84 132 Q88 148 94 160 '
        f'M136 132 Q132 148 126 160" stroke="{HAIR_SHADE}" stroke-width="1.4" fill="none"/>'
        # grey hair tufts on the sides, shiny bald top
        f'<g fill="{HAIR}" stroke="{HAIR_SHADE}" stroke-width="1"><circle cx="72" cy="78" r="13"/>'
        f'<circle cx="66" cy="94" r="11"/><circle cx="148" cy="78" r="13"/><circle cx="154" cy="94" r="11"/></g>'
        '<ellipse cx="97" cy="62" rx="12" ry="6" fill="#fff" opacity=".45"/>'
        # nose and moustache
        f'<ellipse cx="110" cy="109" rx="7" ry="8" fill="{SKIN_SHADE}"/>'
        f'<path d="M110 117 Q96 112 84 123 Q96 121 110 123 Q124 121 136 123 Q124 112 110 117 Z" '
        f'fill="{HAIR}" stroke="{HAIR_SHADE}"/>'
        # mood: mouth, eyes, brows
        + face["mouth"] + face["eyes"] + face["brows"] +
        # monocle on his right eye, with a glint and a gold chain
        f'<circle cx="125" cy="95" r="13" fill="#cfe6ff" fill-opacity=".22" stroke="{GOLD}" stroke-width="3"/>'
        '<path class="glint" d="M117 89 L122 85" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>'
        f'<path d="M137 101 Q152 140 140 184" stroke="{GOLD}" stroke-width="1.6" fill="none" stroke-dasharray="3 2"/>'
        + face["extras"] +
        '</svg>'
    )


def sage_html(mood):
    """The Sage picture plus his speech bubble, as one line of HTML."""
    b64 = base64.b64encode(sage_svg(mood).encode("utf-8")).decode("ascii")
    line = SPEECH.get(mood, SPEECH["welcome"])
    return (f'<div class="sage-wrap"><div class="speech"><span class="who">The Sage says:</span>{line}</div>'
            f'<img class="sage-img" src="data:image/svg+xml;base64,{b64}" alt="The Sage, looking {mood}"/></div>')
