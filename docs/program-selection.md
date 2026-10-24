# Zgjedhja dhe nisja e programeve

Ruhet katalogu ekzistues nga Simply-Fi me 71 programe larjeje, përfshirë Trainers,
Backpacks dhe Duvet & Quilts. Nuk kërkohet cloud dhe nuk zëvendësohen komandat
me protokollin e një modeli tjetër.

1. Zgjidh kategorinë dhe programin.
2. Lexo përshkrimin në shqip, pastaj përshtat temperaturën, centrifugën dhe opsionet.
3. Aktivizo kontrollin nga rrjeti në makinë dhe shtyp Fillo.
4. Shiko gjendjen reale, fazën dhe kohën e mbetur.

Zgjedhja përgatit cilësimet lokalisht; nuk nis larjen. Ndryshimi i programit i
rivendos të gjitha cilësimet, edhe kur programi ndryshon nga filtri i kategorisë.
Pas restart-it rikthehet zgjedhja me vlerat e katalogut; ndryshimet manuale të
parametrave nuk ruhen, që të mos përzihen mes programeve.

`Program default` përdor vlerën e katalogut. Kur ajo mungon, parametri nuk
dërgohet dhe përdoret sjellja e pajisjes. `Cold` dhe `No spin` dërgojnë zero.

## Çfarë raporton makina

`PrNm` dhe `Sel` janë fusha të veçanta. Katalogu ka Trainers (`PrNm=11, Sel=93`),
Backpacks (`PrNm=11, Sel=87`) dhe Duvet & Quilts (`PrNm=11, Sel=47`). Emri nuk
mund të përcaktohet vetëm nga `PrNm`. As fusha `Pr` nuk është automatikisht `PrNm`.

Lista tregon programin e zgjedhur për nisjen e ardhshme. Sensori tregon kodin
e raportuar nga pajisja pa e kthyer në një emër të pasigurt. Atributi
`last_requested_program` është kërkesa e fundit e dërguar me sukses nga butoni
Fillo gjatë këtij sesioni; nuk konfirmon recetën që ekzekuton firmware-i.
`recipe_name_confirmed` mbetet false.

## Kontrolli dhe paneli

Sensori i ri Remote control shfaq nëse makina raporton se pranon komanda.
Start/Pause/Resume/Stop varen edhe nga gjendja e ciklit. Pas komandës butonat
bllokohen për 5 sekonda dhe rifreskohet statusi, sipas qasjes së forku-t
[auanasgheps](https://github.com/auanasgheps/home-assistant-candy).

Shërbimet manuale `candy.*` ruhen për përdoruesit e avancuar. Kufizimet e
butonave nuk zbatohen mbi këto komanda të drejtpërdrejta; mos i përdor
njëkohësisht me komandat nga paneli.

`lovelace/candy_wm_controls.yaml` përdor karta standarde HA. Shtoje si dashboard
manual dhe përshtat ID-të sipas entiteteve të pajisjes. ID-të janë shembuj nga
paneli i mëparshëm; entiteti i ri Remote control mund të ketë prefiks tjetër.
Nuk nevojitet Mushroom. Ruhet identiteti unik i entiteteve ekzistuese.

HA mund të ruajë emra ose kategori të personalizuara në regjistër. Këto mund të
ndryshohen nga cilësimet e entitetit. Instalo degën/versionin e ri dhe rinis HA;
nuk nevojitet heqja dhe rishtimi i integrimit.

## Verifikimi

`python -m unittest discover -s checks -v` verifikon komandat e katalogut,
izolimin e parametrave të 71 programeve, variantet Rapid, zerot dhe shpëlarjen.
`tests/test_program_selection.py` shton kontrolle të selektorëve me HA.
Këto teste nuk provojnë sjelljen e firmware-it fizik.

Duhet provë në pajisje me një ngarkesë të përshtatshme dhe krahasim me Simply-Fi.
Nëse ekzekutohet ende cikël tjetër, duhet verifikuar nëse `Sel` në katalog është
vlerë e pranuar nga modeli. Prania e saj në tabelë nuk e provon këtë.

## Kur Start nuk e nis makinën

Një përgjigje HTTP 200 nga pajisja nuk provon që programi është pranuar.
Butoni Start tani pret rifreskimin e gjendjes dhe deri në dy lexime shtesë.
Komanda Start dërgohet vetëm një herë; leximet nuk provojnë programe të tjera.
Nëse makina mbetet Ready, shfaqet gabimi "Start was sent, but the machine did
not confirm..." dhe sensori i ri Rezultati i nisjes raporton "Nisja nuk u
konfirmua". Nëse makina nis një cikël, kjo shënohet si aktivitet i konfirmuar,
por identiteti i recetës mbetet i paverifikuar.

Për rastin Trainers 20°C / 400 rpm kundrejt panelit Ready 40°C / 1000 rpm,
shkarko diagnostikën te Settings > Devices & Services > Candy > menuja e
integrimit > Download diagnostics. Ajo përmban programin e zgjedhur, komandën
e nisjes dhe gjendjen para/pas, pa kredenciale, IP ose çelës enkriptimi.
Kjo mjafton për të vazhduar analizën pa video. Diagnostika nuk ruhet përtej
restart-it dhe nuk mund të rikrijojë kërkesa të kryera para këtij versioni.

Historiku i repository-t tregon se programet e gatshme u importuan nga katalogu
duke përdorur `parent` si `PrNm`, dhe pozicioni u shtua më vonë si `Sel`.
Repository auanasgheps përdor të dhënat e modelit për lidhjen me programin bazë
dhe një `RecipeId` për programet e gatshme. Këto formate nuk mund të trajtohen
si të barabarta vetëm nga emri Trainers ose nga fotografia e panelit.
Ky rishikim nuk ndryshon numrat e programeve ose formatin e komandës me hamendje.
