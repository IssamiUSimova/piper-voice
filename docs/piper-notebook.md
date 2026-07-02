# Piper TTS + Notebook — Abordagem Principal

> Este documento detalha a abordagem recomendada para voz offline no Simova Track v2.  
> Para o comparativo com alternativas, veja [alternativas.md](./alternativas.md).

---

## O que é o Piper

O Piper é um sistema de síntese de voz por inteligência artificial desenvolvido pela comunidade Rhasspy. Ele usa a arquitetura **VITS** (um modelo de rede neural treinado para soar como uma voz humana) exportado para o formato ONNX, o que permite rodar em tempo real mesmo em hardware modesto — notebooks, Raspberry Pi, e similares.

**Não é um LLM** (como o ChatGPT). O Piper não "pensa" nem gera texto — ele recebe texto pronto e converte para áudio. É um modelo especializado e leve, focado exclusivamente em síntese de voz.

### Por que o Piper e não outros TTS

| TTS | Qualidade em PT-BR | Offline | Custo |
|---|---|---|---|
| **Piper** | ★★★★★ — voz neural natural | ✓ 100% | Gratuito |
| eSpeak-NG | ★★☆☆☆ — robótico | ✓ | Gratuito |
| Google TTS | ★★★★★ | ✗ (requer internet) | Pago por uso |
| ElevenLabs / similares | ★★★★★ | ✗ (requer internet) | Pago por uso |

O Piper é o único que combina qualidade de voz natural, funcionamento 100% offline e custo zero.

---

## Como funciona a arquitetura completa

```
┌─────────────────────────────────────────┐
│           Notebook do técnico            │
│                                          │
│  1. Texto de entrada                     │
│         ↓                                │
│  2. Piper TTS (modelo PT-BR, offline)    │
│         ↓                                │
│  3. Arquivo WAV gerado em memória        │
│         ↓                                │
│  4. HTTP POST → Wi-Fi do ESP32           │
└─────────────────────────────────────────┘
              ↓ (rede Wi-Fi SoftAP)
┌─────────────────────────────────────────┐
│              ESP32                       │
│                                          │
│  5. Recebe o WAV via HTTP                │
│         ↓                                │
│  6. Envia bytes para I2S                 │
│         ↓                                │
│  7. MAX98357A amplifica                  │
│         ↓                                │
│  8. Alto-falante reproduz                │
└─────────────────────────────────────────┘
```

### Detalhes de cada etapa

**Etapa 1–3 (notebook):** O Piper recebe qualquer texto e gera um arquivo WAV com a voz sintetizada. Isso acontece inteiramente no notebook, sem internet, em ~0,5–2 segundos para frases curtas.

**Etapa 4 (envio):** O notebook envia o WAV via HTTP POST para o IP do ESP32 na rede local (tipicamente `192.168.4.1`). A rede é criada pelo próprio ESP32 em modo SoftAP — sem roteador, sem internet.

**Etapa 5–8 (ESP32):** O ESP32 recebe os bytes do WAV e os passa diretamente para o barramento I2S. O MAX98357A converte o sinal digital em analógico e amplifica para o alto-falante. O ESP32 não processa nenhuma linguagem — é idêntico a qualquer reprodutor de áudio.

---

## Por que o ESP32 não faz o TTS sozinho

Essa é uma dúvida comum. O ESP32 é excelente para Wi-Fi, Bluetooth e controle de hardware — mas não tem os recursos necessários para um modelo de voz neural:

| Recurso | ESP32 tem | TTS neural precisa |
|---|---|---|
| RAM | ~520 KB | ~32 MB+ (para carregar o modelo) |
| Flash | 4–16 MB | ~60–200 MB (modelo + engine) |
| CPU | 240 MHz, sem aceleração tensorial | ~1 GHz+ para inferência em tempo real |

Resultado prático: mesmo que coubesse na flash (não cabe), a síntese de uma frase simples levaria dezenas de segundos — inutilizável.

> O ESP32-S3 tem melhorias (PSRAM externo, extensões vetoriais), mas ainda não resolve o problema de memória e velocidade para modelos VITS/ONNX de qualidade.

---

## Modelo de voz utilizado

**`pt_BR-faber-medium`** — masculino, qualidade boa, ~63 MB.

Outros modelos disponíveis em PT-BR no repositório Piper (Hugging Face `rhasspy/piper-voices`):

| Modelo | Voz | Tamanho | Qualidade |
|---|---|---|---|
| `pt_BR-faber-medium` | Masculino | ~63 MB | ★★★★☆ |
| `pt_BR-cadu-medium` | Masculino | ~63 MB | ★★★★☆ |
| `pt_BR-edresson-low` | Masculino | ~29 MB | ★★★☆☆ |

O modelo é baixado uma única vez com internet (no escritório). Em campo, o notebook funciona 100% offline.

---

## Casos de uso reais no Simova Track

O firmware atual já usa `sendTextToSpeech()` para avisar o operador — mas hoje isso vai via BLE para o celular. Com voz on-device, esses mesmos eventos passariam a ser falados pelo próprio dispositivo:

| Evento no firmware | Mensagem de voz |
|---|---|
| Velocidade acima do limite | *"Velocidade excessiva"* |
| Mudança de estado operacional | *"Máquina em operação produtiva"* |
| Ignição ligada/desligada | *"Ignição ligada"* |
| Erro de GPS | *"Sinal de GPS perdido"* |
| Erro de cartão SD | *"Erro no cartão de memória"* |
| CAN bus ativo/inativo | *"Comunicação CAN ativa"* |
| (v2) Leitor de cartão | *"Acesso liberado"* / *"Cartão não reconhecido"* |

Na produção, esses avisos seriam disparados automaticamente pelo firmware — não por um humano digitando texto.

## O que já funciona (Fase 1 — concluída)

O script `notebook/say.py` já está operacional:

```bash
# Gerar todas as frases de teste do produto
.\run.bat                          # Windows
./run.sh                           # Linux / macOS

# Gerar uma frase específica
.\run.bat "Velocidade excessiva"
.\run.bat "Acesso liberado" --output acesso.wav
```

Frases geradas e validadas:
- "Atenção! Velocidade máxima excedida."
- "Velocidade normalizada."
- "Máquina em operação produtiva."
- "Máquina em estado alternativo."
- "Máquina parada."
- "Máquina em trânsito."
- "Ignição ligada."
- "Ignição desligada."
- "Sinal de GPS perdido."
- "Erro no cartão de memória."
- "Comunicação CAN inativa."
- "Comunicação CAN ativa."
- "Acesso liberado." *(v2 — leitor de cartão)*
- "Cartão não reconhecido." *(v2)*
- "Acesso negado." *(v2)*

---

---

## Requisitos de hardware

| Componente | Função | Custo estimado (volume) |
|---|---|---|
| ESP32 | Rede Wi-Fi + servidor HTTP + I2S | já no produto |
| MAX98357A | Amplificador I2S classe D, 3W | ~R$20 ([AutoCore](https://www.autocorerobotica.com.br/modulo-amplificador-de-audio-i2s-max98357) / [SmartKits](https://www.smartkits.com.br/modulo-amplificador-de-audio-i2s-max98357) / [Mercado Livre](https://produto.mercadolivre.com.br/MLB-3224512093-amplificador-de-audio-max98357-max98357a-i2s-esp32-raspberry-_JM)) |
| Alto-falante 4–8 Ohms | Reprodução | ~R$10–25 ([Mercado Livre](https://lista.mercadolivre.com.br/mini-alto-falante-8-ohms)) |
| MAX98357A + speaker (kit) | Amplificador + alto-falante 50mm 4Ω já juntos | [Mercado Livre](https://www.mercadolivre.com.br/amplificador-dac-max98357-alto-falante-50mm-4-3w/p/MLB2019741487) |
| Notebook do técnico | Rodar o Piper TTS | já existe em campo |

**Custo extra por unidade de produto: ~R$30–45.**

### Atenção: restrição de pinos no hardware v1.6.0

O hardware atual do Simova Track tem apenas **GPIO23 e GPIO33 livres como saídas**. I2S precisa de 3 pinos de saída (BCLK, WS, DOUT) — um a mais do que o disponível. Isso exige revisão de hardware no v2, o que já é esperado. Para o protótipo em placa de desenvolvimento ESP32 genérica, use os pinos de referência: **BCK=GPIO26, WS=GPIO25, DATA=GPIO22**.

---

## Requisitos de software (notebook)

- Python 3.9+
- `piper-tts` (instalado automaticamente pelo `run.bat` / `run.sh`)
- Modelo de voz PT-BR (baixado automaticamente na primeira execução)

---

## Limitações conhecidas

- **Requer notebook próximo:** o técnico precisa estar com o notebook quando o dispositivo precisar falar. Se o dispositivo precisar operar sozinho, veja [alternativas.md](./alternativas.md).
- **Latência de ~1–3s:** tempo entre enviar o texto e o áudio sair no alto-falante. Aceitável para avisos e confirmações; pode ser indesejável para feedback muito imediato.
- **Alcance da rede SoftAP:** típico de Wi-Fi (~20–50m em linha de vista). A ser medido nos testes de campo.
