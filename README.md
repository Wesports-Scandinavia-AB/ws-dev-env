# ws-dev-env

En WeSports-utvecklardator, beskriven i ett repo: vilka program, vilka repon,
vilka gemensamma regler och skills Claude ska ha. En ny dator blir en klon och
ett script, och det någon lägger till får alla med `git pull`.

Windows och Mac har varsitt entrypoint (`bootstrap.ps1` respektive
`bootstrap.sh`), men samma lista: `packages.json`, `repos.txt` och `claude/`
är gemensamma för båda, så resultatet är detsamma oavsett dator. Linux har
inget entrypoint ännu.

## Kom igång

Öppna en terminal, klistra in raden för din dator och tryck Enter. Raden
installerar det som behövs för att komma igång (git, GitHub CLI, Claude Code,
Herdr) och startar sedan Claude med uppdraget. Claude gör resten; du loggar
bara in i webbläsaren när den ber om det.

**Ny Windows-dator (PowerShell):**

```powershell
'Git.Git','GitHub.cli','Anthropic.ClaudeCode','Herdr.Herdr.Preview' | % { winget install -e --id $_ --accept-source-agreements --accept-package-agreements }; $env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User'); claude "Det här är min NYA dator. Logga in mig på GitHub, klona Wesports-Scandinavia-AB/ws-dev-env till ~/source/repos/ws-dev-env och följ INSTALL-FOR-CLAUDE.md i repot. Jag är inte utvecklare: kör allt själv och be mig aldrig klistra in kommandon."
```

**Gamla Windows-datorn**, innan du lämnar den:

```powershell
'Git.Git','GitHub.cli','Anthropic.ClaudeCode','Herdr.Herdr.Preview' | % { winget install -e --id $_ --accept-source-agreements --accept-package-agreements }; $env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User'); claude "Jag ska byta dator och det här är den GAMLA. Logga in mig på GitHub, klona Wesports-Scandinavia-AB/ws-dev-env till ~/source/repos/ws-dev-env och följ avsnittet Den gamla datorn i INSTALL-FOR-CLAUDE.md. Jag är inte utvecklare: kör allt själv och fråga innan du ändrar något."
```

**Ny Mac (Terminal):**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; eval "$([ -x /opt/homebrew/bin/brew ] && /opt/homebrew/bin/brew shellenv || /usr/local/bin/brew shellenv)"; brew install git gh herdr; brew install --cask claude-code; claude "Det här är min NYA Mac. Logga in mig på GitHub, klona Wesports-Scandinavia-AB/ws-dev-env till ~/source/repos/ws-dev-env och följ INSTALL-FOR-CLAUDE.md i repot. Jag är inte utvecklare: kör allt själv och be mig aldrig klistra in kommandon."
```

Första gången Claude startar loggar du in på ditt Claude-konto.

## Innehåll

```
bootstrap.ps1   Windows: ny dator, eller uppdatera en befintlig; går att köra om
bootstrap.sh    Mac: samma sak, via Homebrew i stället för winget
check.ps1       Windows, innan en dator lämnas: listar det som bara finns på den
packages.json   program, delat mellan Windows och Mac: ett namn, ett winget-id, ett brew-id
repos.txt       repon alla klonar
claude/
  CLAUDE.md     gemensamma regler, läses in i allas ~/.claude/CLAUDE.md
  skills/       skills alla får, länkade in i ~/.claude/skills
```

Ett paket i `packages.json` som saknar `brew` hoppas över på Mac
(`windows-terminal`, finns bara på Windows). Ett paket utan `winget` hade på
samma sätt hoppats över på Windows, men inget sådant finns ännu. `check.sh`
för Mac finns inte: `check.ps1` är ännu bara Windows.

## Två lager

ws-dev-env är det gemensamma. Det personliga ligger i ett eget privat repo med
samma upplägg, till exempel `erikbulowwesports/dev-env`:

```
packages.json   dina egna program
repos.txt       dina egna repon
claude/
  CLAUDE.md     dina egna regler
  skills/       dina egna skills
```

Ge det en gång med `bootstrap.ps1 -Personal erikbulowwesports/dev-env`. Det
sparas i `~/.ws-dev-env.json` tillsammans med `-Root`, så att nästa körning inte
behöver några argument.

## Det som aldrig ligger här

Hemligheter, tokens, `.env`-filer och SSH-nycklar. Varje dator loggar in för
sig och får en egen SSH-nyckel. Lösenord och nycklar delas med `wsg secret`.

`~/.claude/settings.json` är också personligt: där ligger behörigheterna för
den egna datorn.

## Byta dator

1. Gamla datorn: `check.ps1`. Gult går förlorat om datorn töms, blått är
   påminnelser. Fortsätt först när det står "Nothing lost".
2. Nya datorn: `INSTALL-FOR-CLAUDE.md`, eller klona och kör `bootstrap.ps1`.
3. SSH: lägg in den nya datorns publika nyckel på servrarna från den gamla
   datorn, och ta sedan bort den gamlas.
