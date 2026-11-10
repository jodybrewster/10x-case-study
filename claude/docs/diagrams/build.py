"""Draw the documentation diagrams as inline SVG and inject them into current-system.html.

    python3 docs/diagrams/build.py          (run from claude/)

Each diagram is laid out by hand on a grid. The script writes one .svg per diagram
next to itself and replaces the matching <figure data-svg="name"> body in the page.
The sequence diagram stays in Mermaid.

Visual language: filled boxes coloured by what they are (system record, code in the
repo, described flow with no code, risk), arrows coloured the same way, bold title line
with muted detail lines, a legend under each figure.
"""

import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent

INK, MUTED, GREY = "#202427", "#62686d", "#737373"
KINDS = {
    #            fill       stroke     label colour
    "system": ("#ffffff", "#202427", "#202427"),
    "code":   ("#f3f3f3", "#737373", "#62686d"),
    "ext":    ("#fff3dc", "#b97818", "#94550b"),
    "risk":   ("#fbeaea", "#c00000", "#980000"),
    "step":   ("#ffffff", GREY, MUTED),
    "person": ("#f3f3f3", GREY, INK),
    "new":    ("#f3f3f3", "#202427", "#202427"),
}
LEGEND_WORDS = {
    "system": "System record", "code": "Code in the repo", "ext": "Described, no code in the repo",
    "risk": "Where it fails", "step": "Step or decision", "person": "Person",
    "new": "New or changed component",
}
TITLE, DETAIL, MONO = 15, 12.5, 11.5
LINE = 17


def esc(t):
    return html.escape(t, quote=True)


class Diagram:
    def __init__(self, name, w, h, label, legend=(), page="current-system.html"):
        self.name, self.w, self.h, self.label, self.legend, self.page = name, w, h, label, legend, page
        self.nodes = {}
        self.parts = []

    # ------------------------------------------------------------ text
    def _text(self, cx, cy, lines, mono=(), anchor="middle", colour=None, title=True, size=None, halo=False, weight=None):
        n = len(lines)
        y0 = cy - (n - 1) * LINE / 2
        style = ' style="paint-order:stroke;stroke:#ffffff;stroke-width:4px;stroke-linejoin:round"' if halo else ""
        out = [f'<text x="{cx}" y="{y0}" text-anchor="{anchor}" dominant-baseline="middle"{style}>']
        for i, line in enumerate(lines):
            attrs = f' x="{cx}" dy="{LINE if i else 0}"'
            if i in mono:
                attrs += f' font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="{MONO}" fill="{MUTED}"'
            elif i == 0 and title:
                attrs += f' font-size="{size or TITLE}" font-weight="{weight or 700}" fill="{colour or INK}"'
            else:
                attrs += f' font-size="{size or DETAIL}" fill="{colour or MUTED}"' + (f' font-weight="{weight}"' if weight else "")
            out.append(f"<tspan{attrs}>{esc(line)}</tspan>")
        out.append("</text>")
        return "".join(out)

    # ------------------------------------------------------------ shapes
    def box(self, nid, x, y, w, h, lines, kind="step", mono=(), dashed=False, bad=False):
        if bad:
            kind = "risk"
        fill, stroke, _ = KINDS[kind]
        self.nodes[nid] = (x, y, w, h)
        dash = ' stroke-dasharray="6 5"' if dashed else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"{dash}/>')
        self.parts.append(self._text(x + w / 2, y + h / 2, lines, mono=mono))

    def pill(self, nid, x, y, w, h, lines):
        fill, stroke, _ = KINDS["person"]
        self.nodes[nid] = (x, y, w, h)
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        self.parts.append(self._text(x + w / 2, y + h / 2, lines, size=13.5, weight=600))

    def diamond(self, nid, cx, cy, w, h, lines, mono=(), bad=False):
        fill, stroke, _ = KINDS["risk" if bad else "step"]
        self.nodes[nid] = (cx - w / 2, cy - h / 2, w, h)
        pts = f"{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}"
        self.parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>')
        self.parts.append(self._text(cx, cy, lines, mono=mono, size=13.5))

    def cylinder(self, nid, x, y, w, h, lines, kind="system"):
        fill, stroke, _ = KINDS[kind]
        self.nodes[nid] = (x, y, w, h)
        ry = 9
        self.parts.append(f'<path d="M{x},{y + ry} v{h - 2 * ry} a{w / 2},{ry} 0 0 0 {w},0 v-{h - 2 * ry}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        self.parts.append(f'<ellipse cx="{x + w / 2}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        self.parts.append(self._text(x + w / 2, y + ry + (h - ry) / 2, lines))

    def zone(self, x, y, w, h, title, red=False):
        stroke = f'stroke="{KINDS["risk"][1]}" stroke-width="1.5"' if red else f'stroke="{GREY}" stroke-opacity="0.6"'
        self.parts.insert(0, f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" {stroke} stroke-dasharray="6 5"/>')
        self.parts.insert(1, f'<text x="{x + 14}" y="{y + 18}" font-size="12.5" font-weight="700" fill="{KINDS["risk"][1] if red else MUTED}">{esc(title)}</text>')

    def entity(self, nid, x, y, w, title, rows):
        """ER entity: title bar plus one row per attribute, rows are (name, key, note)."""
        th, rh = 26, 19
        h = th + rh * len(rows)
        self.nodes[nid] = (x, y, w, h)
        fill, stroke, _ = KINDS["system"]
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#ffffff" stroke="{stroke}" stroke-width="1.5"/>')
        self.parts.append(f'<path d="M{x},{y + th} V{y + 6} a6,6 0 0 1 6,-6 H{x + w - 6} a6,6 0 0 1 6,6 V{y + th} z" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        self.parts.append(f'<text x="{x + w / 2}" y="{y + th / 2 + 1}" text-anchor="middle" dominant-baseline="middle" font-size="13.5" font-weight="700" fill="{INK}">{esc(title)}</text>')
        for i, (name, key, note) in enumerate(rows):
            cy = y + th + rh * i + rh / 2
            self.parts.append(f'<text x="{x + 10}" y="{cy}" font-size="12" dominant-baseline="middle" fill="{INK}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace">{esc(name)}</text>')
            if key:
                self.parts.append(f'<text x="{x + w - 10}" y="{cy}" font-size="11" dominant-baseline="middle" text-anchor="end" fill="{KINDS["system"][2]}" font-weight="700">{esc(key)}</text>')
            if note:
                self.parts.append(f'<text x="{x + w - (38 if key else 10)}" y="{cy}" font-size="11" dominant-baseline="middle" text-anchor="end" fill="{MUTED}">{esc(note)}</text>')

    # ------------------------------------------------------------ anchors
    def T(self, n, dx=0): x, y, w, h = self.nodes[n]; return (x + w / 2 + dx, y)
    def B(self, n, dx=0): x, y, w, h = self.nodes[n]; return (x + w / 2 + dx, y + h)
    def L(self, n, dy=0): x, y, w, h = self.nodes[n]; return (x, y + h / 2 + dy)
    def R(self, n, dy=0): x, y, w, h = self.nodes[n]; return (x + w, y + h / 2 + dy)

    # ------------------------------------------------------------ edges
    def edge(self, pts, label=None, at=None, kind=None, dashed=False, arrow=True, dx=0, dy=-10, anchor="middle", ends=None):
        """pts: polyline points. Dashed edges default to the 'ext' (described) colour."""
        if kind is None:
            kind = "ext" if dashed else "step"
        stroke = {"step": GREY}.get(kind, KINDS[kind][1])
        label_colour = {"step": MUTED}.get(kind, KINDS[kind][2])
        width = 2 if kind == "step" else 2.4
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        dash = ' stroke-dasharray="7 7"' if dashed else ""
        mk = f' marker-end="url(#arrow-{kind})"' if arrow else ""
        self.parts.append(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"{dash}{mk}/>')
        if label:
            lines = label if isinstance(label, list) else [label]
            if at is None:
                i = (len(pts) - 1) // 2
                (x1, y1), (x2, y2) = pts[i], pts[i + 1]
                px, py = (x1 + x2) / 2, (y1 + y2) / 2
            else:
                px, py = pts[at] if isinstance(at, int) else at
            self.parts.append(self._text(px + dx, py + dy - (len(lines) - 1) * LINE / 2, lines, size=11.5, halo=True,
                                         anchor=anchor, colour=label_colour, title=False, weight=600))
        if ends:
            for (x, y), txt, ax in ends:
                self.parts.append(self._text(x, y, [txt], size=11, halo=True, anchor=ax, colour=MUTED, title=False))

    def svg(self):
        body = "\n".join(self.parts)
        markers = "".join(
            f'<marker id="arrow-{k}" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">'
            f'<path d="M0,0 L0,6 L9,3 z" fill="{GREY if k == "step" else KINDS[k][1]}"/></marker>'
            for k in ("step", "system", "code", "ext", "risk", "new"))
        return (f'<svg viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(self.label)}" '
                f'xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;display:block;margin:0 auto;font-family:inherit">\n'
                f'<defs>{markers}</defs>\n{body}\n</svg>')

    def legend_html(self):
        if not self.legend:
            return ""
        return '<div class="legend">' + "".join(f'<span class="{k}">{esc(LEGEND_WORDS[k])}</span>' for k in self.legend) + "</div>"


# ============================================================ 1. context
def context():
    d = Diagram("context", 1040, 420, "Orders and registrations flow through legacy-sync into the CRM; the portal, lab and EHR exchange records outside the repo",
                legend=("system", "code", "ext"))
    d.box("EC", 20, 40, 190, 72, ["E-commerce", "533 customers", "905 orders, 547 kits"], kind="system")
    d.box("PORTAL", 20, 180, 190, 60, ["Member portal", "433 kit registrations"], kind="system")
    d.box("LAB", 20, 330, 190, 50, ["Lab partner", "406 results"], kind="ext")
    d.box("OS", 330, 50, 180, 56, ["Order sync", "sync/order_sync.py"], kind="code", mono=(1,))
    d.box("REG", 330, 180, 180, 56, ["Kit registration", "registration/register.py"], kind="code", mono=(1,))
    d.zone(300, 20, 240, 240, "legacy-sync")
    d.box("CRM", 600, 90, 180, 72, ["CRM", "689 accounts", "905 opportunities"], kind="system")
    d.box("MKT", 870, 90, 160, 72, ["Marketing nurture", "marketing/stage.py"], kind="ext", mono=(1,))
    d.box("EHR", 600, 300, 180, 70, ["EHR", "339 charts"], kind="ext")
    d.edge([d.R("EC"), d.L("OS")], "each order", kind="code")
    d.edge([d.R("OS"), (580, 78), (580, 110), d.L("CRM", -16)], ["find or create account", "overwrite email and phone", "create opportunity"], at=(640, 52), dy=0, kind="code")
    d.edge([d.R("PORTAL"), d.L("REG")], "each registration", kind="code")
    d.edge([d.R("REG"), (580, 208), (580, 142), d.L("CRM", 16)], ["find or create account", "move gift opportunity"], at=(655, 200), dy=0, kind="code")
    d.edge([d.B("PORTAL"), (115, 290), (580, 290), (580, 312), d.L("EHR", -23)], "chart from name and birthdate", at=(360, 290), dashed=True)
    d.edge([d.R("LAB"), d.L("EHR", 20)], "result by kit barcode", at=(400, 355), dashed=True)
    d.edge([d.T("EHR", 40), (730, 270), (250, 270), (250, 225), d.R("PORTAL", 15)], "results shown to the customer", at=(500, 270), dashed=True)
    d.edge([d.R("CRM"), d.L("MKT")], ["stage per", "account"], dashed=True, dy=-20)
    return d


# ============================================================ 2. ER
def er():
    d = Diagram("er", 1040, 660, "How the eight data files relate: the kit barcode links e-commerce, portal and lab; the sync writes the only link between e-commerce and CRM")
    d.entity("CUST", 40, 30, 250, "ecom_customers", [("customer_id", "PK", ""), ("email", "", "unique"), ("first_name, last_name", "", ""), ("phone", "", "four formats"), ("default_zip", "", "")])
    d.entity("ORD", 40, 240, 250, "ecom_orders", [("order_id", "PK", ""), ("customer_id", "FK", ""), ("order_email", "", ""), ("ship_name, ship_zip", "", ""), ("is_gift", "", "30 true")])
    d.entity("KIT", 40, 460, 250, "kits", [("kit_barcode", "PK", ""), ("order_id", "FK", "one kit per order")])
    d.entity("ACC", 400, 30, 260, "crm_accounts", [("account_id", "PK", ""), ("primary_email", "", "58 shared"), ("birthdate", "", "241 unusable"), ("mailing_zip", "", ""), ("ecom_customer_id", "", "169 blank"), ("owner_active", "", "54 false"), ("sms_opt_out, do_not_call", "", "")])
    d.entity("OPP", 400, 260, 260, "crm_opportunities", [("opportunity_id", "PK", ""), ("account_id", "FK", ""), ("ecom_order_id", "FK", ""), ("gift_recipient_account_id", "", "always blank")])
    d.entity("REG", 400, 460, 260, "portal_registrations", [("registration_id", "PK", ""), ("kit_barcode", "FK", ""), ("email", "", "341 distinct"), ("first_name, last_name", "", ""), ("birthdate", "", "")])
    d.entity("PAT", 770, 30, 240, "ehr_patients", [("chart_id", "PK", ""), ("first_name, last_name", "", ""), ("birthdate", "", ""), ("sex", "", "")])
    d.entity("RES", 770, 260, 240, "lab_results", [("result_id", "PK", ""), ("kit_barcode", "FK", ""), ("chart_id", "FK", ""), ("patient_birthdate", "", "")])
    d.edge([d.B("CUST"), d.T("ORD")], "customer_id", arrow=False, dx=10, dy=0, anchor="start",
           ends=[((155, 158), "1", "start"), ((155, 232), "many", "start")])
    d.edge([d.B("ORD"), d.T("KIT")], "order_id", arrow=False, dx=10, dy=0, anchor="start",
           ends=[((155, 355), "1", "start"), ((155, 452), "0 or 1", "start")])
    d.edge([d.R("CUST", -40), (345, 85), (345, 112), d.L("ACC", 10)], ["ecom_customer_id", "written by the sync"], at=(345, 112), dy=26, arrow=False, kind="code",
           ends=[((300, 73), "0 or 1", "start"), ((392, 100), "many", "end")])
    d.edge([d.B("ACC"), d.T("OPP")], "account_id", arrow=False, dx=10, dy=0, anchor="start",
           ends=[((540, 203), "1", "start"), ((540, 252), "many", "start")])
    d.edge([d.R("ORD", -20), (345, 305), (345, 335), d.L("OPP", 0)], "ecom_order_id", at=(345, 320), dy=0, arrow=False,
           ends=[((300, 293), "1", "start"), ((392, 347), "1", "end")])
    d.edge([d.R("KIT", -8), (345, 496), (345, 515), d.L("REG", 0)], "kit_barcode", at=(345, 506), dy=0, arrow=False,
           ends=[((300, 484), "1", "start"), ((392, 528), "0 or 1", "end")])
    d.edge([d.B("KIT"), (165, 610), (740, 610), (740, 340), d.L("RES", 0)], "kit_barcode", at=(450, 610), dy=-10, arrow=False,
           ends=[((175, 560), "1", "start"), ((760, 328), "0 or 1", "end")])
    d.edge([d.B("PAT"), d.T("RES")], "chart_id", arrow=False, dx=10, dy=0, anchor="start",
           ends=[((900, 125), "1", "start"), ((900, 252), "many", "start")])
    return d


# ============================================================ 3. order sync
def order_sync():
    d = Diagram("order-sync", 840, 830, "Order sync: lookup by e-commerce ID, then email, then surname and zip, then create; every path overwrites the account's email",
                legend=("system", "step", "risk"))
    d.box("A", 300, 20, 240, 50, ["Order arrives", "replay.py:29-30"], kind="system", mono=(1,))
    d.diamond("B", 420, 150, 270, 96, ["Account with this", "ecom_customer_id?", "order_sync.py:12"], mono=(2,))
    d.diamond("C", 420, 300, 270, 96, ["Account with this email,", "primary or secondary?", "order_sync.py:16"], mono=(2,))
    d.diamond("D", 420, 450, 290, 100, ["Account with the shipment's", "surname and zip?", "order_sync.py:20-24"], bad=True, mono=(2,))
    d.box("S", 120, 560, 230, 64, ["Stamp ecom_customer_id", "if the account has none", "order_sync.py:39-40"], mono=(2,))
    d.box("N", 490, 560, 250, 64, ["Create account, birthdate blank", "duplicate rule applies, not caught", "order_sync.py:32-38"], mono=(2,))
    d.box("U", 280, 670, 300, 70, ["Overwrite primary_email and phone", "with the order's values", "order_sync.py:42"], bad=True, mono=(2,))
    d.box("O", 280, 780, 300, 44, ["Create opportunity on that account", "replay.py:31-33"], kind="system", mono=(1,))
    d.edge([d.B("A"), d.T("B")])
    d.edge([d.B("B"), d.T("C")], "no", dx=12, dy=0, anchor="start")
    d.edge([d.B("C"), d.T("D")], "no", dx=12, dy=0, anchor="start")
    d.edge([d.L("B"), (60, 150), (60, 705), d.L("U")], "yes, 772 orders", at=(60, 420), dx=8, dy=0, anchor="start")
    d.edge([d.L("C"), (200, 300), (200, 560)], "yes, 24", at=(200, 430), dx=8, dy=0, anchor="start")
    d.edge([d.L("D"), (235, 450), (235, 560)], "yes, 43", at=(235, 505), dx=8, dy=0, anchor="start", kind="risk")
    d.edge([d.R("D"), (615, 450), (615, 560)], "no, 66", at=(615, 505), dx=8, dy=0, anchor="start")
    d.edge([d.B("S"), (235, 705), d.L("U")])
    d.edge([d.B("N"), (615, 705), d.R("U")])
    d.edge([d.B("U"), d.T("O")])
    return d


# ============================================================ 4. registration
def registration():
    d = Diagram("registration", 1000, 1060, "Kit registration: find the account by email, check the person, else create and face the duplicate rule, then move a gift purchase",
                legend=("system", "step", "risk"))
    d.box("A", 300, 20, 220, 44, ["Registration arrives", "replay.py:36-38"], kind="system", mono=(1,))
    d.box("B", 290, 100, 240, 50, ["Find the kit's order and opportunity", "register.py:25-26"], mono=(1,))
    d.diamond("C", 410, 235, 260, 90, ["Account with the", "registrant's email?", "register.py:28"], mono=(2,))
    d.diamond("D", 180, 400, 330, 112, ["Same person?", "surname, plus birthdate", "when the account has one", "register.py:15-19"], mono=(3,))
    d.box("E", 560, 360, 250, 72, ["Create an account from the", "registration and the order's", "shipping address", "register.py:36-41"], mono=(3,))
    d.diamond("F", 685, 540, 280, 100, ["CRM duplicate rule: same", "first name, last name, zip?", "client.py:38-40"], mono=(2,))
    d.box("X1", 15, 560, 200, 60, ["IdentityConflict", "11 rejected", "register.py:32-33"], bad=True, mono=(2,))
    d.box("X2", 770, 660, 210, 60, ["RegistrationBlocked", "20 rejected as duplicates", "register.py:42-43"], bad=True, mono=(2,))
    d.diamond("G", 410, 690, 270, 90, ["Gift order sitting on", "a different account?", "register.py:45"], mono=(2,))
    d.diamond("H", 410, 840, 250, 86, ["Recipient's account", "owner active?", "client.py:59"], mono=(2,))
    d.box("X3", 60, 920, 200, 60, ["InactiveOwner", "1 failed", "client.py:60"], bad=True, mono=(2,))
    d.box("M", 580, 920, 220, 60, ["Move the opportunity", "to the recipient", "client.py:61"], mono=(2,))
    d.box("OK", 300, 1000, 220, 44, ["Accepted, 401"], kind="system")
    d.edge([d.B("A"), d.T("B")])
    d.edge([d.B("B"), d.T("C")])
    d.edge([d.L("C"), (180, 235), d.T("D")], "yes", at=(180, 300), dx=8, dy=0, anchor="start")
    d.edge([d.R("C"), (685, 235), d.T("E")], "no", at=(685, 300), dx=8, dy=0, anchor="start")
    d.edge([d.B("D", -50), d.T("X1", 0)], "no", at=(130, 520), dx=-8, dy=0, anchor="end", kind="risk")
    d.edge([d.B("D", 50), (230, 630), (410, 630), d.T("G")], "yes, 391", at=(230, 580), dx=8, dy=0, anchor="start")
    d.edge([d.B("E"), d.T("F")])
    d.edge([d.R("F"), (875, 590), d.T("X2")], "yes", at=(875, 625), dx=8, dy=0, anchor="start", kind="risk")
    d.edge([d.B("F"), (685, 630), (410, 630)], "no, 10", at=(685, 612), dx=8, dy=0, anchor="start", arrow=False)
    d.edge([d.R("G"), (600, 690), (600, 1022), d.R("OK")], "no", at=(600, 760), dx=8, dy=0, anchor="start")
    d.edge([d.B("G"), d.T("H")], "yes", dx=12, dy=0, anchor="start")
    d.edge([d.L("H"), (160, 840), d.T("X3")], "no", at=(160, 880), dx=8, dy=0, anchor="start", kind="risk")
    d.edge([d.R("H"), (690, 840), d.T("M")], "yes, 12", at=(690, 880), dx=8, dy=0, anchor="start")
    d.edge([d.B("M"), (690, 990), (470, 990), d.T("OK", 60)])
    return d


# ============================================================ 5. causal chain
def chain():
    d = Diagram("chain", 1000, 900, "The six symptoms as one causal chain from the June hotfix, plus the separate merge path for consent",
                legend=("step", "risk"))
    d.box("H", 40, 20, 220, 60, ["June hotfix", "match on surname and zip", "order_sync.py:20-24"], mono=(2,))
    d.box("S1", 40, 130, 220, 60, ["Symptom 1", "Purchase lands on", "a relative's account"], bad=True)
    d.box("OW", 40, 240, 220, 60, ["Every order overwrites", "the account's email", "order_sync.py:42"], mono=(2,))
    d.box("S2", 40, 350, 220, 50, ["Symptom 2", "CRM emails change"], bad=True)
    d.box("LOOK", 40, 450, 220, 60, ["Registration looks up", "by email only", "register.py:28"], mono=(2,))
    d.box("S3", 40, 580, 220, 60, ["Symptom 3", "Duplicate rule rejects", "the new account"], bad=True)
    d.box("IC", 310, 580, 190, 50, ["Identity conflict", "same email, other birthdate"])
    d.box("GIFT", 540, 450, 200, 50, ["Gift recipient registers"])
    d.box("IO", 540, 540, 200, 60, ["Recipient's account has", "an inactive owner", "client.py:59-60"], mono=(2,))
    d.box("S4", 540, 650, 200, 60, ["Symptom 4", "Gift registration fails,", "purchase cannot move"], bad=True)
    d.box("NR", 310, 700, 200, 56, ["CRM holds no registration", "for the kit"])
    d.box("SPLIT", 790, 450, 200, 56, ["Purchase and registration", "on different accounts"])
    d.box("S5", 310, 810, 200, 60, ["Symptom 5", "Register your kit", "sent after results"], bad=True)
    d.box("DUP", 790, 20, 190, 50, ["Duplicate accounts"])
    d.box("MERGE", 790, 130, 190, 70, ["Merge keeps only the", "survivor's consent flags", "merge.py:3-4"], mono=(2,))
    d.box("S6", 790, 260, 190, 50, ["Symptom 6", "Opt-outs lost"], bad=True)
    d.edge([d.B("H"), d.T("S1")])
    d.edge([d.B("S1"), d.T("OW")])
    d.edge([d.B("OW"), d.T("S2")])
    d.edge([d.B("S2"), d.T("LOOK")])
    d.edge([d.R("S1"), (765, 160), (765, 478), d.L("SPLIT")])
    d.edge([d.L("GIFT"), d.R("LOOK")], "also looks up by email", dy=-10)
    d.edge([d.B("LOOK", -40), d.T("S3", -40)], "finds nobody", dx=-8, dy=0, anchor="end")
    d.edge([d.B("LOOK", 40), (190, 540), (405, 540), d.T("IC")], "finds a relative", at=(300, 540), dy=-10)
    d.edge([d.B("GIFT"), d.T("IO")])
    d.edge([d.B("IO"), d.T("S4")])
    d.edge([d.B("S3"), (150, 728), d.L("NR")])
    d.edge([d.B("IC"), d.T("NR")])
    d.edge([d.B("S4"), (640, 728), d.R("NR")])
    d.edge([d.B("NR"), d.T("S5")])
    d.edge([d.B("SPLIT"), (890, 840), d.R("S5")])
    d.edge([d.B("DUP"), d.T("MERGE")])
    d.edge([d.B("MERGE"), d.T("S6")])
    return d


# ============================================================ 6. topology
def topology():
    d = Diagram("topology", 1100, 660, "Topology: people, the commercial and clinical zones, legacy-sync between them and the identity fields that cross each hop",
                legend=("system", "code", "ext", "person"))
    d.pill("CUST", 450, 16, 200, 40, ["Customer or gift recipient"])
    d.cylinder("EC", 50, 140, 190, 84, ["E-commerce", "customers, orders, kits"])
    d.cylinder("CRM", 50, 330, 210, 96, ["CRM", "accounts, opportunities,", "consent flags"])
    d.box("MK", 50, 480, 210, 44, ["Nurture messages"], kind="ext")
    d.zone(20, 100, 330, 450, "Commercial systems")
    d.box("OS", 500, 190, 160, 46, ["Order sync"], kind="code")
    d.box("RG", 500, 300, 160, 46, ["Registration"], kind="code")
    d.zone(470, 150, 220, 230, "legacy-sync")
    d.cylinder("PORTAL", 760, 140, 180, 84, ["Member portal", "registrations"])
    d.cylinder("EHR", 755, 330, 150, 84, ["EHR", "charts"], kind="ext")
    d.pill("LAB", 765, 470, 130, 40, ["Lab partner"])
    d.zone(740, 100, 340, 440, "Clinical systems", red=True)
    d.pill("REP", 470, 480, 200, 40, ["Sales rep, account owner"])
    d.pill("SUP", 470, 550, 130, 40, ["Support"])
    d.pill("MKTG", 50, 590, 160, 40, ["Marketing team"])
    d.edge([d.L("CUST"), (145, 36), d.T("EC")], "buys", at=(145, 90), dx=8, dy=0, anchor="start")
    d.edge([d.R("CUST"), (850, 36), d.T("PORTAL")], "registers a kit", at=(850, 90), dx=8, dy=0, anchor="start")
    d.edge([d.R("EC", -10), (420, 172), (420, 213), d.L("OS")], ["order: customer_id, email,", "ship name and address, is_gift"], at=(330, 172), dy=-22, kind="code")
    d.edge([d.L("OS", 12), (440, 225), (440, 340), d.R("CRM", -38)], ["account: ecom_customer_id,", "email, phone", "opportunity: order_id"], at=(330, 290), dy=-14, kind="code")
    d.edge([d.L("PORTAL", 10), (715, 192), (715, 323), d.R("RG")], ["registration: kit barcode,", "email, name, birthdate"], at=(715, 250), dx=8, dy=0, anchor="start", kind="code")
    d.edge([d.L("RG", 12), (420, 335), (420, 392), d.R("CRM", 14)], ["account by email,", "gift opportunity moved"], at=(320, 368), dy=0, kind="code")
    d.edge([d.B("PORTAL", -30), d.T("EHR", -10)], "chart: name, birthdate", at=(828, 302), dx=0, dy=0, anchor="start", dashed=True)
    d.edge([d.T("LAB"), d.B("EHR")], ["result: kit barcode, chart_id,", "name, birthdate"], at=(838, 442), dx=0, dy=0, anchor="start", dashed=True)
    d.edge([d.T("EHR", 45), d.B("PORTAL", 40)], "results to view", at=(883, 250), dx=0, dy=0, anchor="start", dashed=True)
    d.edge([d.L("REP"), (330, 500), (330, 416), d.R("CRM", 38)], ["phone sales,", "owns accounts"], dashed=True, at=(330, 455), dx=8, dy=0, anchor="start")
    d.edge([d.L("SUP"), (300, 570), (300, 416)], ["moves purchases,", "merges duplicates"], dashed=True, at=(350, 570), dy=-22, arrow=False)
    d.edge([d.B("CRM"), d.T("MK")], "stage per account", dashed=True, dx=10, dy=0, anchor="start")
    d.edge([d.B("MK"), d.T("MKTG")], dashed=True)
    return d


# ============================================================ 7. journey
def journey():
    d = Diagram("journey", 1140, 440, "Customer journey: buy, CRM copy, ship, register, chart, sample, result, view, with the marketing messages each stage triggers",
                legend=("system", "code", "ext", "risk"))
    row, h = 100, 96
    d.box("B", 20, row, 160, h, ["Buy online", "e-commerce checkout", "gives email, name,", "phone, address"], kind="system")
    d.box("C", 210, row, 160, h, ["Order copied to CRM", "about 30 minutes later", "account found or created"], kind="code")
    d.box("S", 400, row, 160, h, ["Kit ships", "with a barcode", "delivered after 4 days"], kind="system")
    d.box("R", 590, row, 160, h, ["Register the kit", "member portal,", "1 day after delivery", "gives email, name,", "birthdate, phone"], kind="system")
    d.box("M", 780, row, 160, h, ["Mail the sample", "to the lab"], kind="ext")
    d.box("L", 970, row, 160, h, ["Result filed", "to the chart, 11 days", "after registration,", "linked by kit barcode"], kind="ext")
    d.box("N1", 210, 250, 160, 50, ["Message", "please register your kit"], bad=True, dashed=True)
    d.box("RC", 575, 250, 190, 84, ["Registration to CRM", "account found by email,", "or created", "the portal waits for the answer"], bad=True)
    d.box("N2", 590, 370, 160, 44, ["Message", "registered"], kind="ext", dashed=True)
    d.box("CH", 780, 250, 160, 60, ["Chart created in EHR", "from name and birthdate"], kind="ext")
    d.box("V", 970, 250, 160, 50, ["View results", "member portal"], kind="system")
    d.box("N3", 970, 370, 160, 44, ["Message", "results ready"], kind="ext", dashed=True)
    for a, b in [("B", "C"), ("C", "S"), ("S", "R"), ("R", "M"), ("M", "L")]:
        d.edge([d.R(a), d.L(b)])
    d.edge([d.B("C"), d.T("N1")], dashed=True, kind="risk")
    d.edge([d.B("R"), d.T("RC")], kind="code")
    d.edge([d.B("RC"), d.T("N2")], dashed=True)
    d.edge([d.B("R", 60), (730, 222), (860, 222), d.T("CH")], dashed=True)
    d.edge([d.B("L"), d.T("V")], dashed=True)
    d.edge([d.B("V"), d.T("N3")], dashed=True)
    d.edge([d.T("B"), (100, 60), (1050, 60), d.T("L")], "the kit barcode travels the whole way", at=(575, 60), arrow=False, dashed=True, kind="system")
    return d


def main():
    diagrams = [context(), er(), order_sync(), registration(), chain(), topology(), journey()]
    diagrams += TARGET_DIAGRAMS()
    for page_name in sorted({dg.page for dg in diagrams}):
        path = DOCS / page_name
        if not path.exists():
            print("skipping", page_name, "(not written yet)")
            continue
        page = path.read_text()
        count = 0
        for dg in diagrams:
            if dg.page != page_name:
                continue
            svg = dg.svg()
            (HERE / f"{dg.name}.svg").write_text(svg + "\n")
            pattern = re.compile(rf'(<figure class="diagram" data-svg="{dg.name}">).*?(</figure>)', re.S)
            page, n = pattern.subn(lambda m: m.group(1) + "\n" + svg + "\n" + dg.legend_html() + m.group(2), page)
            if n != 1:
                raise SystemExit(f"{dg.name}: expected one figure placeholder in {page_name}, found {n}")
            count += 1
        path.write_text(page)
        print("wrote", count, "diagrams into", page_name)


# ============================================================ target state
T = "target-architecture.html"


def t_topology():
    d = Diagram("t-topology", 1100, 620, "Target topology: an identity service between the commercial and clinical systems, holding the person key, links, evidence, review queue and audit log",
                legend=("system", "new", "ext", "person"), page=T)
    d.pill("CUST", 450, 16, 200, 40, ["Customer or gift recipient"])
    d.cylinder("EC", 40, 130, 190, 84, ["E-commerce", "unchanged"])
    d.cylinder("CRM", 40, 300, 200, 96, ["CRM", "today's and its replacement,", "person_key on each account"])
    d.box("MK", 40, 470, 200, 56, ["Marketing platform", "person_key, kit stage, consent"], kind="ext")
    d.box("API", 410, 205, 130, 50, ["Resolve API"], kind="new")
    d.box("MATCH", 570, 205, 120, 50, ["Matcher"], kind="new")
    d.box("REVIEW", 410, 275, 130, 50, ["Review queue"], kind="new")
    d.box("LOG", 570, 275, 120, 50, ["Event log"], kind="new")
    d.cylinder("STORE", 430, 345, 240, 96, ["Identity store", "person, source_record, identifier,", "relationship, kit_role, consent"], kind="new")
    d.zone(390, 165, 320, 300, "Identity service, new")
    d.cylinder("PORTAL", 870, 130, 190, 84, ["Member portal", "accepts first, resolves after"])
    d.cylinder("EHR", 870, 300, 180, 84, ["EHR", "chart carries person_key", "as an external identifier"], kind="ext")
    d.pill("LAB", 860, 480, 200, 40, ["Lab partner, unchanged"])
    d.pill("SUP", 430, 520, 170, 40, ["Support decides"])
    d.edge([d.L("CUST"), (135, 36), d.T("EC")], "buys", at=(135, 85), dx=8, dy=0, anchor="start")
    d.edge([d.R("CUST"), (965, 36), d.T("PORTAL")], "registers a kit", at=(965, 85), dx=8, dy=0, anchor="start")
    d.edge([d.R("EC", -10), (330, 162), (330, 220), d.L("API", -10)], ["order event: customer_id,", "email, ship-to, gift flag"], at=(330, 110), dy=0, kind="new")
    d.edge([d.L("API", 10), (310, 240), (310, 330), d.R("CRM", -18)], ["opportunity on the buyer's person,", "recipient as a role, no email rewrite"], at=(300, 285), dy=0, kind="new")
    d.edge([d.R("CRM", 18), (350, 366), (350, 395), d.L("STORE", 5)], "rep edits, consent changes", at=(360, 420), dy=0, kind="new")
    d.edge([d.B("STORE", -60), (490, 475), (240, 475), d.R("MK", -10)], ["person_key, kit stage,", "channel consent, nothing clinical"], at=(360, 500), dy=10, kind="new")
    d.edge([d.L("PORTAL", -10), (475, 152), d.T("API")], ["registration event,", "after the portal has accepted it"], at=(660, 152), dy=-24, kind="new")
    d.edge([d.R("API", 10), (800, 240), (800, 330), d.L("EHR", -18)], ["person_key written to the chart,", "chart_id linked back"], at=(810, 285), dy=0, kind="new")
    d.edge([d.B("PORTAL", 40), d.T("EHR", 40)], "chart, unchanged", dashed=True, dx=-8, dy=0, anchor="end")
    d.edge([d.T("LAB"), d.B("EHR")], "result by kit barcode", dashed=True, dx=8, dy=0, anchor="start")
    d.edge([d.L("EHR", 18), (760, 348), (760, 400), d.R("STORE", 5)], "result event, status only", at=(760, 455), dy=0, kind="new")
    d.edge([d.T("SUP"), (515, 500), (515, 441)], "decisions", dx=8, dy=0, anchor="start", at=(515, 480))
    return d


def t_model():
    d = Diagram("t-model", 1040, 640, "Target data model: a person with linked source records, identifiers with provenance, relationships, kit roles, consent per channel, a review queue and an append-only event log", page=T)
    d.entity("PERSON", 40, 30, 240, "person", [("person_key", "PK", "opaque, never reused"), ("status", "", "active or merged"), ("merged_into", "FK", "nullable"), ("created_at", "", "")])
    d.entity("SRC", 340, 30, 300, "source_record", [("system, record_id", "PK", ""), ("person_key", "FK", ""), ("confidence", "", "0 to 1"), ("method", "", "rule, score, human"), ("evidence", "", "which fields agreed"), ("status", "", "linked, review, rejected"), ("linked_at", "", "")])
    d.entity("IDENT", 340, 250, 300, "identifier", [("identifier_id", "PK", ""), ("person_key", "FK", ""), ("type", "", "email, phone, dob, name, address"), ("value_normalized", "", ""), ("source_system, observed_at", "", "history kept"), ("preferred", "", "chosen, never overwritten")])
    d.entity("REL", 40, 250, 240, "relationship", [("person_a, person_b", "FK", ""), ("type", "", "household, guardian, gift"), ("evidence", "", "")])
    d.entity("KIT", 700, 30, 300, "kit_role", [("kit_barcode", "PK", ""), ("order_id", "", ""), ("buyer_person", "FK", ""), ("registrant_person", "FK", "until registered"), ("patient_person", "FK", "from the result"), ("stage", "", "bought, shipped, registered, resulted")])
    d.entity("CONSENT", 700, 250, 300, "consent", [("consent_id", "PK", ""), ("person_key", "FK", ""), ("channel, address_value", "", "sms number or email"), ("status", "", "opt_in or opt_out"), ("source_system, observed_at", "", "strictest wins")])
    d.entity("REVIEW", 40, 430, 300, "review_item", [("review_id", "PK", ""), ("record_a, record_b", "FK", ""), ("score, reasons", "", "codes, no names"), ("decision, decided_by, decided_at", "", "")])
    d.entity("EVENT", 700, 430, 300, "identity_event", [("event_id", "PK", "append only"), ("person_key", "FK", ""), ("kind", "", "link, unlink, merge, split, view"), ("actor, reason, at", "", "")])
    d.edge([d.R("PERSON", -20), d.L("SRC", -20)], "1 to many", dy=-10, arrow=False)
    d.edge([d.R("PERSON", 30), (310, 111), (310, 300), d.L("IDENT", -20)], "1 to many", at=(310, 200), dx=8, dy=0, anchor="start", arrow=False)
    d.edge([d.B("PERSON", -60), d.T("REL", -60)], "2 per row", dx=10, dy=0, anchor="start", arrow=False)
    d.edge([d.R("SRC", -40), d.L("KIT", -40)], "3 roles per kit", dy=14, arrow=False, kind="new")
    d.edge([d.R("IDENT", -20), d.L("CONSENT", -20)], "per person", dy=14, arrow=False)
    d.edge([d.B("REL", -60), d.T("REVIEW", -60)], "pairs under review", dx=10, dy=0, anchor="start", arrow=False)
    d.edge([d.B("CONSENT", 60), d.T("EVENT", 60)], "every change logged", dx=10, dy=0, anchor="start", arrow=False)
    return d


def t_matching():
    d = Diagram("t-matching", 1100, 420, "Matching pipeline: normalise, link deterministically, generate candidate pairs, score, split by threshold into automatic links, a review queue and no link, then cluster under constraints",
                legend=("step", "new", "system", "ext"), page=T)
    row = 50
    d.box("N1", 20, row, 170, 90, ["Normalise", "emails, phones, names", "with a nickname table,", "dates, addresses"])
    d.box("N2", 215, row, 170, 90, ["Deterministic links", "kit barcode chain,", "order to opportunity", "confidence 1.0"], kind="system")
    d.box("N3", 410, row, 170, 90, ["Candidate pairs", "share an email, a phone,", "surname and zip,", "or surname and birthdate"])
    d.box("N4", 605, row, 180, 90, ["Score the pair", "agree and disagree weights", "birthdate conflict is a veto", "household is not identity"], kind="new")
    d.diamond("TH", 880, row + 45, 150, 80, ["Score?"])
    d.box("AUTO", 920, 250, 170, 56, ["0.90 and above", "link automatically"], kind="system")
    d.box("REV", 640, 260, 190, 56, ["0.60 to 0.90", "review queue, with reasons"], kind="ext")
    d.box("NONE", 420, 260, 170, 56, ["below 0.60", "no link"])
    d.box("N5", 640, 340, 250, 70, ["Constrained clustering", "no cluster with two birthdates,", "EHR charts never merged by code"], kind="new")
    d.box("N6", 20, 340, 340, 70, ["Outputs", "person_key and confidence per record,", "review items, event log entries"], kind="system")
    for a, b in [("N1", "N2"), ("N2", "N3"), ("N3", "N4")]:
        d.edge([d.R(a), d.L(b)])
    d.edge([d.R("N4"), d.L("TH")])
    d.edge([d.R("TH"), (1005, 165), d.T("AUTO")], kind="system")
    d.edge([d.B("TH"), (880, 235), (735, 235), d.T("REV")], kind="ext")
    d.edge([(880, 235), (505, 235), d.T("NONE")], "no link", at=(600, 235), dy=-10)
    d.edge([d.B("AUTO"), (1005, 375), d.R("N5")], "accepted links", at=(1005, 340), dx=8, dy=0, anchor="start", kind="system")
    d.edge([d.B("REV"), d.T("N5", -30)], "human yes or no", dx=8, dy=0, anchor="start", dashed=True)
    d.edge([d.L("N5"), d.R("N6")])
    return d


def t_registration():
    d = Diagram("t-registration", 1100, 330, "Registration never waits on identity: the portal accepts, a provisional person is created, resolution runs afterwards and a merge or a review item follows",
                legend=("system", "new", "ext"), page=T)
    row = 90
    d.box("P1", 20, row, 180, 80, ["Portal accepts", "the registration", "milliseconds"], kind="system")
    d.box("P2", 230, row, 200, 80, ["Provisional person", "linked to this registration", "with confidence 1.0"], kind="new")
    d.box("P3", 460, row, 190, 80, ["Kit stage: registered", "chart and lab flow", "continue as today"], kind="system")
    d.box("P4", 680, row, 190, 80, ["Resolve in the background", "match against", "existing people"], kind="new")
    d.diamond("Q", 980, row + 40, 150, 80, ["Confident?"])
    d.box("P5", 680, 230, 190, 60, ["Merge provisional into", "the person, log the event"], kind="new")
    d.box("P6", 900, 230, 190, 60, ["Review item", "kit keeps the provisional person"], kind="ext")
    for a, b in [("P1", "P2"), ("P2", "P3"), ("P3", "P4")]:
        d.edge([d.R(a), d.L(b)])
    d.edge([d.R("P4"), d.L("Q")])
    d.edge([d.B("Q", -30), (950, 200), (775, 200), d.T("P5")], "yes", at=(950, 185), dx=8, dy=0, anchor="start", kind="system")
    d.edge([d.B("Q", 30), (1010, 200), (995, 200), d.T("P6")], "no", at=(1010, 185), dx=8, dy=0, anchor="start", kind="ext")
    d.edge([d.T("P1"), (110, 40), (575, 40), d.T("P3")], "nothing on this path calls the CRM", at=(340, 40), arrow=False, dashed=True, kind="system")
    return d


def t_phi():
    d = Diagram("t-phi", 1100, 420, "Protected health information: the clinical zone and the identity store sit inside the boundary; the commercial zone receives the person key, contact details and consent, never results or test names",
                legend=("system", "new", "ext"), page=T)
    d.cylinder("PORTAL", 50, 110, 170, 76, ["Member portal"])
    d.cylinder("EHR", 50, 230, 170, 76, ["EHR"], kind="ext")
    d.pill("LAB", 60, 345, 150, 36, ["Lab partner"])
    d.zone(20, 60, 230, 340, "Clinical zone, PHI", red=True)
    d.cylinder("STORE", 420, 150, 260, 110, ["Identity store", "demographics, links, consent,", "every access logged"], kind="new")
    d.box("HASH", 420, 300, 260, 50, ["Hashed match keys for blocking", "outside the boundary"], kind="new")
    d.zone(390, 60, 320, 340, "Identity service, PHI, restricted access", red=True)
    d.cylinder("CRM", 850, 90, 200, 80, ["CRM", "sales and support"])
    d.box("MK", 850, 215, 200, 56, ["Marketing platform"], kind="ext")
    d.cylinder("EC", 850, 310, 200, 76, ["E-commerce"])
    d.zone(820, 60, 260, 340, "Commercial zone")
    d.edge([d.R("PORTAL"), (320, 148), (320, 180), d.L("STORE", -25)], ["registration: name, email,", "phone, birthdate, kit barcode"], at=(320, 110), dy=0, kind="new")
    d.edge([d.R("EHR"), (320, 268), (320, 220), d.L("STORE", 15)], ["chart_id and result event,", "status only, without values"], at=(320, 300), dy=0, kind="new")
    d.edge([d.R("STORE", -30), (760, 175), (760, 130), d.L("CRM")], ["person_key, preferred contact", "details, consent flags"], at=(805, 100), dy=0, anchor="end", kind="new")
    d.edge([d.R("STORE", 10), (760, 215), (760, 243), d.L("MK")], ["person_key, kit stage,", "channel consent"], at=(760, 290), dy=0, kind="new")
    d.edge([d.L("EC"), (760, 348), (760, 330), d.R("HASH", 5)], ["order event in,", "person_key back"], at=(760, 380), dy=0, kind="new")
    d.edge([d.B("STORE", 0), d.T("HASH", 0)], None, arrow=False)
    return d


def t_review():
    d = Diagram("t-review", 1100, 400, "Review item lifecycle: open, claimed, decided, applied and closed, with side paths for a lapsed claim, escalation, an item superseded by new evidence and a decision that fails to apply",
                legend=("step", "new", "system", "ext", "risk"), page=T)
    row = 150
    d.box("OPEN", 20, row, 150, 70, ["Open", "queued with score", "and reason codes"], kind="new")
    d.box("CLAIM", 235, row, 150, 70, ["Claimed", "one reviewer,", "30-minute lease"], kind="new")
    d.box("DEC", 450, row, 160, 70, ["Decided", "same, different", "or cannot tell"], kind="new")
    d.box("APPLY", 675, row, 160, 70, ["Applying", "re-check evidence,", "merge or keep apart"], kind="new")
    d.box("CLOSED", 900, row, 180, 70, ["Closed", "event logged, consumers", "notified, label stored"], kind="system")
    d.box("ESC", 450, 30, 160, 60, ["Escalated", "second reviewer or", "clinical operations"], kind="ext")
    d.box("SUP", 40, 290, 190, 64, ["Superseded", "evidence changed,", "pair re-scored"], kind="step")
    d.box("FAIL", 675, 300, 160, 64, ["Apply failed", "retried, then paged", "nothing half-applied"], bad=True)
    d.edge([d.R("OPEN"), d.L("CLAIM")], "claim", kind="new")
    d.edge([d.R("CLAIM"), d.L("DEC")], "decide", kind="new")
    d.edge([d.R("DEC"), d.L("APPLY")], "same or different", kind="new")
    d.edge([d.R("APPLY"), d.L("CLOSED")], "committed", kind="system")
    d.edge([d.T("CLAIM", -30), (280, 110), (95, 110), d.T("OPEN")], "lease lapses", at=(190, 110), dy=-10)
    d.edge([d.T("DEC"), d.B("ESC")], ["cannot tell, chart pair", "or high-risk merge"], dx=10, dy=0, anchor="start", dashed=True)
    d.edge([d.R("ESC"), (755, 60), d.T("APPLY")], "second decision", at=(690, 60), dy=-10, dashed=True)
    d.edge([d.B("OPEN", 20), d.T("SUP", 0)], "new record or link", dx=10, dy=0, anchor="start")
    d.edge([d.B("APPLY", -40), (715, 260), (140, 260), d.T("SUP", 25)], "evidence no longer matches the decision", at=(430, 260), dy=-10)
    d.edge([d.B("APPLY", 20), d.T("FAIL", 20)], "error", dx=8, dy=0, anchor="start", kind="risk")
    d.edge([d.B("SUP", -40), (75, 385), (8, 385), (8, 185), d.L("OPEN")], "re-queued, or closed as moot", at=(90, 385), dx=0, dy=0, anchor="start")
    return d


def TARGET_DIAGRAMS():
    return [t_topology(), t_model(), t_matching(), t_registration(), t_phi(), t_review()]


if __name__ == "__main__":
    main()
