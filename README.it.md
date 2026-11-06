# Integrazione Homeray

**I controlli che la dashboard non può fare da sola.** Una piccola integrazione gratuita per Home Assistant che lavora insieme alle [card Homeray](https://github.com/DarkBeccio/homeray-cards). Legge solo i dati di Home Assistant: non invia nulla ai dispositivi né a internet.

🇬🇧 [Read in English](README.md)

## Cosa aggiunge

| | Cosa fa |
| --- | --- |
| **Dispositivi muti** | Trova i dispositivi che risultano disponibili ma non mandano nulla da ore. È così che di solito muore un dispositivo a batteria: resta fermo sull'ultimo valore (spesso "80 %") e non diventa mai non disponibile, quindi la dashboard Manutenzione di Home Assistant non lo vede. |
| **Tutte le batterie** | Sensori in percentuale, sensori binari "scarica" e sensori basso/medio/alto, una riga per dispositivo. Elenca anche il sensore di batteria che ha smesso di rispondere mentre il resto del dispositivo funziona. Telefoni e batterie di accumulo sono esclusi, perché per loro un livello basso è normale. |
| **La rete di casa** | Riconosce tra i tuoi dispositivi router, switch, access point, powerline e server, con il piano e la stanza che hai dato loro in Home Assistant e il sensore Ping che li controlla. La mappa di Homeray Pro lo usa per disegnare la rete senza configurazione. |

### Rispetto alla dashboard Manutenzione di Home Assistant

| | Manutenzione | Homeray |
| --- | --- | --- |
| Dispositivi non disponibili e batterie scariche | ✓ | ✓ |
| Dispositivi morti senza diventare non disponibili | | ✓ |
| Sensori di batteria basso/medio/alto | | ✓ |
| Ignora telefoni e batterie di accumulo | | ✓ |
| Ignora singoli dispositivi (etichetta) | | ✓ |
| Sensori da usare in automazioni e notifiche | | ✓ |

## Installazione

1. HACS → tre puntini (in alto a destra) → **Repository personalizzati** → `https://github.com/DarkBeccio/homeray-integration`, tipo **Integrazione**.
2. Cerca **Homeray** in HACS, **Scarica**, poi riavvia Home Assistant.
3. Impostazioni → Dispositivi e servizi → **Aggiungi integrazione** → **Homeray**.

Serve Home Assistant 2026.1 o successivo.

## Opzioni

Impostazioni → Dispositivi e servizi → Homeray → **Configura**.

| Opzione | Predefinito | Cosa fa |
| --- | --- | --- |
| Muto dopo (ore) | 24 | Per quanto un dispositivo può non mandare nulla prima di essere elencato come muto |
| Dispositivi da controllare | Solo a batteria | Oppure tutti i dispositivi con sensori |
| Batteria scarica sotto (%) | 20 | Soglia per i sensori in percentuale |
| Ignora le batterie ricaricabili | Sì | Esclude telefoni e dispositivi con un sensore di ricarica o di accumulo |
| Etichetta dei dispositivi da ignorare | `fuori_monitoraggio` | La stessa etichetta usata dalla card dei problemi |

Un riavvio fa ripartire il conteggio: Home Assistant non conserva l'ora dell'ultimo messaggio tra un riavvio e l'altro, quindi subito dopo un riavvio nessun dispositivo può risultare muto. L'attributo `ready` dice quando il controllo è attivo.

## Sensori

| Entità | Stato | Attributi |
| --- | --- | --- |
| `sensor.homeray_silent_devices` | Numero di dispositivi muti | `devices` (nome, device_id, ore), `silent_after_hours`, `ready` |
| `sensor.homeray_low_batteries` | Numero di batterie scariche | `batteries` (nome, entity_id, tipo, livello) |

## Mappa di rete

Per i dispositivi che Homeray non riconosce, o per correggerlo, dai al dispositivo un'etichetta: `homeray_router`, `homeray_switch`, `homeray_ap`, `homeray_powerline`, `homeray_powerline_wifi`, `homeray_server` o `homeray_alarm`. `homeray_hide` lo esclude. Piani e stanze vengono da Home Assistant (Impostazioni → Aree, etichette e zone).

Riconosciuti oggi: FRITZ!, UniFi, TP-Link Omada, devolo, ASUS, Netgear, MikroTik, OpenWrt, Keenetic, Huawei LTE, Vodafone Station, Freebox, SFR Box, router UPnP, Synology, QNAP, TrueNAS, Proxmox e l'host di Home Assistant.

## Assistenza

Problemi e idee: [GitHub issues](https://github.com/DarkBeccio/homeray-integration/issues) o support@homeray.app. Se Homeray ti è utile, puoi [offrirmi un caffè](https://paypal.me/AndreaGuarducci1992).

Licenza MIT © 2026 DarkBeccio
