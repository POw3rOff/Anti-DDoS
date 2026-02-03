# Script de Auditoria e Hardening de Servidor Linux

O `server_audit_hardening.sh` é um script totalmente novo focado na segurança interna do servidor, complementando scripts de proteção de perímetro (como firewalls e anti-DDoS).

## Funcionalidades Principais

O script opera em dois modos:

1.  **Modo Auditoria**: Realiza verificações de segurança sem alterar nada no sistema.
2.  **Modo Hardening**: Aplica correções automáticas para vulnerabilidades comuns encontradas.

### Verificações Realizadas

*   **Usuários**:
    *   Detecção de usuários não-root com UID 0 (risco crítico).
    *   Detecção de contas com senha vazia.
*   **Permissões de Arquivos**:
    *   Verificação e correção de permissões em arquivos críticos (`/etc/passwd`, `/etc/shadow`, `/etc/ssh/sshd_config`, etc.).
*   **SSH**:
    *   Verificação de configurações inseguras (`PermitRootLogin`, `PasswordAuthentication`).
*   **Rede**:
    *   Listagem de portas abertas e serviços ouvindo.

## Como Usar

### Pré-requisitos

*   Acesso **root** obrigatório.

### Instalação

1.  Dê permissão de execução:
    ```bash
    chmod +x server_audit_hardening.sh
    ```

### Execução

1.  Execute o script:
    ```bash
    ./server_audit_hardening.sh
    ```

2.  Escolha uma opção no menu interativo:
    *   **Opção 1**: Gera um relatório detalhado na tela e em `/var/log/security_audit.log`.
    *   **Opção 2**: Aplica correções de segurança (Hardening). O script pedirá confirmação antes de alterar arquivos.

## Log

Todas as operações são registradas em `/var/log/security_audit.log` com data e hora.

---
*Desenvolvido pela Equipe de Segurança Cyber Gamers.*
