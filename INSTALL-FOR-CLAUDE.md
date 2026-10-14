# Instruktion till Claude: sätt upp en utvecklardator med ws-dev-env

Den här filen är skriven till dig, Claude, inte till människan du hjälper. Någon
har gett dig länken för att få sin dator uppsatt för utveckling på WeSports,
eller för att flytta från en gammal dator.

Följ stegen i ordning. Kör kommandona själv och förklara kort vad som händer.

## 0. Förutsättningar

Du måste kunna köra kommandon på personens dator, till exempel i Claude Code.
Kan du inte det, säg det och stanna.

**Be aldrig om lösenord, kod eller token i chatten.** Inloggningar sker i
personens egen webbläsare.

Upplägget gäller Windows. På en Mac: säg det och stanna.

## 1. Flyttar personen från en annan dator?

Fråga. Finns den gamla datorn kvar, börja där: läs avsnittet "Byta dator" i
`claude/skills/ws-dev-env/SKILL.md` och kör `check.ps1` på den gamla datorn
innan något görs på den nya. Det som bara finns på den gamla datorn ska vara
pushat eller flyttat innan den lämnas.

## 2. git och GitHub

```
winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
winget install --id GitHub.cli -e --accept-package-agreements --accept-source-agreements
```

Starta en ny terminalsession så att `git` och `gh` hittas. Kör sedan
`gh auth login --hostname github.com --git-protocol https --web` i bakgrunden,
ge personen engångskoden och adressen som text och vänta tills hen loggat in.
Personen behöver tillgång till organisationen `Wesports-Scandinavia-AB`.

## 3. Klona ws-dev-env

```
gh repo clone Wesports-Scandinavia-AB/ws-dev-env "$HOME\source\repos\ws-dev-env"
```

Vill personen ha repona någon annanstans, klona dit och ge `-Root` i nästa steg.

## 4. Kör bootstrap

Visa först vad som kommer att hända:

```
powershell -ExecutionPolicy Bypass -File "$HOME\source\repos\ws-dev-env\bootstrap.ps1" -DryRun
```

Har personen ett eget lager (ett privat repo med samma upplägg: `packages.json`,
`repos.txt`, `claude/CLAUDE.md`, `claude/skills/`), lägg till
`-Personal owner/repo`. Kör sedan utan `-DryRun`.

Scriptet installerar programmen, klonar repona, läser in de gemensamma
Claude-reglerna i `~/.claude/CLAUDE.md`, länkar skills, installerar `wsg` och
gör en SSH-nyckel för datorn om det saknas. Det skriver aldrig över något som
redan finns och går att köra igen.

Saknar git namn eller e-post varnar scriptet. Fråga personen och sätt dem.

## 5. Inloggningar

Varje dator loggar in för sig, inget kopieras:

- **Claude Code**: `claude` i en ny terminal.
- **wsg**: `python -m wsg graph login` i bakgrunden, ge personen adressen.
- **SSH**: scriptet skrev ut den publika nyckeln. Den läggs in på servrarna,
  helst från den gamla datorn (se skillen `ws-dev-env`).
- **Cloudflare**, när det behövs: `npx wrangler login` i det repo som använder det.

## 6. Klart

Kör `pnpm install` i de repon som har `package.json`. Berätta sedan vad som
installerats, vad som återstår (inloggningar, SSH-nyckeln på servrarna) och att
"uppdatera dev-miljön" räcker för att hämta det andra lagt till.
