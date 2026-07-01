# Simova Track — Resumo Técnico Completo

> Documento gerado a partir da leitura do `CLAUDE.md`, `README.md`, `changelog.md` e de todos os arquivos em `docs/` do repositório `simova-track`. Objetivo: servir de contexto para um novo repositório que adicionará um método de **reprodução de áudio TTS no próprio ESP32** (o Simova Track atual não faz isso — ver seção 5).

---

## 1. O que é o Simova Track

O **Simova Track** é um dispositivo de **telemetria e sensoriamento automotivo/industrial**, desenvolvido pela **Simova Tecnologia e Serviços de Informática LTDA**. É instalado em veículos, caminhões, tratores e outras máquinas pesadas (esteiras, forwarders florestais, basculantes, motoniveladoras, plantadeiras, etc.) para:

- Rastreamento em tempo real via **GPS**.
- Leitura de dados do motor via **CAN bus** (protocolos **J1939** e **OBD2**).
- Detecção de movimento/vibração via **acelerômetro**.
- Leitura de até **4 entradas digitais** de propósito geral (5–45V) — ex: botão de garra de joystick, solenoide, etc.
- Registro local dos dados (black box em cartão SD) com transmissão via **BLE** ou **Wi-Fi**.
- Classificação do **estado operacional da máquina** (parado / produtivo / alternativo / em trânsito) através de "Programas de Sensoriamento" (lógica de negócio por classe de máquina) — isso alimenta relatórios de produtividade no painel web da Simova.
- Opcionalmente, transmissão via **satélite Globalstar** (módulo SmartOne C) em áreas sem cobertura celular/Wi-Fi.

O firmware é proprietário (todos os direitos reservados — ver seção de copyright do README) e roda inteiramente em **C++** sobre um **ESP32**.

---

## 2. Hardware

**Versão de hardware atual:** 1.6.0 (mantido por Italo Soares, fabricado pela JLCPCB). Datasheets em `docs/datasheets/`.

### 2.1 MCU
- **ESP32-WROOM-32E-N16**
  - WiFi + Bluetooth (BLE via NimBLE)
  - 16MB de flash: 4MB OTA0 + 4MB OTA1 + 8MB reservados

### 2.2 Sensores embarcados
| Sensor | Chip | Interface | Endereço |
|---|---|---|---|
| Acelerômetro | LIS2DW12TR | I2C | 0x18 |
| Temperatura | TMP102 | I2C | 0x48 |
| RTC (relógio) | PCF8563 | I2C | 0x51 (battery-backed, CR1632, ~0.25µA) |
| GPS | L80RE | UART | — (hot-start, battery-backed p/ retenção de posição) |

I2C usa os pinos padrão do Arduino/ESP32 (`Wire.begin()` sem parâmetros): **SDA=GPIO21, SCL=GPIO22**.

### 2.3 CAN Bus
- Controlador **TWAI** interno do ESP32 + transceiver **TI TCAN332/SN65HVD232DR** (proteção ±70V, até 1Mbps).
- Protetores: TVS diode PESD2CAN-ES + resistores série 10Ω.
- Suporta ISO 11898-1, SAE J1939 (heavy-duty) e OBD2.
- Pinos: `CAN_TX=GPIO18`, `CAN_RX=GPIO19`.

### 2.4 Alimentação
- Regulador principal **XL1509-3.3** (saída 3.3V), protegido por fusível 1.5A/33V, diodos reversos SS34, TVS SMBJ36A (28V).
- Regulador buck de 60V (revisão nova) para robustez em transientes de alta tensão.
- Bateria de backup **CR1632** (120mAh) alimenta RTC + GPS (~7.5µA combinado, vida útil real ~6 meses).
- Monitoramento de tensão de entrada em `GPIO35` (ADC, divisor 15.8kΩ/1.2kΩ, mede até 45V, saída máx 3.53V).

### 2.5 Entradas digitais (4x)
Optoisoladas, protegidas por fusível 50mA/33V + resistor 22kΩ + zener 3.1–3.5V + optoacoplador LTV-247 (Vf 1.2V, Iout máx 50mA). Pull-up 10kΩ + LED de status com resistor 5kΩ.

- `INPUT1=GPIO25`, `INPUT2=GPIO26`, `INPUT3=GPIO27`, `INPUT4=GPIO32`.
- **Nota importante:** no hardware 1.3 a lógica é invertida (0 = >10V, 1 = <10V); tensão mínima de detecção ~9V.
- Uma entrada pode ser configurada como contador de pulso de RPM (interrupção), via `AT+RPMSRC`.

### 2.6 Armazenamento
Cartão SD via adaptador TF-115, modo **SPI**:
- `CS=GPIO15`, `MOSI=GPIO13`, `SCLK=GPIO14`, `MISO=GPIO12`. Alimentação 3.3V.

### 2.7 Módulo satélite (opcional)
**SmartOne C** (Globalstar), protocolo binário próprio via UART2 (9600 baud, 8N1):
- `TX=GPIO17`, `RX=GPIO5`.
- Ver seção 7.

### 2.8 Mapa de pinos GPIO — resumo (importante para planejar novo hardware)

| GPIO | Uso atual |
|---|---|
| 0 | Boot (não usar — deve estar LOW para flash) |
| 1 | UART0 TX (debug/AT serial) |
| 2 | LED de diagnóstico |
| 3 | UART0 RX |
| 4 | **Buzzer** (único "áudio" existente hoje — apenas bips) |
| 5 | SmartOne C RX |
| 6–11 | Reservado (flash SPI interno) — não usar |
| 12 | SD MISO |
| 13 | SD MOSI |
| 14 | SD SCLK |
| 15 | SD CS (também strapping pin — cuidado no boot) |
| 16 | GPS RX (UART1) |
| 17 | SmartOne C TX |
| 18 | CAN TX |
| 19 | CAN RX |
| 21 | I2C SDA (acelerômetro, temp, RTC) |
| 22 | I2C SCL |
| 23 | **livre** |
| 25 | Input1 (também DAC0 do ESP32, se não usado como input) |
| 26 | Input2 (também DAC1 do ESP32, se não usado como input) |
| 27 | Input3 |
| 32 | Input4 |
| 33 | **livre** |
| 34, 36, 39 | Input-only, **livres** (não podem ser saída — não servem para BCLK/WS/DOUT de I2S) |
| 35 | ADC leitura de tensão de alimentação (VIN) |

> **Para o novo repositório de TTS on-device:** o hardware atual do Simova Track **não tem DAC de áudio dedicado, amplificador ou alto-falante** — apenas um buzzer piezo simples no GPIO4 para bips de erro/sucesso (ver `lib/drvBuzzer`). Se o objetivo for tocar áudio TTS de fato (sintetizado ou pré-gravado) a partir do próprio ESP32, será necessário adicionar hardware (ex: módulo I2S DAC + amplificador classe D como MAX98357A, ou usar o DAC interno de 8 bits do ESP32 em GPIO25/26 com amplificador simples). Pinos livres para isso hoje: **GPIO23, GPIO33** (saída) e **GPIO34/36/39** (somente entrada, não servem para sinal I2S). Isso é pouco para um barramento I2S completo (precisa de 3 pinos de saída: BCLK, WS/LRCLK, DOUT) — o projeto real provavelmente exigirá reuso de algum pino hoje ocupado (ex. liberar Input4/GPIO32, ou usar uma segunda entrada apenas se não usada naquela aplicação) ou uma revisão de hardware.

---

## 3. Arquitetura de Software

### 3.1 Stack
- **Framework:** ESP-IDF v4.4.7 + Arduino Framework (Arduino como componente do ESP-IDF).
- **Linguagem:** C++.
- **Build system:** PlatformIO (`pio run -e esp32dev`).
- **Bibliotecas principais:** NimBLE-Arduino, TinyGPSPlus, RTClib, Adafruit ADXL343/GFX/SSD1306, ArduinoJson, DFRobot_LIS, QMC5883LCompass, Geofence, NuS-NimBLE-Serial.

### 3.2 Modelo de execução
Padrão Arduino (`setup()`/`loop()`) rodando sobre **FreeRTOS**. Sequência de boot (`setupAppBase`):
1. NVS flash → SD card → comunicações (UART + WiFi + BLE + comandos AT)
2. Sensores (RTC, GPS, LED, Buzzer, GPIO, Temp, Acelerômetro) → task dedicada `sensorsTask` (pinada a um core)
3. CAN bus → sistema de telemetria → `core.init()` → SmartOne C → `setupSensoringApp()`

Principais tasks FreeRTOS (definidas em `lib/common/config.h`): `updateSensors`, `canbusDriver`, `canbusProcessor`, `logTxTask` (telemetria), `bleRoute`, `uartRoute`, `restartAssistant`, além das tasks do sistema (loopTask, IDLE0/1, nimble_host, tiT/lwip, etc). Dois watchdogs alimentados no loop principal: task WDT (90s) e RTC WDT (20s) — **por isso `delay()` nunca é usado**, apenas checagens não-bloqueantes baseadas em `millis()`.

### 3.3 Estado global — struct `api`
Todo o firmware compartilha um único objeto global: `simova_track_api_t api` (definido em `lib/api/api.h`). É a única fonte de verdade:

| Camada | Acesso | Descrição |
|---|---|---|
| Sensores | `api.sensors.*` | Escrito pelos drivers |
| Telemetria | `api.telemetry.*` | Valores computados/fundidos para relatórios |
| Programas de usuário | `api.telemetry.working_state` | Saída principal dos "classeOperacional" |
| Info do dispositivo | `api.device_info.*` | Contadores de boot, MACs, versão FW |
| Comunicação | `api.comms.*` | Nome BLE, ID do dispositivo (virloc), contadores |
| CAN bus | `api.sensors.can.*` | Dados OBD2 / J1939 |

Campos importantes: `api.sensors.gps.speedKmh`, `api.sensors.gpio.input1..4`, `api.telemetry.ignition_status`, `api.telemetry.rpm`, `api.telemetry.working_state` (0=idle, 1=produtivo, 2=alternativo, 3=trânsito). Referência completa gerada automaticamente em `docs/api.md`.

### 3.4 Drivers
Todos inicializados em `src/updateSensors.cpp` / `src/canbus/drvCan.cpp`. Escrevem exclusivamente em `api.sensors.*`; nenhum outro código deve acessar drivers diretamente — apenas ler de `api`. A maioria são singletons (`Driver::getInstance()`), exceto `DrvTemp` e `DrvInputs`.

- `AccelerometerSensor` — médias de 10 amostras, roll/pitch, detecção de movimento.
- `GpsSensor` (wrapper TinyGPS++) — posição, velocidade, distância percorrida, fallback para última posição válida.
- `DrvInputs` — leitura debounced das 4 entradas + tensão de alimentação.
- `ClockSensor` (RTClib) — RTC com sync automático via GPS.
- `DrvTemp` — temperatura interna da placa.
- `SensorNVS` — wrapper para NVS do ESP-IDF.
- `DrvLed` / `DrvBuzzer` — feedback visual/sonoro simples (não escrevem em `api`).
- `CanProcessor` — decodificadores J1939/OBD2/Komatsu, task dedicada.

### 3.5 Programas de sensoriamento (`classeOperacional`)
São módulos de lógica de negócio (um `.h`+`.cpp` por classe de máquina) que leem `api.sensors.*`/`api.telemetry.*` e escrevem `api.telemetry.working_state`. Ativados via `AT+USRPROGRAM=<N>` + `AT+RESTART`. Programas atuais incluem: motoniveladora, basculante, pipa, trator esteira (com variante RPM), plantadeira (genérica), forwarder (3 variações, incluindo uma feita para Irving/Canadá). Guia completo em `src/classeOperacional/.skill-make-sensoring-programs.md`.

### 3.6 NVS (armazenamento persistente)
Wrapper `stCore.prphNvs`. Chaves com no máximo **15 caracteres**, prefixadas por programa (`irv_`, `meu_`, etc.), chaves cross-program em `include/nvsKeys.h` (prefixo `KN_`). Escrita no máximo a cada 60s (nunca a cada loop).

### 3.7 Sistema de comandos AT
`CommandAtProcessor` (`src/comms/commandProcessor.h`) — comandos registrados via `registerCommand("AT+CMD", callback)`. Disponível via UART0, BLE UART e Wi-Fi TCP. Cada callback trata 3 modos: `AT+CMD=?` (describe), `AT+CMD?` (query), `AT+CMD=<valor>` (set). Lista completa e atualizada em `docs/protocol-AT.md` (>50 comandos: sistema, WiFi, BLE, log, SD, GPIO/RPM, telemetria, programas de usuário, CAN, SmartOne C).

### 3.8 Logging
`LOG_I(TAG, "msg %d", val)` via `SafeLogger` (thread-safe, colorido, filtrável por tag) — nunca `printf`/`Serial.print`.

---

## 4. Protocolos de telemetria e comunicação

### 4.1 ST0 — log de eventos posicionais (formato principal)
Cada evento relevante (ignição, mudança de estado, violação de velocidade, etc.) gera um registro completo com GPS+velocidade+RPM+estado, salvo em `/sdcard/log.txt` e transmitido via BLE/Wi-Fi. Envelope XVM: `><payload>;ID=<device_id>;#<msg_num>;*<checksum><CRLF>`. ~25 códigos de evento (ignição on/off, motor on/off, mudança de working_state, violação de velocidade, aceleração/frenagem crítica, CAN ativo/inativo, etc). Ver `docs/protocol-ST0.md`.

### 4.2 RAX — anotações de texto livre
Mesmo envelope/arquivo do ST0, mas carrega apenas texto (sem GPS/sensores) — usado para boot info, diagnóstico, avisos e erros. Códigos: `RAX_INFORMATION(80)`, `RAX_WARNING(81)`, `RAX_ERROR(82)`, `WIFI_HELLO(83)`, `DIAGNOSTIC(100)`. Ver `docs/protocol-RAX.md`.

### 4.3 XVM — protocolo legado (compatibilidade)
Herdado de um dispositivo predecessor (família VL/Virloc). Comandos `>Q…`/`>S…`, respostas `>R…`. Em fase de descontinuação — **novas integrações devem usar AT + ST0/RAX**. Registrado em `src/comms/xvmCommands.cpp`. Contém o comando `>TTS<texto>` (ver seção 5). Ver `docs/protocol-XVM.md`.

### 4.4 Transporte
- **BLE:** via NimBLE, nome configurável (`AT+BLENAME`), MTU até 512 bytes (185 default Android). Transmissão de log iniciada pelo comando `>GFFN_HI` do app conectado.
- **Wi-Fi:** até 3 SSID/senha configuráveis (`AT+WIFI`), upload batelado para `ota.simovatrack.com`.
- **Satélite (SmartOne C / Globalstar):** protocolo binário próprio via UART2, usado como fallback fora de área de cobertura. Pacotes com preâmbulo `0xAA`, CRC-16, comandos como Get ESN, Get Firmware, Send Truncated/Raw Message, Get Diagnostic Info. Detalhes completos em `docs/smartonec.md`.

---

## 5. Estado atual de "TTS" / áudio — **contexto crítico para o novo repositório**

O Simova Track **já tem um mecanismo chamado "TTS" hoje, mas ele NÃO sintetiza nem reproduz áudio no ESP32**. Funciona assim:

- Função helper: `sendTextToSpeech(std::string)` / `sendTextToSpeech(const char* format, ...)` em `src/comms/communications.cpp`, que internamente chama `handle_TTS(message, BLE_UART)` (`src/comms/xvmCommands.cpp`).
- `handle_TTS()` apenas **monta um envelope XVM e ecoa o texto de volta pela BLE**: `>TTS<mensagem>;ID=...;#...;*XX<`.
- **Quem "fala" o texto é o aplicativo celular conectado via BLE**, não o firmware — o ESP32 só envia a string.
- Mensagens padronizadas (erros de boot, avisos) ficam centralizadas em `src/core/language.h`, em português, com macros para caracteres especiais (`CHAR_A_TILDE`, `CHAR_C_CEDILLA`, etc), já que o C++ não usa UTF-8 direto no código-fonte facilmente. Exemplos: `TTS_SDCARD_ERROR`, `TTS_GPS_ERROR`, etc.
- O único "áudio" físico embarcado no dispositivo é um **buzzer piezo simples** (`lib/drvBuzzer`, `GPIO4`) que toca apenas bips de sucesso/erro (2 bips curtos / 3 bips longos) — não reproduz voz nem áudio arbitrário.
- Não existe DAC de áudio, amplificador ou alto-falante no hardware atual (ver seção 2.8).

### Implicações para o novo repositório
Se o objetivo é fazer o **próprio ESP32 reproduzir áudio TTS** (sintetizado no device, ou tocando arquivos de áudio pré-gravados/baixados), isso é uma capacidade **nova**, não existente hoje. Pontos a considerar ao planejar:

1. **Hardware necessário:** DAC de áudio + amplificador + alto-falante. Opções comuns em ESP32: (a) DAC interno 8-bit (GPIO25/26) + amplificador classe D simples — barato mas qualidade baixa; (b) módulo I2S externo (ex. MAX98357A, PCM5102) — melhor qualidade, mas precisa de 3 pinos de saída livres (BCLK, WS, DOUT), que são escassos no hardware atual do Simova Track (só há GPIO23 e GPIO33 livres como saída — ver seção 2.8).
2. **Origem do áudio:** síntese de voz local (ex. engine TTS embarcado, geralmente pesado para ESP32) vs. tocar arquivos de áudio pré-gerados (ex. .wav/.mp3 gerados off-device por um serviço de TTS na nuvem e enviados/baixados para o SD card) vs. streaming.
3. **Armazenamento:** já existe SD card no hardware (SPI, `lib/drvSdCard`), reaproveitável para guardar arquivos de áudio.
4. **Convenção de nomes:** se este novo repo for ligado ao ecossistema Simova, considerar manter compatibilidade conceitual com o mecanismo `>TTS<texto>` existente (para não quebrar apps que já esperam esse comando), mas adicionando reprodução local como capability adicional — não necessariamente substituindo o relay atual.
5. **Restrições de memória/CPU:** o firmware atual já é sensível a heap (ver notas no `changelog.md` sobre otimizações de memória, remoção de buffers, watchdogs de 90s/20s) — qualquer biblioteca de síntese de voz ou decodificação de áudio precisa ser avaliada quanto a footprint em uma ESP32-WROOM-32E (SRAM interna é o recurso mais escasso, não a flash de 16MB).

---

## 6. Referência rápida de arquivos-chave (repo `simova-track`)

| O quê | Onde |
|---|---|
| Estado global (`api`) | `lib/api/api.h` |
| Registro de chaves NVS cross-program | `include/nvsKeys.h` |
| Enum + orquestração de programas de usuário | `include/appSensoring.h`, `src/appSensoring.cpp` |
| Funções utilitárias (`elapsed_since`, etc) | `lib/common/portTools.h` |
| Configurações de hardware/pinos | `lib/common/config.h` |
| Singleton core (NVS, LED, SD) | `src/core/core.h` |
| Helpers de comandos AT | `src/comms/atCommands.h`, `.cpp` |
| Mensagens de TTS (texto, PT-BR) | `src/core/language.h` |
| Função `sendTextToSpeech` | `src/comms/communications.cpp` |
| Handler XVM do TTS | `src/comms/xvmCommands.cpp` (`handle_TTS`) |
| Driver do buzzer | `lib/drvBuzzer/` |
| Driver do SD card | `src/filesystem/drvSdCard.cpp` |
| Guia para criar programa de sensoriamento | `src/classeOperacional/.skill-make-sensoring-programs.md` |
| Docs completos | `docs/*.md` (hardware, drivers, api, sensoring-app, protocol-AT/ST0/RAX/XVM, smartonec, code-style) |

---

## 7. Convenções do projeto (resumo)

- **Commits:** Conventional Commits (`feat`, `fix`, `chore`, `refactor`, `perf`, `docs`, `style`, `test`), com `JOURNAL.md` atualizado **antes** de cada commit.
- **Estilo de código:** Google C++ Style Guide; PascalCase para classes, camelCase para variáveis/métodos, SCREAMING_SNAKE_CASE para constantes; evitar variáveis globais soltas; RAII; smart pointers; `enum class`.
- **AT commands novos:** devem sempre ser documentados em `docs/protocol-AT.md`.
- **Nunca usar `delay()`** — usar `elapsed_since()` / `millis()` (watchdogs de 90s e 20s ativos).
