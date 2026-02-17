# Priorisierung & Projektmanagement – Hauskeeping

Hauskeeping ist ein Open-Source-Projekt, das von [@iLollek](https://github.com/iLollek) entwickelt und gepflegt wird. Dieses Dokument beschreibt, wie das Projekt organisiert ist, wie Features und Bugs priorisiert werden und wie Releases entstehen.

---

## Projektstruktur

Hauskeeping wird als Solo-Projekt ohne festes Team oder feste Arbeitszeiten entwickelt. Es gibt keinen Product Owner, keinen Scrum-Master und keine Sprints mit definiertem Zeitfenster. Entscheidungen über Scope, Priorität und Umsetzung trifft ausschließlich der Maintainer.

Das Projekt lebt von Community-Beiträgen über GitHub. Wer einen Bug findet oder eine Idee hat, öffnet einen Issue – der Maintainer sichtet, bewertet und priorisiert ihn.

---

## Priorisierung mit dem MoSCoW-Modell

Hauskeeping verwendet das **MoSCoW-Modell** zur Priorisierung von Features, Bugfixes und technischen Aufgaben. Jeder Issue wird vom Maintainer einer der vier Kategorien zugeordnet:

| Priorität | Label | Bedeutung |
|---|---|---|
| **MUST** | `must` | Muss umgesetzt werden. Ohne dieses Feature/diesen Fix ist das Projekt unvollständig oder fehlerhaft. Blockiert ggf. ein Release. |
| **SHOULD** | `should` | Soll umgesetzt werden, solange Aufwand und Nutzen in einem vernünftigen Verhältnis stehen. Kein Blocker, aber klar wertvoll. |
| **COULD** | `could` | Wäre nice to have. Wird umgesetzt, wenn Zeit und Kapazität da sind – ohne konkreten Anspruch auf einen Platz im nächsten Release. |
| **WON'T** | `wont` | Wird bewusst nicht umgesetzt – zumindest nicht in absehbarer Zeit. Begründung wird im Issue hinterlassen. |

### Entscheidungskriterien

Beim Einordnen eines Issues stellt der Maintainer folgende Fragen:

- **Betrifft es die Kernfunktion von Hauskeeping?** → Tendenz MUST/SHOULD
- **Wie viele User sind davon betroffen?** → Breite Wirkung → höhere Priorität
- **Wie hoch ist der Implementierungsaufwand?** → Hoher Aufwand bei geringem Nutzen → COULD oder WON'T
- **Passt es zum Designrahmen des Projekts?** → Sprengt es den Scope? → WON'T
- **Ist es ein Bug oder ein Feature?** → Bugs mit Auswirkung auf Kernfunktion → immer mindestens SHOULD

---

## Issues & GitHub

Neue Features und Bugs werden ausschließlich über den **GitHub Issues Tab** gemeldet:  
[github.com/iLollek/hauskeeping/issues](https://github.com/iLollek/hauskeeping/issues) 

### Issue-Typen

Grundsätzlich gibt es zwei Arten von Issues:

- **Bug Report** – etwas funktioniert nicht wie erwartet
- **Feature Request** – eine neue Funktion oder Verbesserung wird gewünscht

### Lebenszyklus eines Issues

```
Issue wird geöffnet (Community oder Maintainer)
        ↓
Maintainer sichtet und vergibt MoSCoW-Label
        ↓
        ├── MUST/SHOULD → kommt in den Pool für das nächste Release
        ├── COULD       → bleibt offen, kein fester Termin
        └── WON'T       → wird mit Begründung geschlossen
        ↓
Issue wird einem Release Milestone zugeordnet
        ↓
Umsetzung durch Maintainer (oder Pull Request aus der Community)
        ↓
Issue wird geschlossen
```

### Verhalten als Contributor

Wer einen Issue öffnet, sollte ihn so präzise wie möglich beschreiben. Für Bug Reports gilt: Reproduktionsschritte, erwartetes Verhalten und tatsächliches Verhalten angeben. Der Maintainer entscheidet, ob und wann der Issue umgesetzt wird – ein Anspruch auf Umsetzung besteht nicht.

Pull Requests sind willkommen, sollten aber vorher mit einem Issue abgestimmt sein, um doppelte Arbeit zu vermeiden.

---

## Releases

Hauskeeping veröffentlicht Releases **ohne festes Zeitfenster**. Es gibt kein „Release every two weeks" oder ähnliche Rhythmen. Stattdessen sammelt der Maintainer Issues, bis ein sinnvoller Release-Umfang zusammengekommen ist.

### Ablauf eines Releases

1. Der Maintainer erstellt einen **GitHub Milestone** mit einem Zieldatum
2. Issues mit MUST- und SHOULD-Priorität werden dem Milestone zugeordnet
3. Der Maintainer arbeitet die Issues ab
4. Wenn alle Milestone-Issues erledigt sind, wird der Release erstellt und getaggt
5. Ein Changelog wird mit dem Release veröffentlicht

### Zieldatum

Das Zieldatum eines Milestones ist ein **angestrebter Termin**, kein harter Deadline. Wenn Issues komplexer werden als erwartet, verschiebt sich das Datum. Das ist im Rahmen eines Solo-Open-Source-Projekts normal und akzeptiert.

### Versionierung

Hauskeeping folgt **Semantic Versioning (SemVer)**:

| Teil | Bedeutung | Beispiel |
|---|---|---|
| **MAJOR** | Breaking Changes, große Umstrukturierungen | `2.0.0` |
| **MINOR** | Neue Features, rückwärtskompatibel | `1.3.0` |
| **PATCH** | Bugfixes, kleine Anpassungen | `1.3.1` |

---

## Kurzübersicht

| Thema | Vorgehen |
|---|---|
| Priorisierungsmodell | MoSCoW (MUST / SHOULD / COULD / WON'T) |
| Feature- & Bug-Meldungen | GitHub Issues |
| Priorisierungsentscheidung | Maintainer (@iLollek) |
| Release-Rhythmus | Kein fester Rhythmus – Milestone mit Zieldatum |
| Versionierung | Semantic Versioning (SemVer) |
| Externe Contributor | Willkommen via Pull Request, vorher Issue abstimmen |