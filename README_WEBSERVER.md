# Script de Segurança para Web Servers (Apache/Nginx)

O `webserver_security.sh` é um script de auditoria focado em servidores web. Ele detecta automaticamente se você está rodando Apache ou Nginx e verifica as melhores práticas de segurança.

## Funcionalidades

### Detecção Automática
*   Identifica se o servidor principal é **Nginx** ou **Apache** (httpd).

### Nginx Security
*   **Version Hiding**: Verifica se `server_tokens off` está ativo para ocultar a versão do Nginx.
*   **Buffer Overflow Protection**: Checa a configuração de `client_max_body_size`.
*   **Security Headers**: Verifica a presença de headers críticos:
    *   `X-Frame-Options` (Contra Clickjacking)
    *   `X-XSS-Protection` (Contra XSS)
    *   `X-Content-Type-Options` (Contra MIME-sniffing)

### Apache Security
*   **Information Leakage**: Verifica `ServerTokens` (deve ser Prod) e `ServerSignature` (deve ser Off).
*   **Modules Check**:
    *   Verifica se o **ModSecurity** (WAF) está carregado.
    *   Verifica se o **ModEvasive** (Anti-DDoS) está carregado.
*   **Headers**: Checa proteção contra Clickjacking.

### SSL/TLS
*   Verifica a existência de certificados SSL gerenciados pelo Let's Encrypt.

## Como Usar

### Pré-requisitos
*   Acesso **root** obrigatório.

### Execução

1.  Dê permissão de execução:
    ```bash
    chmod +x webserver_security.sh
    ```

2.  Execute o script:
    ```bash
    ./webserver_security.sh
    ```

3.  Analise o output colorido:
    *   **VERDE [OK]**: Configuração segura encontrada.
    *   **AMARELO [WARN]**: Configuração insegura ou ausente (ação recomendada).
    *   **VERMELHO [ERROR]**: Problema crítico ou falha na execução.

## Logs
Um log detalhado é salvo em `/var/log/webserver_security.log`.

---
*Desenvolvido pela Equipe de Segurança Cyber Gamers.*
