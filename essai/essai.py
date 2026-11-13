"""Essai fonctionnel : compte, clé d'API, horaires, type de rendez-vous avec questions et champs cachés, webhook signé,
réservation par la page publique (avec utm et champ prérempli), lecture par l'API v2, report, annulation, mails,
inscription fermée. Écrit pour la CI ; sort en erreur au premier écart."""
import hashlib, hmac, json, os, pathlib, secrets, subprocess, sys, time, urllib.error, urllib.request, uuid
from datetime import date, timedelta

WEB, API = "http://127.0.0.1:3000", "http://127.0.0.1:5555"
ICI = pathlib.Path(__file__).parent
SECRET_WH = secrets.token_hex(16)


def appel(methode, url, corps=None, en_tetes=None, attendu=(200, 201)):
    req = urllib.request.Request(url, method=methode, data=None if corps is None else json.dumps(corps).encode(),
                                 headers={"Content-Type": "application/json", **(en_tetes or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            code, texte = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        code, texte = e.code, e.read().decode()
    if attendu and code not in attendu:
        sys.exit(f"ÉCHEC {methode} {url} -> {code} {texte[:1500]}")
    try:
        return code, json.loads(texte)
    except ValueError:
        return code, texte


def ok(msg):
    print("ok :", msg, flush=True)


def psql(sql):
    return subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "caldiy", "-d", "caldiy", "-At",
                           "-c", sql], cwd=ICI, check=True, capture_output=True, text=True).stdout.strip()


# 1. Premier compte (administrateur), par la route d'installation
appel("POST", WEB + "/api/auth/setup", {"username": "adrien", "full_name": "Adrien Beun", "email_address":
      "adrien@test.invalid", "password": "Essai-" + secrets.token_hex(8) + "-Aa1"})
appel("POST", WEB + "/api/auth/setup", {"username": "x", "full_name": "xxx", "email_address": "x@test.invalid",
      "password": "Essai-" + secrets.token_hex(8) + "-Aa1"}, attendu=(400,))
ok("compte créé, seconde installation refusée")

# 2. Clé d'API posée en base (empreinte SHA-256 de la clé sans son préfixe)
uid = psql("select id from users where username='adrien'")
cle = secrets.token_hex(24)
psql(f"insert into \"ApiKey\"(id, \"userId\", note, \"hashedKey\") values ('{uuid.uuid4()}', {uid}, 'essai', "
     f"'{hashlib.sha256(cle.encode()).hexdigest()}')")
H = {"Authorization": "Bearer cal_" + cle}
_, me = appel("GET", API + "/v2/me", en_tetes=H)
assert me["data"]["username"] == "adrien", me
ok("API v2 : /v2/me")

# 3. Horaires (comme Calendly : lun-jeu 9h30-12h et 14h-18h30, vendredi 9h30-12h)
semaine = ["Monday", "Tuesday", "Wednesday", "Thursday"]
_, sch = appel("POST", API + "/v2/schedules", {"name": "Horaires Symind", "timeZone": "Europe/Paris", "isDefault": True,
               "availability": [{"days": semaine + ["Friday"], "startTime": "09:30", "endTime": "12:00"},
                                {"days": semaine, "startTime": "14:00", "endTime": "18:30"}]},
               en_tetes={**H, "cal-api-version": "2024-06-11"})
ok("horaires : " + str(sch["data"]["id"]))

# 4. Type de rendez-vous : 30 min (15 ou 30), téléphone obligatoire, projet facultatif, utm en champs cachés
champs = [{"type": "phone", "slug": "telephone", "label": "Numéro de téléphone à contacter :", "required": True},
          {"type": "textarea", "slug": "projet", "label": "Merci de bien vouloir m'expliquer votre projet en quelques lignes",
           "required": False}]
champs += [{"type": "text", "slug": u, "label": u, "required": False, "hidden": True}
           for u in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")]
_, et = appel("POST", API + "/v2/event-types", {"title": "Premier échange avec Symind (30 min)", "slug": "30min",
              "lengthInMinutes": 30, "lengthInMinutesOptions": [15, 30], "description": "Essai",
              "bookingFields": champs, "minimumBookingNotice": 240},
              en_tetes={**H, "cal-api-version": "2024-06-14"})
etid = et["data"]["id"]
ok(f"type de rendez-vous {etid}")

# 5. Webhook signé vers le récepteur de l'essai (adresse interne en http : permise en auto-hébergé)
_, wh = appel("POST", API + "/v2/webhooks", {"subscriberUrl": "http://recepteur:8080/", "active": True, "secret": SECRET_WH,
              "triggers": ["BOOKING_CREATED", "BOOKING_RESCHEDULED", "BOOKING_CANCELLED"]}, en_tetes=H)
ok("webhook " + str(wh["data"]["id"]))

# 6. Créneaux
debut = date.today() + timedelta(days=3)
_, sl = appel("GET", API + f"/v2/slots?eventTypeId={etid}&start={debut}&end={debut + timedelta(days=10)}&timeZone=Europe/Paris",
              en_tetes={**H, "cal-api-version": "2024-09-04"})
creneaux = [s["start"] for j in sorted(sl["data"]) for s in sl["data"][j]]
assert len(creneaux) > 5, sl
ok(f"{len(creneaux)} créneaux, premier {creneaux[0]}")

# 7. Réservation comme la page publique (même route que le formulaire), avec utm et champ prérempli
utm = {"utm_source": "machine", "utm_medium": "linkedin", "utm_campaign": "partenaire-essai", "utm_content": "P-123"}
reponses = {"name": "Essai Symind", "email": "invite@test.invalid", "telephone": "+33600000000",
            "projet": "Entretien partenaire", **utm}
_, b = appel("POST", WEB + "/api/book/event", {"eventTypeId": etid, "start": creneaux[0], "timeZone": "Europe/Paris",
             "language": "fr", "metadata": {}, "responses": reponses, "tracking": utm, "user": "adrien"})
buid = b["uid"]
ok("réservation " + buid)


def webhook(declencheur, attente=60):
    for _ in range(attente):
        for f in sorted((ICI / "recu").glob("*.json")):
            d = json.loads(f.read_text())
            corps = json.loads(d["corps"])
            if corps.get("triggerEvent") == declencheur:
                sig = {k.lower(): v for k, v in d["en_tetes"].items()}.get("x-cal-signature-256")
                attendu = hmac.new(SECRET_WH.encode(), d["corps"].encode(), hashlib.sha256).hexdigest()
                assert sig == attendu, ("signature", sig, attendu)
                f.unlink()
                return corps
        time.sleep(1)
    sys.exit(f"ÉCHEC webhook {declencheur} non reçu")


c = webhook("BOOKING_CREATED")
p = c["payload"]
print(json.dumps({k: p.get(k) for k in ("uid", "startTime", "responses", "metadata", "tracking", "userFieldsResponses")},
                 ensure_ascii=False)[:2500])
assert p["responses"]["utm_content"]["value"] == "P-123", p["responses"]
assert p["responses"]["projet"]["value"] == "Entretien partenaire"
ok("webhook BOOKING_CREATED signé, utm et champ prérempli présents")

# 8. Lecture par l'API v2
_, lu = appel("GET", API + f"/v2/bookings/{buid}", en_tetes={**H, "cal-api-version": "2024-08-13"})
print(json.dumps(lu["data"], ensure_ascii=False)[:1500])
ok("lecture API v2")
print("suivi en base :", psql(f"select t.utm_source, t.utm_content, t.utm_campaign from \"Tracking\" t join \"Booking\" b on "
                              f"b.id = t.\"bookingId\" where b.uid = '{buid}'"))

# 9. Report puis annulation par l'API v2
_, rs = appel("POST", API + f"/v2/bookings/{buid}/reschedule", {"start": creneaux[3], "reschedulingReason": "essai"},
              en_tetes={**H, "cal-api-version": "2024-08-13"})
nuid = rs["data"]["uid"]
webhook("BOOKING_RESCHEDULED")
ok("report " + nuid)
appel("POST", API + f"/v2/bookings/{nuid}/cancel", {"cancellationReason": "essai"},
      en_tetes={**H, "cal-api-version": "2024-08-13"})
webhook("BOOKING_CANCELLED")
ok("annulation")

# 10. Mails (boîte de test)
time.sleep(5)
_, m = appel("GET", "http://127.0.0.1:8025/api/v1/messages")
sujets = [(x["To"][0]["Address"], x["Subject"]) for x in m["messages"]]
print("mails :", sujets)
assert any(a == "invite@test.invalid" for a, _ in sujets), "pas de mail à l'invité"
ok(f"{len(sujets)} mails")

# 11. Inscription fermée
code, r = appel("POST", WEB + "/api/auth/signup", {"username": "intrus", "email": "intrus@test.invalid",
                "password": "Intrus-" + secrets.token_hex(8) + "-Aa1", "language": "fr"}, attendu=None)
print("inscription :", code, str(r)[:200])
assert code >= 400, "inscription ouverte"
ok("inscription fermée")
print("ESSAI COMPLET")
