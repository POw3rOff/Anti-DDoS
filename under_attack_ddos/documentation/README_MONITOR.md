# Script de Monitoramento de Segurança e Integridade

O `security_monitor.sh` é um script de monitoramento proativo que combina **Monitoramento de Integridade de Arquivos (FIM)** com **Análise de Logs** para detectar atividades suspeitas.

## Funcionalidades

1.  **Monitoramento de Integridade (FIM)**:
    *   Monitora arquivos críticos do sistema (`/etc/passwd`, `/etc/shadow`, `/etc/ssh/sshd_config`, etc.).
    *   Cria uma base de dados de hashes (SHA256) na primeira execução.
    *   Nas execuções subsequentes, compara os hashes atuais com os salvos e alerta se houver modificações.

2.  **Detecção de Brute Force**:
    *   Analisa as últimas 1000 linhas de `/var/log/auth.log` (ou `/var/log/secure`).
    *   Alerta se detectar um alto volume de falhas de autenticação (> 50 falhas).

3.  **Monitoramento de Processos**:
    *   Verifica se existem processos consumindo uso excessivo de CPU (> 80%), o que pode indicar crypto-miners ou processos travados.

4.  **Sistema de Alerta**:
    *   Registra tudo em `/var/log/security_monitor.log`.
    *   Suporte a envio de e-mail (se configurado e o comando `mail` estiver disponível).

## Como Usar

### Pré-requisitos
*   Acesso **root** obrigatório.

### Instalação
1.  Dê permissão de execução:
    ```bash
    chmod +x security_monitor.sh
    ```

2.  (Opcional) Edite o script para configurar o e-mail de alerta:
    ```bash
    EMAIL_ALERT="seu_email@exemplo.com"
    ```

### Execução Manual
Execute o script para verificar o estado atual:
```bash
./security_monitor.sh
```

### Agendamento (Recomendado)
Para monitoramento contínuo, adicione ao crontab para rodar a cada hora:

1.  Edite o crontab: `crontab -e`
2.  Adicione a linha:
    ```
    0 * * * * /caminho/para/security_monitor.sh > /dev/null 2>&1
    ```

---
*Desenvolvido pela Equipe de Segurança Cyber Gamers.*
