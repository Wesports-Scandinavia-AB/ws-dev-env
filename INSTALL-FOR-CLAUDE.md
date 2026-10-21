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

Upplägget gäller Windows och Mac. På Linux: säg det och stanna.

## 1. Vilken plattform, och gammal eller ny dator?

Kör `uname` (Mac/Linux svarar `Darwin`/`Linux`) eller titta efter `$env:OS` på
Windows, om det inte redan är tydligt. Är det Linux: säg det och stanna.

Fråga sedan om det här är datorn personen ska **lämna** eller den **nya**.
Steg 2 och 3 gäller båda. Är det den gamla, gå till "Den gamla datorn" längst
ner i stället för steg 4; på Mac finns där ännu bara Windows-kontrollen
(`check.ps1`), se anmärkningen i det avsnittet.

## 2. git och GitHub

**Windows:**

```
winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
winget install --id GitHub.cli -e --accept-package-agreements --accept-source-agreements
```

Startraden i README:n har oftast redan installerat dem; winget hoppar då över
dem. Läs in PATH igen (se ovan).

**Mac:**

```
brew install git gh
```

Saknas Homebrew helt, installera det först:
`NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`,
läs sedan in det i din egen session med
`eval "$([ -x /opt/homebrew/bin/brew ] && /opt/homebrew/bin/brew shellenv || /usr/local/bin/brew shellenv)"`.

**Båda:** kör sedan `gh auth login --hostname github.com --git-protocol https --web`
i bakgrunden, ge personen engångskoden och adressen som text och vänta tills
hen loggat in. Personen behöver tillgång till organisationen
`Wesports-Scandinavia-AB`.

## 3. Klona ws-dev-env

**Windows:**

```
gh repo clone Wesports-Scandinavia-AB/ws-dev-env "$HOME\source\repos\ws-dev-env"
```

**Mac:**

```
gh repo clone Wesports-Scandinavia-AB/ws-dev-env "$HOME/source/repos/ws-dev-env"
```

Vill personen ha repona någon annanstans, klona dit och ge `-Root`/`--root` i
nästa steg.

## 4. Kör bootstrap

Visa först vad som kommer att hända:

**Windows:**

```
powershell -ExecutionPolicy Bypass -File "$HOME\source\repos\ws-dev-env\bootstrap.ps1" -DryRun
```

**Mac:**

```
bash "$HOME/source/repos/ws-dev-env/bootstrap.sh" --dry-run
```

Har personen ett eget lager (ett privat repo med samma upplägg: `packages.json`,
`repos.txt`, `claude/CLAUDE.md`, `claude/skills/`), lägg till
`-Personal owner/repo` (Windows) eller `--personal owner/repo` (Mac). Kör
sedan utan `-DryRun`/`--dry-run`.

Scriptet installerar programmen, klonar repona, läser in de gemensamma
Claude-reglerna i `~/.claude/CLAUDE.md`, länkar skills, installerar `wsg` och
gör en SSH-nyckel för datorn om det saknas. Det skriver aldrig över något som
redan finns och går att köra igen. På Mac installeras Homebrew och `jq` som
en del av steget om de saknas; det är `bootstrap.sh` självt som behöver dem,
inte listan i `packages.json`.

Saknar git namn eller e-post varnar scriptet. Fråga personen och sätt dem.

## 5. Inloggningar

Varje dator loggar in för sig, inget kopieras:

- **wsg**: `python -m wsg graph login` (Windows) eller `python3 -m wsg graph login`
  (Mac) i bakgrunden, ge personen adressen. Scriptet la `wsg` i PATH, men ditt
  eget fönster startade innan dess, så den fulla formen är det som fungerar
  direkt. I personens nya terminal heter det bara `wsg`.
- **SSH**: scriptet skrev ut den publika nyckeln. Den behövs bara för att
  deploya `wesports-data`. Frågar personen inte själv efter det, säg att
  nyckeln finns och lämna det därvid. Ska personen kunna deploya `wesports-data`,
  läggs nyckeln in på den servern, helst från den gamla datorn (se skillen
  `ws-dev-env`).
- **Cloudflare**, när det behövs: `npx wrangler login` i det repo som använder det.

## 6. Klart

Kör `pnpm install` i de repon som har `package.json`. Berätta sedan vad som
installerats, vad som återstår (inloggningar, och SSH-nyckeln på servern om
personen ska deploya `wesports-data`) och att "uppdatera dev-miljön" räcker
för att hämta det andra lagt till.

## Den gamla datorn

Här installeras ingenting. Målet är att inget går förlorat när datorn lämnas.

1. Kör kontrollen. Ligger repona inte i `~/source/repos`, ge `-Root`:

   ```
   powershell -ExecutionPolicy Bypass -File "$HOME\source\repos\ws-dev-env\check.ps1"
   ```

   Det här finns bara för Windows (`check.ps1`). Är den gamla datorn en Mac,
   gå igenom samma sak för hand: `git status` och `git log --branches --not --remotes`
   i varje repo under `~/source/repos`, leta efter `.env`/`.pem`/`.key`-filer
   som git ignorerar, och notera SSH-nyckeln i `~/.ssh`.

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
