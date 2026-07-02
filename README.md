# Piper + ESP32 — Voz offline para o Simova Track

Protótipo de **voz on-device em português** para o Simova Track v2, usando o **Piper TTS** (síntese de voz por IA) rodando no notebook do técnico e um **ESP32** que recebe o áudio e reproduz no alto-falante — sem depender de internet.

## Como funciona

```
Notebook do técnico                          ESP32 (Simova Track)
┌──────────────────────┐  Wi-Fi do ESP32     ┌─────────────────────┐
│ texto → Piper TTS    │ ──────────────────> │ recebe áudio (HTTP) │
│ gera áudio (WAV)     │  (sem roteador,     │ toca via I2S        │
│ 100% offline         │   sem internet)     │ (MAX98357A + falante)│
└──────────────────────┘                     └─────────────────────┘
```

O ESP32 não processa nenhuma linguagem — apenas recebe bytes de áudio prontos e envia ao amplificador. O Piper é quem gera a voz, no notebook.

## Offline

| Etapa | Precisa de internet? |
|---|---|
| Instalar dependências (`pip install`) | Sim — uma única vez |
| Baixar o modelo de voz (~63 MB) | Sim — uma única vez |
| Usar em campo | **Não — 100% offline** |

O setup é feito no escritório. Em campo, tudo roda sem conexão.

## Como rodar (lado notebook)

**Windows:**
```bat
cd notebook
.\run.bat
```

**Linux / macOS** (dar permissão uma vez):
```bash
cd notebook
chmod +x run.sh
./run.sh
```

Na **primeira execução**: instala as dependências e baixa o modelo de voz automaticamente.

A partir daí, abre o **modo demo** — você digita qualquer frase e ouve pelo alto-falante do notebook:
```
--- Modo demo Simova Track ---
>>> Velocidade máxima excedida.
>>> Ignição desligada.
>>> (Enter para sair)
```

### Outros modos

```bat
# Gerar e ouvir todas as frases do produto
.\run.bat --list-frases --play

# Sintetizar uma frase e ouvir
.\run.bat "Sinal de GPS perdido." --play

# Salvar em arquivo sem tocar
.\run.bat "Acesso liberado." --output acesso.wav
```

## Estrutura do repositório

```
/notebook     → script do notebook (Piper TTS + demo + envio para ESP32)
/firmware     → firmware do ESP32 (a implementar)
/docs         → documentação técnica e análise de arquitetura
```

## Status

| Fase | Status |
|---|---|
| Fase 1 — Piper no notebook, qualidade de voz validada | ✅ Concluída |
| Fase 2 — Firmware ESP32: SoftAP + servidor HTTP | ⬜ A fazer |
| Fase 3 — ESP32 recebe WAV e toca via I2S | ⬜ A fazer |
| Fase 4 — Fluxo completo ponta a ponta | ⬜ A fazer |
| Fase 5 — Testes de campo | ⬜ A fazer |

## Hardware (para as próximas fases)

| Componente | Função | Preço estimado |
|---|---|---|
| ESP32 (placa de desenvolvimento) | MCU + Wi-Fi + I2S | já disponível |
| [MAX98357A](https://produto.mercadolivre.com.br/MLB-3224512093-amplificador-de-audio-max98357-max98357a-i2s-esp32-raspberry-_JM) | Amplificador I2S classe D, 3W | ~R$20 |
| Mini alto-falante 8 Ohms 40mm | Reprodução de áudio | ~R$10–15 |

> O Simova Track atual não possui hardware de áudio além do buzzer piezo — MAX98357A e alto-falante precisam ser adicionados.

Pinos I2S para o protótipo (placa de dev genérica): BCK = GPIO 26, WS = GPIO 25, DATA = GPIO 22.

## Documentação

- [Visão geral e decisão de arquitetura](./docs/visao-geral.md)
- [Detalhes técnicos do Piper](./docs/piper-notebook.md)
- [Alternativas avaliadas](./docs/alternativas.md)
