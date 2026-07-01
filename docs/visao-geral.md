# Voz On-Device para o Simova Track v2 — Visão Geral

> **Para quem é este documento:** Italo, Fabio, e qualquer pessoa que queira entender rapidamente as opções de voz offline para o Simova Track antes de tomar uma decisão técnica ou de produto.

---

## O que é o Simova Track

O Simova Track é um dispositivo de **telemetria veicular** instalado em máquinas pesadas — tratores, caminhões, forwarders florestais, motoniveladoras. Ele monitora GPS, dados do motor via CAN bus, vibração, entradas digitais, e transmite tudo via BLE/Wi-Fi para o servidor da Simova.

O firmware já tem um mecanismo chamado `sendTextToSpeech()` — mas ele **não reproduz áudio no dispositivo**. Ele envia o texto via BLE para o celular do operador, e quem fala é o app no telefone. O único áudio físico embarcado hoje é um **buzzer piezo** (GPIO4) que toca bips simples de erro/sucesso.

---

## O problema

O operador da máquina nem sempre tem o celular pareado e na mão. O objetivo do v2 é fazer o **próprio dispositivo falar** — sem depender do celular — para avisos como:

- *"Velocidade excessiva"*
- *"Motor em temperatura crítica"*
- *"Ignição desligada"*
- *"Acesso liberado"* (se leitor de cartão for integrado no v2)

---

## Recomendação: Piper TTS no notebook do técnico

Após avaliar todas as alternativas, a abordagem mais viável para o protótipo combina qualidade de voz, custo e simplicidade:

```
Notebook do técnico
    │  (Piper gera o áudio — voz neural, PT-BR, offline)
    │
    ▼  Wi-Fi própria do ESP32 (SoftAP — sem roteador, sem internet)
    │
ESP32 do Simova Track
    │  (recebe o áudio pronto e toca no alto-falante)
    ▼
MAX98357A → Alto-falante
```

**Por que essa abordagem vence as alternativas para o protótipo:**

| Critério | Piper + notebook |
|---|---|
| Qualidade de voz | Voz neural natural em PT-BR — a melhor possível |
| Síntese ao vivo | Qualquer texto, gerado na hora |
| Offline | 100% — modelo baixado uma única vez com internet |
| Custo extra no produto | ~US$1–3 (MAX98357A + speaker) |
| Complexidade | Baixa — ESP32 só toca áudio, não processa linguagem |
| Dependência | Notebook do técnico (que já carrega em campo) |

> O ESP32 não precisa "entender" nenhum idioma. Ele recebe bytes de áudio já prontos e envia ao amplificador via I2S — o suporte ao português está 100% no Piper, no notebook.

---

## Comparativo rápido com as alternativas

| Abordagem | Qualidade PT-BR | Síntese ao vivo | Custo extra/unidade | Standalone |
|---|---|---|---|---|
| **Piper + notebook** ← recomendado | ★★★★★ | ✓ | ~US$1–3 | ✗ requer notebook |
| Pré-gravado em flash/SD | ★★★★★ | ✗ frases fixas | ~US$1–3 | ✓ |
| eSpeak-NG no ESP32 | ★★☆☆☆ robótico | ✓ | US$0 | ✓ |
| RPi Zero 2W + Piper | ★★★★★ | ✓ | ~US$15–35 | ✓ |

Para detalhes completos de cada alternativa, veja [alternativas.md](./alternativas.md).  
Para detalhes técnicos do Piper, veja [piper-notebook.md](./piper-notebook.md).

---

## Restrição de hardware no Simova Track atual

O hardware atual (v1.6.0) tem apenas **GPIO23 e GPIO33 livres como saídas**. Um barramento I2S completo precisa de 3 pinos de saída (BCLK, WS, DOUT). Isso significa que **adicionar I2S na PCB atual exige uma revisão de hardware** — o que é esperado, já que o alvo é o v2. Para o protótipo, qualquer placa ESP32 de desenvolvimento funciona com os pinos de referência (BCK=26, WS=25, DATA=22).

---

## A pergunta decisiva para a arquitetura final

> **O dispositivo precisa falar sozinho, sem ninguém por perto com notebook?**

- **Não** (técnico sempre presente) → Piper no notebook é a escolha certa. Siga em frente.
- **Sim** (falar sozinho, standalone) → veja [alternativas.md](./alternativas.md).

---

## Estado atual do projeto

- [x] Piper instalado e validado no notebook — qualidade de voz aprovada
- [ ] Firmware ESP32: modo SoftAP + servidor HTTP
- [ ] ESP32 recebe WAV e toca via I2S
- [ ] Fluxo completo ponta a ponta
- [ ] Testes de campo

---

*Investigação iniciada a pedido do Fabio. Desenvolvimento: Italo.*
