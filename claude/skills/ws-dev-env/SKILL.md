---
name: ws-dev-env
description: Sätt upp eller uppdatera en utvecklardator på WeSports med ws-dev-env, och kontrollera att inget går förlorat innan en dator lämnas. Use when the user says "ny dator", "byta dator", "flytta till nya datorn", "sätt upp min dator", "uppdatera dev-miljön", "kan jag tömma datorn", "kolla innan jag lämnar datorn", or wants a program, repo or Claude rule shared with the whole team.
---

# ws-dev-env

Repot `Wesports-Scandinavia-AB/ws-dev-env` beskriver en WeSports-utvecklardator:
program (`packages.json`), repon (`repos.txt`), gemensamma Claude-regler
(`claude/CLAUDE.md`) och skills (`claude/skills/`). Det ligger klonat under
roten i `~/.ws-dev-env.json`, normalt `~/source/repos/ws-dev-env`.

## Byta dator

1. **På den gamla datorn**, kör kontrollen och gå igenom det den listar med
   personen:

   ```
   powershell -ExecutionPolicy Bypass -File <root>\ws-dev-env\check.ps1
   ```

   Gult är sådant som går förlorat: committa och pusha, eller flytta
   hemligheter med `wsg secret`. Blått är påminnelser (minne, SSH-nycklar).
   Säg inte att datorn kan tömmas förrän scriptet avslutas med "Nothing lost".

2. **På den nya datorn**, följ `INSTALL-FOR-CLAUDE.md` i repot.

3. **SSH**: flytta aldrig den privata nyckeln. `bootstrap.ps1` gör en ny och
   skriver ut den publika delen. Den läggs in på servern från den gamla datorn,
   som redan kommer in:

   ```
   ssh <användare>@<server> "echo '<publik nyckel>' >> ~/.ssh/authorized_keys"
   ```

   När den nya fungerar tas den gamla datorns rad bort ur `authorized_keys`.

## Uppdatera

`git pull` i ws-dev-env och sedan `bootstrap.ps1` igen. Det hoppar över allt som
redan finns. `-DryRun` visar vad som skulle hända utan att ändra något.

## Dela något med alla

Ett program, ett repo, en regel eller en skill som hela teamet ska ha läggs i
ws-dev-env, inte bara på den egna datorn. Det som är personligt hör hemma i
personens eget lager (`-Personal owner/repo`, samma upplägg). Lägg aldrig in
hemligheter, tokens eller personliga sökvägar i ws-dev-env.
