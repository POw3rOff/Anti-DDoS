# Layer 4 - TCP/UDP Advanced Suite

Este diretório contém scripts Python avançados para monitorização, deteção e mitigação de ameaças na camada de transporte (Layer 4).

## Scripts Disponíveis

### 1. `syn_flood_detector.py`
Deteta ataques de SYN Flood monitorizando o estado `SYN_RECV` das conexões TCP.
- **Uso:** `python3 syn_flood_detector.py [--threshold 100] [--interval 2]`

### 2. `syn_ack_anomaly_monitor.py`
Analisa anomalias no handshake TCP (desequilíbrio SYN/SYN-ACK) e ativação de SYN Cookies.
- **Uso:** `python3 syn_ack_anomaly_monitor.py [--interval 5]`

### 3. `tcp_connection_rate_guard.py`
Monitoriza a taxa de criação de novas conexões por endereço IP.
- **Uso:** `python3 tcp_connection_rate_guard.py [--limit 10] [--interval 1.0]`

### 4. `tcp_state_exhaustion_detector.py`
Deteta exaustão de estados TCP (tabela `conntrack` e uso de sockets/memória).
- **Uso:** `python3 tcp_state_exhaustion_detector.py [--threshold 80] [--interval 5]`

### 5. `udp_flood_detector.py`
Deteta floods UDP baseando-se em taxas de pacotes (PPS), erros de buffer e filas de recepção saturadas.
- **Uso:** `python3 udp_flood_detector.py [--pps-threshold 2000] [--interval 2]`

## Requisitos
- Python 3.x
- Permissões de leitura em `/proc` (geralmente não requer root, exceto para mitigação ativa se implementada).
- Linux Kernel (dependência de `/proc/net/*`).


### 6. `udp_amplification_guard.py`
Deteta padrões de amplificação UDP (DNS, NTP, SSDP, CLDAP) analisando tráfego de entrada.
- **Uso:** `python3 udp_amplification_guard.py [--threshold-pps 1000]`

### 7. `port_abuse_detector.py`
Deteta abuso massivo (flood/scan) em portas específicas, com suporte a portas críticas configuráveis.
- **Uso:** `python3 port_abuse_detector.py [--limit 1000]`

### 8. `packet_rate_baseline_engine.py`
Cria uma baseline de tráfego (RX/TX PPS) e alerta sobre desvios significativos (spikes).
- **Uso:** `python3 packet_rate_baseline_engine.py [--threshold 3.0]`

### 9. `tcp_flag_anomaly_detector.py`
Analisa pacotes TCP à procura de flags inválidas (NULL, XMAS, SYN+FIN) ou suspeitas.
- **Uso:** `python3 tcp_flag_anomaly_detector.py [--interval 5]`

### 10. `layer4_response_orchestrator.py`
Orquestrador central que pode monitorizar logs de alerta e aplicar mitigação automática (bloqueio de IP).
- **Uso:** `python3 layer4_response_orchestrator.py --monitor --log-file /var/log/l4.log`
