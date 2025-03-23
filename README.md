Šis web servisas naudodamas Cassandra duomenų bazę leidžia valdyti kanalus, jų narius ir žinutes. 
Suteikiama galimybė kurti kanalus, pridėti žinutes ir narius, gauti informaciją apie kanalus, pašalinti narius ar ištrinti visą duomenų bazę. 
Programoje taip pat įgyvendintos ir duomenų filtravimo funkcijos, pvz., žinučių gavimas pagal autorių ar datą.

## Programos naudojimas:

Vienas iš būdų paleisti programą naudojant Docker Desktop:

* Atsisiųskite ir susidiekite Docker Desktop
* Pasileiskite Docker konteinerį: docker run --name cassandra -d -p 9042:9042 cassandra:latest

Testavimui galima naudoti Postman programą.

## **Operacijos kanalui**
/channels - PUT: sukuriamas naujas kanalas su ID, savininku ir tema. Jei kanalas jau egzistuoja, grąžinama klaida.

/channels/<channelId> - GET: grąžina kanalo informaciją pagal ID (savininkas, tema).

/channels/<channelId> - DELETE: ištrina kanalą pagal ID ir susijusius duomenis.

## **Operacijos žinutėms**

/channels/<channelId>/messages - PUT: pridedama žinutė į kanalą su autoriumi ir tekstu.

/channels/<channelId>/messages - GET: grąžina žinutes pagal filtrus (data ir/ar autorius).

## **Operacijos nariams**

/channels/<channelId>/members - PUT: pridėti narį į kanalą.

/channels/<channelId>/members - GET: grąžina visus kanalo narius.

/channels/<channelId>/members/<memberId> - DELETE: pašalina narį iš kanalo.

## **Papildomos operacijos**

/cleanup - POST: ištrina visus kanalus, žinutes ir narius iš duomenų bazės.
