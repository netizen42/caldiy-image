# caldiy-image

Images Docker de [Cal.diy](https://github.com/calcom/cal.diy) (licence MIT) construites pour un usage personnel
auto-hébergé, essayées sans droits root avant publication sur ghcr.io. Lancement : onglet Actions, « Image Cal.diy »,
avec le commit voulu de calcom/cal.diy.

`charte-mails.py` habille les mails de Cal.diy aux couleurs de Symind avant la construction ; il échoue si un gabarit
de Cal.diy a changé. Toute retouche : monter `MAILS_VERSION` dans le workflow (seule la base web est reconstruite).
