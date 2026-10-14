# ws-dev-env

En WeSports-utvecklardator, beskriven i ett repo: vilka program, vilka repon,
vilka gemensamma regler och skills Claude ska ha. En ny dator blir en klon och
ett script, och det någon lägger till får alla med `git pull`.

Enklast: ge Claude Code länken till `INSTALL-FOR-CLAUDE.md` och be den sätta
upp datorn.

```
bootstrap.ps1   ny dator, eller uppdatera en befintlig; går att köra om
check.ps1       innan en dator lämnas: listar det som bara finns på den
packages.json   program, i winget-format (winget export / import)
repos.txt       repon alla klonar
claude/
  CLAUDE.md     gemensamma regler, läses in i allas ~/.claude/CLAUDE.md
  skills/       skills alla får, länkade in i ~/.claude/skills
```

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
