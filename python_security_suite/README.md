# Python Security Suite

Esta suite contém ferramentas de segurança desenvolvidas em Python para complementar os scripts em Bash do repositório. O Python é utilizado aqui para tarefas que exigem análise estatística, processamento de dados complexos ou bibliotecas específicas.

## Ferramentas Disponíveis

### 1. Detector de Anomalias em Logs (`log_anomaly_detector.py`)

Analisa arquivos de log (como Syslog ou Auth.log) e detecta comportamentos anômalos baseados em estatística (desvio padrão).

**Funcionalidades:**
- Parse automático de datas (formato Syslog).
- Agrupamento de eventos por minuto.
- Cálculo de Média e Desvio Padrão.
- Alerta sobre picos de atividade (Z-Score).

**Como usar:**

Diretamente com Python:
```bash
python3 log_anomaly_detector.py /var/log/auth.log --threshold 3.0
```

Ou via Wrapper:
```bash
./run_anomaly_detector.sh /var/log/auth.log
```

**Parâmetros:**
- `logfile`: Caminho para o arquivo de log.
- `--threshold`: (Opcional) Número de desvios padrão para considerar uma anomalia (Padrão: 3.0).

## Requisitos

- Python 3.6+
- Bibliotecas padrão (`re`, `collections`, `statistics`, `datetime`, `argparse`).

### 2. SOC - Correlação de Eventos (`soc_correlacao_eventos.py`)

Correlaciona logs de múltiplos arquivos (firewall, SSH, sistema) para detectar padrões complexos de ataque.

**Funcionalidades:**
- Detecção de Brute-Force distribuído ou lento.
- Detecção de Movimentação Lateral (Login seguido de ações privilegiadas).
- Correlação por IP e timestamp.

**Como usar:**
```bash
python3 soc_correlacao_eventos.py --logs /var/log/auth.log /var/log/syslog
```

### 3. IDS Comportamental (`ids_comportamental.py`)

IDS baseado em baseline dinâmica. Aprende o comportamento normal do sistema (CPU, Memória, Rede) e alerta desvios.

**Funcionalidades:**
- Modo de Aprendizado (`--mode learn`): Cria perfil de baseline.
- Modo de Monitoramento (`--mode monitor`): Compara estado atual com perfil (Z-Score).
- Monitora CPU, Memória e Taxa de Rede (Upload/Download).

**Como usar:**
```bash
# Fase de aprendizado (60 segundos)
python3 ids_comportamental.py --mode learn --duration 60 --output baseline.json

# Fase de monitoramento
python3 ids_comportamental.py --mode monitor --input baseline.json
```

### 4. Detector de Exfiltração de Dados (`detetor_exfiltracao_dados.py`)

Analisa o tráfego de saída para identificar exfiltração de dados silenciosa e anomalias de rede.

**Funcionalidades:**
- Monitoramento de volume de upload (MB/min).
- Detecção de conexões longas ou para portas suspeitas.
- Heurística simples para tunelamento DNS/HTTP.

**Como usar:**
```bash
python3 detetor_exfiltracao_dados.py --limit-mb 50 --interval 10
```

### 5. Firewall Dinâmica Autônoma (`firewall_dinamica_autonomo.py`)

Monitora conexões em tempo real e bloqueia IPs hostis automaticamente usando iptables.

**Funcionalidades:**
- Proteção contra DoS/DDoS (Connection Flood, SYN Flood).
- Lista de permissão (Whitelist) integrada.
- Modo de simulação (Dry-Run) e modo ativo.

**Como usar:**
```bash
# Modo simulação (apenas mostra o que faria)
python3 firewall_dinamica_autonomo.py --max-conns 50

# Modo ativo (Aplica bloqueios - Requer Root)
sudo python3 firewall_dinamica_autonomo.py --max-conns 50 --apply
```

### 6. Forense de Memória Live (`forense_memoria_live.py`)

Realiza análise forense em memória sem desligar o sistema, focando em processos suspeitos.

**Funcionalidades:**
- Detecta binários deletados ainda em execução.
- Detecta regiões de memória RWX (Read-Write-Execute), indicativo de shellcode/injectors.
- Lista sockets abertos por processo suspeito.

**Como usar:**
```bash
sudo python3 forense_memoria_live.py --scan-level full
```

### 7. Auditoria de Integridade Total (`auditoria_integridade_total.py`)

Monitoramento de integridade de arquivos (FIM) com base em hash SHA256.

**Funcionalidades:**
- Monitora /bin, /sbin, /usr/bin, /etc, /boot.
- Detecta criação, remoção e modificação de conteúdo ou permissões.
- Base de dados local (JSON).

**Como usar:**
```bash
# Inicializar (Baseline)
python3 auditoria_integridade_total.py --action init

# Verificar alterações
python3 auditoria_integridade_total.py --action check
```

### 8. Timeline Forense Automática (`timeline_forense_automatica.py`)

Gera uma linha do tempo unificada de eventos do sistema e modificações de arquivos.

**Funcionalidades:**
- Parse de logs (Auth, Syslog, Kernel).
- Coleta de metadados de arquivos (mtime/ctime).
- Exportação para CSV ordenado cronologicamente.

**Como usar:**
```bash
python3 timeline_forense_automatica.py --days 7 --output caso_investigacao.csv
```
