# Alternativas ao Piper + Notebook

> Este documento descreve as alternativas à abordagem principal (Piper no notebook).  
> Leia primeiro [visao-geral.md](./visao-geral.md) para entender por que o Piper é a recomendação principal.

Cada alternativa abaixo existe para um cenário específico. Nenhuma supera o Piper em qualidade de voz — as alternativas existem quando a dependência do notebook não é aceitável.

---

## Alternativa 1 — Áudio pré-gravado em flash ou cartão SD

### Como funciona

As frases são geradas com o Piper no escritório (com toda a qualidade neural), convertidas para WAV, e armazenadas no cartão SD do próprio Simova Track (que já existe no hardware). Em campo, o firmware toca o arquivo correspondente ao evento.

O hardware de reprodução é **exatamente o mesmo** da abordagem Piper — MAX98357A + alto-falante. A única diferença é a origem do áudio: em vez de vir do notebook pela rede, vem do SD card local.

```
[Escritório — uma vez]
Piper → frases.wav → copiar para o SD card

[Campo — sempre]
ESP32 lê o WAV do SD card → MAX98357A → alto-falante
(sem notebook, sem rede, sem processamento)
```

### Quando usar

- O vocabulário do produto é pequeno e estável (10–30 frases)
- As frases raramente mudam (ou mudanças aceitam atualização via OTA/SD)
- Custo mínimo de BOM é prioritário
- Operação standalone é obrigatória

### Prós e contras

| | |
|---|---|
| ✓ | Qualidade de voz máxima (gerado com Piper) |
| ✓ | Custo baixo (~R$35–50 por unidade — MAX98357A + speaker) |
| ✓ | Standalone — não depende de notebook em campo |
| ✓ | Simples de implementar e manter |
| ✗ | Não é síntese ao vivo — frases fixas apenas |
| ✗ | Cada nova frase exige atualização do SD/firmware |

### Hardware necessário

| Componente | Custo estimado |
|---|---|
| MAX98357A | ~R$20 — [AutoCore](https://www.autocorerobotica.com.br/modulo-amplificador-de-audio-i2s-max98357) / [SmartKits](https://www.smartkits.com.br/modulo-amplificador-de-audio-i2s-max98357) / [Mercado Livre](https://produto.mercadolivre.com.br/MLB-3224512093-amplificador-de-audio-max98357-max98357a-i2s-esp32-raspberry-_JM) |
| Alto-falante 4–8 Ohms | ~R$10–25 — [Mercado Livre](https://lista.mercadolivre.com.br/mini-alto-falante-8-ohms) |
| MAX98357A + speaker (kit) | Opção kit com tudo junto — [Mercado Livre](https://www.mercadolivre.com.br/amplificador-dac-max98357-alto-falante-50mm-4-3w/p/MLB2019741487) |
| SD card | já existe no Simova Track |

---

## Alternativa 2 — eSpeak-NG embarcado diretamente no ESP32

### Como funciona

O eSpeak-NG é um sintetizador de voz baseado em síntese formântica — ele gera a voz a partir de regras matemáticas (não IA). Foi portado para ESP32 por Phil Schatzmann ([arduino-espeak-ng](https://github.com/pschatzmann/arduino-espeak-ng)). Suporta português e cabe na flash do ESP32 com o partition scheme "Huge APP" (~52% de uso).

```
[Campo]
Texto → ESP32 (eSpeak-NG embarcado) → I2S → MAX98357A → alto-falante
(100% standalone, sem notebook, sem rede, sem nada)
```

### Quando usar

- Síntese ao vivo de qualquer texto é obrigatória
- Custo de BOM é crítico — zero componentes extras
- A qualidade robótica da voz é aceitável para o contexto de uso
- Ambiente industrial onde voz natural não é esperada

### Prós e contras

| | |
|---|---|
| ✓ | 100% standalone e offline |
| ✓ | Zero custo extra de hardware |
| ✓ | Síntese ao vivo de qualquer texto |
| ✓ | Suporte real ao português |
| ✗ | Qualidade de voz robótica — sotaque mecânico notável |
| ✗ | Não aprovado para uso com usuários finais sem teste de aceitação |

### Hardware necessário

| Componente | Situação no Simova Track atual |
|---|---|
| ESP32 | já existe |
| MAX98357A | **não existe — precisa ser adicionado** |
| Alto-falante 4–8 Ohms | **não existe — precisa ser adicionado** |

> O Simova Track atual não tem nenhum hardware de áudio além do buzzer piezo (GPIO4). Qualquer abordagem que reproduza áudio real exige adicionar MAX98357A + alto-falante.

---

## Alternativa 3 — Raspberry Pi Zero 2W como co-processador de voz

### Como funciona

Um Raspberry Pi Zero 2W fica integrado ao produto (ou em um hub de campo compartilhado). Ele roda o Piper TTS e expõe uma API local. O ESP32 manda o texto para o RPi via Wi-Fi local ou UART, o RPi gera o áudio e o envia de volta para o ESP32 tocar — ou o RPi tem saída de áudio própria.

```
[Campo]
Texto → ESP32 → RPi Zero 2W (Piper) → áudio → alto-falante
(standalone, qualidade máxima, sem notebook)
```

### Quando usar

- Síntese ao vivo é obrigatória
- Qualidade de voz natural é obrigatória
- Operação standalone é obrigatória (sem notebook)
- O custo extra de ~R$120–200 por unidade é aceitável no BOM

### Prós e contras

| | |
|---|---|
| ✓ | Qualidade de voz idêntica ao Piper no notebook |
| ✓ | Síntese ao vivo de qualquer texto |
| ✓ | 100% standalone e offline |
| ✗ | Custo extra de ~R$405–435 por unidade de produto (RPi ~R$350 + MAX98357A + speaker) |
| ✗ | Maior tamanho físico — precisa de espaço na PCB ou caixa |
| ✗ | Consumo extra de ~1,5W |
| ✗ | Boot de ~20s a frio — requer considerar estratégia de ligar/desligar |
| ✗ | Maior complexidade de firmware e integração |

### Hardware necessário

| Componente | Custo estimado |
|---|---|
| Raspberry Pi Zero 2W | ~R$350 — [Saravati R$354,90](https://www.saravati.com.br/placa-raspberry-pi-zero-2-w-quad-core-64-bit-arm-c-pinos.html) / [Mercado Livre](https://lista.mercadolivre.com.br/raspberry-pi-zero-2w) |
| Cartão microSD (sistema) | ~R$25–40 |
| MAX98357A + speaker | ~R$30–45 (ver links acima) |

---

## Resumo da decisão

```
O produto precisa falar sozinho, sem notebook?
│
├─ NÃO → Piper no notebook (abordagem principal)
│         Qualidade máxima, custo mínimo, pronto para uso.
│
└─ SIM → As frases são fixas ou variam muito?
          │
          ├─ FIXAS (10–30 frases) → Pré-gravado no SD card + MAX98357A
          │   Simples, barato, qualidade ótima. SD card já existe no produto.
          │
          └─ VARIÁVEIS (qualquer texto)
              │
              ├─ Qualidade robótica é aceitável? → eSpeak-NG no ESP32
              │   Zero custo extra, síntese ao vivo.
              │
              └─ Qualidade natural é obrigatória? → RPi Zero 2W + Piper
                  Máxima qualidade, maior custo e complexidade.
```
