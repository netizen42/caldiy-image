"""Mails de Cal.diy à la charte Symind (retour d'Adrien du 2026-11-13 : « de beaux mails HTML à la charte ? »).

Appliqué au source de cal.diy avant la construction de l'image web (workflow image.yml) : bandeau encre avec le logo
« Symind. », surtitre au carré turquoise, titre en Instrument Serif (Georgia en secours), corps en Inter sur papier,
liens turquoise, pied Symind ; dates des objets en ordre français. Chaque remplacement est vérifié : si cal.diy change
un gabarit, la construction échoue ici au lieu de livrer un mail à moitié habillé. Modèle : skill charte-symind,
email/modele-email.html. Usage : python3 charte-mails.py <dossier source cal.diy>
"""
import pathlib
import re
import sys

SRC = pathlib.Path(sys.argv[1]) / "packages/emails"
FAUTES = []


def remplacer(chemin, avant, apres, compte=1):
    f = SRC / chemin
    t = f.read_text()
    n = t.count(avant)
    if n != compte:
        FAUTES.append(f"{chemin} : {n} occurrence(s) au lieu de {compte} pour {avant[:70]!r}")
        return
    f.write_text(t.replace(avant, apres))


SERIF = "Instrument Serif, Georgia, Times New Roman, serif"
SANS = "Inter, Arial, Helvetica, sans-serif"

# 1. Gabarit commun : bandeau encre en tête de carte, carte arrondie à filet fin, pied Symind à la place du logo Cal.
B = "src/components/BaseEmailHtml.tsx"
remplacer(B, 'import EmailBodyLogo from "./EmailBodyLogo";\n', "")
remplacer(B, 'import EmailScheduledBodyHeaderContent from "./EmailScheduledBodyHeaderContent";\n', "")
remplacer(B, 'import EmailSchedulingBodyHeader from "./EmailSchedulingBodyHeader";\n', "")
remplacer(B, 'backgroundColor: "#F3F4F6"', 'backgroundColor: "#FAFAF7"', 2)
remplacer(B, 'paddingTop: "40px",', 'paddingTop: "32px",')
remplacer(B, '''              borderRadius: "8px",
              border: "1px solid #E5E7EB",
              padding: "2px",
              backgroundColor: "#FFFFFF",''', '''              borderRadius: "16px",
              border: "1px solid #E7E5DF",
              overflow: "hidden",
              backgroundColor: "#FFFFFF",''')
remplacer(B, '''            {props.headerType && (
              <EmailSchedulingBodyHeader headerType={props.headerType} headStyles={{ border: 0 }} />
            )}
            {props.title && (
              <EmailScheduledBodyHeaderContent
                headStyles={{ border: 0 }}
                title={props.title}
                subtitle={props.subtitle}
              />
            )}
            {(props.headerType || props.title || props.subtitle) && (
              <EmailSchedulingBodyDivider headStyles={{ border: 0 }} />
            )}''', f'''            <div style={{{{ background: "#0E1113", padding: "28px 32px 30px", textAlign: "left" }}}}>
              <a href="https://www.symind.ai" target="_blank" rel="noreferrer">
                <img
                  src="https://www.symind.ai/brand/logo-fond-sombre.png"
                  width="130"
                  alt="Symind"
                  style={{{{ display: "block", width: "130px", height: "auto", border: "0" }}}}
                />
              </a>
              <div
                style={{{{
                  paddingTop: "24px",
                  fontFamily: "{SANS}",
                  fontSize: "13px",
                  lineHeight: "18px",
                  fontWeight: 500,
                  color: "#A9AEB5",
                }}}}>
                <span
                  style={{{{
                    display: "inline-block",
                    width: "7px",
                    height: "7px",
                    background: "#57C1B9",
                    marginRight: "8px",
                    verticalAlign: "1px",
                  }}}}
                />
                Rendez-vous avec Symind
              </div>
              {{props.title && (
                <div
                  data-testid="heading"
                  style={{{{
                    paddingTop: "10px",
                    fontFamily: "{SERIF}",
                    fontSize: "30px",
                    lineHeight: "36px",
                    fontWeight: 400,
                    color: "#FFFFFF",
                  }}}}>
                  {{props.title}}
                </div>
              )}}
              {{props.subtitle && (
                <div
                  data-testid="subHeading"
                  style={{{{
                    paddingTop: "8px",
                    fontFamily: "{SANS}",
                    fontSize: "14px",
                    lineHeight: "21px",
                    fontWeight: 400,
                    color: "#A9AEB5",
                  }}}}>
                  {{props.subtitle}}
                </div>
              )}}
            </div>''')
remplacer(B, '{!Boolean(props.hideLogo) && <EmailBodyLogo />}', f'''<div
            style={{{{
              margin: "0px auto",
              maxWidth: 600,
              padding: "18px 32px 32px",
              fontFamily: "{SANS}",
              fontSize: "12px",
              lineHeight: "18px",
              color: "#6B6F77",
              textAlign: "center",
            }}}}>
            Symind · Agents IA pour les PME ·{{" "}}
            <a href="https://www.symind.ai" style={{{{ color: "#247C75", textDecoration: "none" }}}}>
              symind.ai
            </a>
          </div>''')
remplacer(B, '''                            fontSize: 16,
                            fontWeight: 500,
                            lineHeight: 1,''', '''                            fontSize: 15,
                            fontWeight: 500,
                            lineHeight: 1,''')

# 2. Rubriques (Quoi, Quand, Qui, Où...) : libellé gris discret, valeur en encre.
I = "src/components/Info.tsx"
remplacer(I, '''        <p style={{ color: "#101010" }}>''',
          '''        <p style={{ color: "#6B6F77", fontSize: "13px", lineHeight: "18px", fontWeight: 500, margin: "4px 0 4px" }}>''')
# Libellé des questions du formulaire (téléphone, projet) : HTML sans <p> imbriqué, sinon le navigateur casse la
# rubrique et le libellé sort en gros texte noir (essai réel du 13/11).
remplacer(I, "{props.isLabelHTML ? <StyledHtmlContent htmlContent={safeLabel} /> : props.label}",
          '{props.isLabelHTML ? (\n            <span dangerouslySetInnerHTML={{ __html: (safeLabel || "").replace(/<\\/?p[^>]*>/g, "") }} />\n'
          '          ) : (\n            props.label\n          )}')
remplacer(I, '''            color: "#101010",
            fontWeight: 400,
            lineHeight: "24px",''', '''            color: "#0E1113",
            fontWeight: 400,
            lineHeight: "24px",
            margin: "0",''')

# 3. Polices et couleurs dans tous les gabarits : Inter au lieu de Roboto, jetons du kit au lieu des gris de Cal.
COULEURS = {
    "#101010": "#0E1113", "#111827": "#0E1113", "#292929": "#0E1113",
    "#3E3E3E": "#4A4F57", "#3e3e3e": "#4A4F57", "#494949": "#4A4F57", "#4B5563": "#6B6F77", "#6B7280": "#6B6F77",
    "#374151": "#247C75",
    "#E1E1E1": "#E7E5DF", "#E5E7EB": "#E7E5DF", "#e5e7eb": "#E7E5DF", "#D1D5DB": "#E7E5DF", "#d1d5db": "#E7E5DF",
    "#F3F4F6": "#FAFAF7",
}
roboto = 0
for f in (SRC / "src").rglob("*.tsx"):
    t = f.read_text()
    n = t.replace("Roboto, Helvetica, sans-serif", SANS)
    roboto += t.count("Roboto, Helvetica, sans-serif")
    for a, b in COULEURS.items():
        n = n.replace(a, b)
    if n != t:
        f.write_text(n)
if roboto < 5:
    FAUTES.append(f"police Roboto trouvée {roboto} fois seulement")
remplacer("src/components/EmailHead.tsx", "family=Roboto:400,500,700", "family=Inter:400,500,600|Instrument+Serif", 2)

# 4. Dates des objets en ordre français : « 09:30 - 10:00, lundi 23 novembre 2026 » au lieu de
#    « 9:30am - 10:00am, lundi, novembre 23, 2026 ».
remplacer("src/templates/BaseScheduledEmail.tsx", 'getRecipientStart("h:mma")} - ${getRecipientEnd("h:mma")}',
          'getRecipientStart("HH:mm")} - ${getRecipientEnd("HH:mm")}')
DATE = re.compile(r'\$\{(this\.)?t\(\s*(this\.get\w+Start|getRecipientStart)\("dddd"\)\.toLowerCase\(\)\s*\)\},\s*'
                  r'\$\{(?:this\.)?t\(\s*\2\("MMMM"\)\.toLowerCase\(\)\s*\)\}\s*\$\{\2\("D, YYYY"\)\}')
dates = 0
for f in list((SRC / "templates").glob("*.ts")) + list((SRC / "src/templates").glob("*.tsx")):
    t = f.read_text()
    n, k = DATE.subn(lambda m: f'${{{m[1] or ""}t({m[2]}("dddd").toLowerCase())}} ${{{m[2]}("D")}} '
                              f'${{{m[1] or ""}t({m[2]}("MMMM").toLowerCase())}} ${{{m[2]}("YYYY")}}', t)
    if k:
        f.write_text(n)
        dates += k
if dates < 5:
    FAUTES.append(f"dates d'objet réordonnées {dates} fois seulement")

if FAUTES:
    sys.exit("charte-mails : gabarit de cal.diy inattendu\n" + "\n".join(FAUTES))
print(f"charte-mails : gabarit commun, rubriques, {roboto} polices, {dates} dates d'objet")
