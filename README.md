\# Projekt: Kvízová nástěnka s AI



\## Popis

Aplikace slouží k evidenci výsledků kvízu a generování vtipných komentářů pomocí lokálního LLM.



\## Síťové nastavení

\- \*\*IP adresa serveru:\*\* \[Doplňte svou IP, např. 10.10.10.1]

\- \*\*Port aplikace:\*\* 8081 (TCP)

\- \*\*Firewall:\*\* Povolen port 8081 (příkaz: `netsh advfirewall firewall add rule name="KvizAPI" dir=in action=allow protocol=TCP localport=8081`)



\## Endpointy

\- `GET /ping`: Ověření dostupnosti (vrací "pong")

\- `GET /status`: Stav aplikace a autor v JSON

\- `POST /ai`: Generování komentáře k výsledku (vyžaduje JSON `{"score": 10}`)



\## Spuštění

1\. Nainstalujte a spusťte \*\*Ollama\*\* s modelem `llama3.2:1b`.

2\. V adresáři projektu spusťte:

&#x20;  ```bash

&#x20;  docker compose up --build

