# Instruktion till Claude: sätt upp en utvecklardator med ws-dev-env

Den här filen är skriven till dig, Claude, inte till människan du hjälper. Någon
har gett dig länken för att få sin dator uppsatt för utveckling på WeSports,
eller för att flytta från en gammal dator.

Följ stegen i ordning och förklara kort vad som händer. Personen är inte
nödvändigtvis utvecklare: förklara på vanlig svenska, och fråga innan du
committar, pushar eller tar bort något.

**Kör varje kommando själv.** Be aldrig personen klistra in något i PowerShell
eller en terminal, och be hen inte öppna en ny terminal. Hen ska bara läsa,
logga in i webbläsaren och svara på frågor. Saknas ett program som nyss
installerats, läs in PATH igen i ditt eget anrop:

```
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
```

## 0. Förutsättningar

Du måste kunna köra kommandon på personens dator, till exempel i Claude Code.
Kan du inte det, säg det och stanna.

**Be aldrig om lösenord, kod eller token i chatten.** Inloggningar sker i
personens egen webbläsare.

Upplägget gäller Windows. På en Mac: säg det och stanna.

## 1. Gammal eller ny dator?

Fråga om det här är datorn personen ska **lämna** eller den **nya**. Steg 2 och
3 gäller båda. Är det den gamla, gå sedan till "Den gamla datorn" längst ner i
stället för steg 4.

## 2. git och GitHub

```
winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
winget install --id GitHub.cli -e --accept-package-agreements --accept-source-agreements
```

Startraden i README:n har oftast redan installerat dem; winget hoppar då över
dem. Läs in PATH igen (se ovan). Kör sedan
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

- **wsg**: `python -m wsg graph login` i bakgrunden, ge personen adressen.
- **SSH**: scriptet skrev ut den publika nyckeln. Den läggs in på servrarna,
  helst från den gamla datorn (se skillen `ws-dev-env`).
- **Cloudflare**, när det behövs: `npx wrangler login` i det repo som använder det.

## 6. Klart

Kör `pnpm install` i de repon som har `package.json`. Berätta sedan vad som
installerats, vad som återstår (inloggningar, SSH-nyckeln på servrarna) och att
"uppdatera dev-miljön" räcker för att hämta det andra lagt till.

## Den gamla datorn

Här installeras ingenting. Målet är att inget går förlorat när datorn lämnas.

1. Kör kontrollen. Ligger repona inte i `~/source/repos`, ge `-Root`:

   ```
   powershell -ExecutionPolicy Bypass -File "$HOME\source\repos\ws-dev-env\check.ps1"
   ```

2. Gå igenom det **gula** med personen, en sak i taget, och förklara vad det är:
   - **Inte committat / inte pushat**: visa vad som ändrats och fråga om det ska
     sparas. Ska det det, committa och pusha på en egen gren och berätta vilken.
   - **Filer som ser ut som hemligheter** (`.env`, `.dev.vars`): de flyttas inte
     via git, OneDrive eller mail. Skicka dem till personen själv med
     `python -m wsg secret`, en engångslänk, och be hen öppna den på den nya
     datorn. Saknas wsg, installera det enligt
     https://github.com/Wesports-Scandinavia-AB/wsg-cli/blob/main/INSTALL-FOR-CLAUDE.md
   - **Mappar utan git eller utan remote**: fråga om de behövs. Behövs de, lägg
     dem i ett privat GitHub-repo eller i OneDrive om de inte innehåller hemligheter.
3. Kör kontrollen igen tills den slutar med **"Nothing lost"**. Säg först då att
   datorn kan lämnas.
4. Det **blå** är påminnelser. Claude-minnet per projekt kan kopieras till
   `~/.claude/projects` på den nya datorn om personen vill. SSH-nycklarna
   flyttas inte, se nästa punkt.
5. **SSH**: när den nya datorn har en nyckel (bootstrap skriver ut den publika
   delen) och personen ger dig den raden, lägg in den på servrarna härifrån med
   den gamla nyckeln:

   ```
   ssh <användare>@<server> "echo '<publik nyckel>' >> ~/.ssh/authorized_keys"
   ```

   Användare och server hittar du i `~/.ssh/config` eller `~/.ssh/known_hosts`,
   annars fråga. Be personen testa från den nya datorn, och ta sedan bort den
   gamla datorns rad ur `authorized_keys` på servern.
