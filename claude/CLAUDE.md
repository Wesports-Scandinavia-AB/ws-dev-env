# WeSports utvecklingsmiljö (gemensamt)

Den här filen kommer från `Wesports-Scandinavia-AB/ws-dev-env` och läses in i
allas `~/.claude/CLAUDE.md` med en `@`-rad. Ändra den i repot och pusha, inte
lokalt: en `git pull` i ws-dev-env ger alla samma version.

## Datorn

- Repon ligger under roten i `~/.ws-dev-env.json`, normalt `~/source/repos`.
  Samma sökväg på varje dator, annars hittar Claude inte minnet per projekt.
- Ett nytt program alla behöver läggs i `packages.json` i ws-dev-env, inte bara
  med `winget install` på den egna datorn.
- Innan en dator lämnas eller töms körs `check.ps1` i ws-dev-env. Det som
  listas finns bara på den datorn.

## Hemligheter

- Aldrig i git, OneDrive, mail, Teams eller chatten. Lösenord och nycklar delas
  med `wsg secret`, en engångslänk som krypteras innan den lämnar datorn.
- `.env` och `.dev.vars` ligger utanför git och flyttas för sig.
- En SSH-nyckel per dator. En privat nyckel flyttas aldrig: den nya datorn får
  en egen, och den gamla datorns publika nyckel tas bort från servrarna.

## Kod

- Databasmigrationer namnges `ÅÅÅÅMMDDTTMMSS_namn.sql`, aldrig med löpnummer.
  Löpnummer krockar mellan grenar; en tidsstämpel är unik utan samordning.
- Microsoft 365, Teams och Arena från terminalen: `wsg` (skillen `wsg`).
