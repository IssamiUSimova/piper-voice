# CLAUDE.md

Este arquivo orienta o Claude Code (ou qualquer IA assistente) a entender o estado, o objetivo e as decisões de arquitetura deste projeto antes de continuar o desenvolvimento.

## O que é este projeto

Protótipo de **voz on-device para o Simova Track**, um dispositivo de telemetria veicular baseado em ESP32, instalado em máquinas pesadas (tratores, caminhões, forwarders). O objetivo é fazer o próprio dispositivo falar frases em português — alertas, status operacional, confirmações — sem depender de internet e sem depender do celular do operador.

### Contexto: o TTS já existe, mas não é no ESP32

O firmware atual do Simova Track já tem um mecanismo chamado `sendTextToSpeech()`, mas ele **não reproduz áudio no dispositivo**. Ele apenas envia o texto via BLE para o celular pareado, e quem fala é o app no telefone. O único "áudio" físico embarcado hoje é um buzzer piezo (GPIO4) que toca bips simples.

Este repositório investiga como fazer o próprio ESP32 reproduzir voz — eliminando a dependência do celular para os avisos de voz.

Este repositório implementa **a ponte entre o Piper (rodando no notebook do técnico) e o ESP32 (que toca o áudio no alto-falante via I2S)**, conectados por uma rede Wi-Fi local criada pelo próprio ESP32 (modo SoftAP), sem necessidade de roteador ou internet em campo.

## Origem / motivação (card original)

Card: "Investigar solução de voz offline para ESP32 (track v2)"

- **O que:** Investigar solução de voz 100% offline para ESP32 — TTS + hardware de áudio
- **Por que:** Pedido do Fabio para avaliar viabilidade de voz on-device no track v2 — hoje a voz depende do celular via BLE; a ideia é que o próprio dispositivo fale, possivelmente integrado com um leitor de cartão no v2
- **Quem:** Italo
- **Itens originais do card:**
  - Pesquisar alto-falante disponível na JLCPCB (tensão, impedância, tamanho compatível com o track)
  - Estudar I2S: pinos no ESP32, amplificadores compatíveis (ex: MAX98357A)
  - Avaliar esp32-flite (https://github.com/alkhimey/esp32-flite) — qualidade, RAM/flash consumido
  - Levantar alternativas TTS 100% offline (ESP-SR da Espressif, pico2wave port, áudio pré-gravado em flash como fallback)
  - Definir abordagem final: TTS em tempo real vs samples pré-gravados
  - Prototipar integração com leitor de cartão no track v2

## Decisões tomadas após a investigação

Foram avaliadas duas rotas de TTS offline:

1. **eSpeak-NG compilado diretamente no ESP32** (projeto `arduino-espeak-ng` de Phil Schatzmann)
   - Síntese 100% standalone, sem depender de nenhum outro dispositivo
   - Suporta português, cabe na flash do ESP32 (~52% de uso com config mínima, partition scheme "Huge APP")
   - Qualidade de voz robótica (formant synthesis), aceitável para avisos curtos
   - **Status: guardada como alternativa viável, mas não é o foco deste repositório.** Se este repo (Piper+ESP32) não atingir a qualidade/latência desejada, cair para essa rota é o plano B.

2. **Piper TTS rodando no notebook do técnico + ESP32 só toca o áudio** ← **é o que este repositório implementa**
   - Piper é uma engine de TTS neural (VITS exportado para ONNX), leve o suficiente para rodar em tempo real até em Raspberry Pi, então roda folgado em qualquer notebook
   - Uma vez os modelos de voz baixados (precisa de internet só nesse passo único, feito no escritório), o Piper funciona 100% offline
   - Qualidade de voz muito superior ao eSpeak-NG (voz neural, natural, não robótica)
   - O ESP32 não precisa processar TTS — só recebe áudio já sintetizado e toca via I2S
   - Reaproveita o padrão de rede já usado por outro produto da empresa (aparelho irmão do Simova Track, mesma placa/componentes, que já cria uma rede Wi-Fi própria e expõe uma interface web offline)

**Por que essa rota foi escolhida como prioridade:** menor esforço de engenharia (reaproveita servidor HTTP e I2S que já existem no firmware atual do Simova Track), melhor qualidade de voz, e o técnico já carrega notebook em campo — não é uma dependência nova.

## Arquitetura

```
┌─────────────────────┐         Wi-Fi local          ┌──────────────────────┐
│   Notebook técnico   │  (rede criada pelo ESP32,    │        ESP32         │
│                      │   SoftAP, sem internet)      │                      │
│  1. Texto → Piper    │ ────────────────────────────>│  3. Recebe áudio     │
│  2. Gera WAV/PCM     │      HTTP POST (ou stream)   │     via HTTP/socket  │
│                      │                               │  4. Toca via I2S     │
└─────────────────────┘                               │     (MAX98357A +     │
                                                        │      alto-falante)   │
                                                        └──────────────────────┘
```

Fluxo:
1. ESP32 sobe em modo **SoftAP** (`WiFi.softAP()`), criando uma rede própria — igual ao aparelho irmão que já faz isso para a interface web.
2. ESP32 sobe um servidor HTTP (reaproveitando a base que já existe no firmware do Simova Track, que hoje tem um endpoint `/say` que recebe texto e sintetiza localmente com Flite).
3. Notebook conecta nessa rede.
4. No notebook, um script/serviço recebe um texto, gera o áudio com Piper (modelo de voz PT-BR), e envia esse áudio (WAV completo via POST, ou PCM em streaming) para o ESP32.
5. ESP32 recebe os bytes de áudio e toca direto no I2S, reaproveitando a lógica existente em `i2s_stream_chunk()` do `main.c` original — só que agora os dados vêm da rede em vez de virem do Flite local.

### Duas formas de envio de áudio (a decidir/testar)

- **Mais simples (recomendado para o protótipo inicial):** Piper gera o WAV completo, notebook faz um `POST` HTTP do arquivo pronto para o ESP32, que recebe e toca. Latência de início maior (espera gerar tudo antes de mandar), mas muito mais fácil de implementar e debugar.
- **Mais responsiva (otimização futura):** streaming de PCM bruto via TCP/UDP, ESP32 toca conforme os bytes chegam — mais parecido com o que o Flite fazia originalmente, mas com a fonte de áudio vindo da rede.

Comece pela abordagem simples (WAV completo via HTTP) e só evolua para streaming se a latência for um problema real.

## Hardware de referência

- **MCU:** ESP32 (mesma placa/componentes do Simova Track / aparelho irmão)
- **Amplificador de áudio:** MAX98357A (I2S, classe D, 3W) — já validado em projetos similares, compatível com ESP32 e Raspberry Pi
- **Alto-falante:** 4-8 Ohms, compatível com o footprint do MAX98357A
- **Pinos I2S de referência** (do firmware original, configuráveis via Kconfig):
  - BCK (Bit Clock): GPIO 26
  - WS (Word Select / LRCK): GPIO 25
  - DATA: GPIO 22

Esses pinos e o módulo de amplificador já estão validados no firmware base (`esp32-flite`) que deu origem a este projeto — reaproveitar a mesma config de I2S.

### Restrição de pinos no hardware atual do Simova Track

O hardware atual (v1.6.0) tem apenas **GPIO23 e GPIO33 livres como saída**. Um barramento I2S completo precisa de 3 pinos de saída (BCLK, WS, DOUT). Isso significa que adicionar I2S no hardware atual exigirá ou:
- Liberar um pino ocupado (ex: GPIO32/Input4, se aquela entrada não for usada na aplicação alvo), ou
- Uma revisão de hardware no v2 (já previsto, já que o v2 é o alvo desta investigação).

Para o protótipo com hardware de desenvolvimento (não a PCB do Simova Track), os pinos de referência do `esp32-flite` (BCK=26, WS=25, DATA=22) funcionam normalmente.

## Estado atual do projeto

**Repositório vazio — desenvolvimento ainda não começou.** Este CLAUDE.md documenta o plano antes do código existir.

## Plano de implementação (fases)

### Fase 1 — Validar o Piper sozinho no notebook (sem ESP32)
- Instalar Piper (`pip install piper-tts`)
- Baixar modelo(s) de voz PT-BR
- Gerar áudios de teste com frases reais do produto (ex: "Cartão não reconhecido", "Acesso liberado")
- Critério de sucesso: qualidade de voz aprovada pela equipe

### Fase 2 — ESP32 em modo SoftAP
- Adaptar o firmware (`main.c` do `esp32-flite` como ponto de partida) trocando `WiFi.begin()` (modo estação) por `WiFi.softAP()`
- Manter o servidor HTTP existente rodando na rede própria
- Critério de sucesso: notebook consegue conectar na rede do ESP32 e acessar seu IP (geralmente `192.168.4.1`)

### Fase 3 — Tocar um áudio fixo enviado pelo notebook
- Notebook envia um WAV qualquer (não precisa ser do Piper ainda) via HTTP POST para o ESP32
- Firmware recebe os bytes e toca via I2S (adaptar `i2s_stream_chunk()` existente)
- Critério de sucesso: áudio sai no alto-falante, vindo da rede

### Fase 4 — Fluxo completo: texto → Piper → ESP32 fala
- Script no notebook: recebe texto → gera áudio com Piper → envia para o ESP32
- Testar latência (tempo entre "texto digitado" e "som sai no alto-falante")
- Testar com frases curtas e longas
- Testar alcance físico da rede SoftAP
- Critério de sucesso: fluxo completo funcionando, ponta a ponta, offline

### Fase 5 — Teste de campo simulado
- Testar com interferência de outras redes Wi-Fi por perto
- Testar reconexão do notebook após reiniciar o ESP32
- Medir consumo de energia/bateria do ESP32 durante reprodução de áudio
- Levantar lista de frases padrão do produto para já deixar testadas

## Decisões em aberto / perguntas para revisitar

- Qual formato de transporte de áudio usar primeiro: WAV completo via HTTP POST, ou streaming PCM via socket?
- O ESP32 deve ficar em modo SoftAP puro, ou modo dual (AP + STA), permitindo também conectar a uma rede existente quando disponível?
- Qual(is) modelo(s) de voz Piper em PT-BR usar (qualidade vs tamanho do modelo)?
- Vale a pena ter uma lista fixa de frases pré-geradas em cache no notebook, para reduzir latência de frases repetidas (ex: "Acesso liberado")?
- Autenticação/segurança da rede SoftAP do Simova Track (mesmo padrão do aparelho irmão, a definir com o time)?

## Alternativa de fallback (não esquecer)

Se a abordagem Piper + notebook não atingir os requisitos de latência ou usabilidade em campo, a alternativa validada é compilar o **arduino-espeak-ng diretamente no ESP32** — síntese standalone, sem depender de notebook, com qualidade de voz mais robótica mas suporte a português e funcionando 100% dentro do dispositivo. Essa rota está documentada separadamente e não faz parte do escopo deste repositório, mas deve ser considerada caso este protótipo não avance.

## Referências técnicas

- Firmware base de referência (Flite no ESP32): https://github.com/alkhimey/esp32-flite
- eSpeak-NG portado para Arduino/ESP32 (rota alternativa/fallback): https://github.com/pschatzmann/arduino-espeak-ng
- Piper TTS: https://github.com/rhasspy/piper (desenvolvimento atual em https://github.com/OHF-Voice/piper1-gpl)
- Vozes Piper (incluindo PT-BR): https://github.com/rhasspy/piper/blob/master/VOICES.md (ou Hugging Face, repositório `rhasspy/piper-voices`)
- Biblioteca de áudio I2S para ESP32 (tocar streams/arquivos recebidos via rede): https://github.com/schreibfaul1/ESP32-audioI2S
- Amplificador de referência: MAX98357A (I2S, classe D)

## Convenções para quem for codar aqui

- Priorizar a abordagem mais simples primeiro (WAV completo via HTTP) antes de otimizar para streaming.
- Reaproveitar ao máximo a base de código do `esp32-flite` (estrutura de projeto ESP-IDF, configuração I2S, Kconfig) — não reinventar a configuração de hardware que já foi validada.
- Manter o código do notebook (lado Piper) e o firmware do ESP32 em pastas separadas dentro deste repo (sugestão: `/notebook` ou `/server` e `/firmware` ou `/esp32`).
- Documentar no README.md os passos de setup de cada lado (notebook e firmware) conforme forem implementados.