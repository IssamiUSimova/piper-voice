# Piper + ESP32 — Voz offline para o Simova Track

Protótipo de **voz offline em português** para o Simova Track, combinando o **Piper TTS** (síntese de voz por IA, rodando em um notebook) com um **ESP32** que recebe o áudio já pronto e o reproduz em campo — sem depender de internet.

## A ideia em uma frase

O notebook do técnico (que ele já carrega em campo) gera a fala com IA usando o Piper, e o ESP32 só recebe esse áudio por uma rede Wi-Fi própria (criada pelo próprio dispositivo, sem roteador) e toca no alto-falante.

## Por que essa abordagem

Rodar um modelo de TTS neural (qualidade de voz natural) diretamente em um microcontrolador como o ESP32 não é viável — esse tipo de modelo precisa de mais poder de processamento (classe Raspberry Pi pra cima). Em vez de comprometer a qualidade da voz com soluções 100% embarcadas (robóticas), aproveitamos que o técnico de campo sempre tem um notebook por perto:

- O **notebook** faz o trabalho pesado (Piper TTS, offline, voz natural em PT-BR)
- O **ESP32** faz só o que ele faz bem: rede Wi-Fi e áudio via I2S

Isso também reaproveita um padrão que a empresa já usa em outro produto (mesma placa/componentes do Simova Track): o dispositivo cria sua própria rede Wi-Fi (modo *Access Point*) para ser acessado offline, sem depender de roteador ou internet no local.

## Arquitetura

```
Notebook do técnico                          ESP32 (Simova Track)
┌─────────────────────┐                      ┌──────────────────────┐
│ texto → Piper TTS     │  Wi-Fi local (AP)    │ recebe áudio via HTTP │
│ gera áudio (WAV)      │ ───────────────────> │ toca via I2S          │
│                       │                      │ (MAX98357A + falante) │
└─────────────────────┘                      └──────────────────────┘
```

1. O ESP32 cria sua própria rede Wi-Fi (SoftAP) — não precisa de roteador nem internet.
2. O notebook conecta nessa rede.
3. Um script no notebook recebe um texto, gera o áudio com o Piper (modelo de voz em português), e envia esse áudio para o ESP32.
4. O ESP32 recebe e toca o áudio direto no alto-falante via I2S.

## Hardware

- ESP32 (mesma placa/componentes do Simova Track)
- Amplificador de áudio I2S **MAX98357A**
- Alto-falante 4-8 Ohms
- Pinos I2S de referência: BCK = GPIO 26, WS = GPIO 25, DATA = GPIO 22

## Status do projeto

🚧 Em desenvolvimento inicial. Veja o [CLAUDE.md](./CLAUDE.md) para o plano técnico completo, decisões de arquitetura e fases de implementação.

## Estrutura do repositório

```
/firmware     → código do ESP32 (ESP-IDF / Arduino)
/notebook     → script(s) que rodam no notebook do técnico (Piper TTS + envio de áudio)
```

> Estrutura ainda sendo montada — este README será atualizado conforme o código for adicionado.

## Como rodar (em construção)

### Lado notebook (Piper)

```bash
pip install piper-tts
# baixar um modelo de voz em português antes de ir a campo (único passo que precisa de internet)
```

Instruções completas de uso do script de geração/envio de áudio serão adicionadas conforme implementadas.

### Lado ESP32 (firmware)

Instruções de build e flash serão adicionadas conforme o firmware for implementado.

## Plano de testes

O desenvolvimento segue fases incrementais (detalhadas no `CLAUDE.md`):

1. Validar a qualidade de voz do Piper em PT-BR, isoladamente
2. ESP32 criando sua própria rede Wi-Fi (SoftAP)
3. ESP32 tocando um áudio fixo recebido pela rede
4. Fluxo completo: texto → Piper → ESP32 fala
5. Teste de campo simulado (interferência, reconexão, consumo de energia)

## Alternativa avaliada (fallback)

Caso esta abordagem não atenda aos requisitos de latência ou praticidade em campo, existe uma alternativa 100% standalone (sem depender de notebook): compilar o **eSpeak-NG** diretamente no ESP32. A qualidade de voz é mais robótica, mas funciona sem nenhum dispositivo auxiliar. Essa rota está documentada no `CLAUDE.md`, mas não é o foco deste repositório.

## Origem do projeto

Este projeto nasceu de uma investigação sobre viabilidade de voz offline para o Simova Track v2 (track com leitor de cartão), a pedido do Fabio. Mais contexto no `CLAUDE.md`.