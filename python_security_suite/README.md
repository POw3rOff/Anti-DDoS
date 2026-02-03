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
