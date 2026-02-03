# Novo Script Anti-DDoS Consolidado

Este diretório contém o novo script `new_anti_ddos.sh`, desenvolvido para consolidar e aprimorar as funcionalidades de proteção Anti-DDoS dos scripts anteriores (`blocklist e kernel Anti-DDoS` e `Menu-2.sh`).

## Funcionalidades

O script implementa as seguintes camadas de proteção:

1.  **Kernel Hardening (Sysctl)**: Aplica configurações robustas no kernel do Linux para mitigar ataques comuns como SYN Flood, Smurf Attacks e redirecionamentos maliciosos.
2.  **Rastreamento e Rate Limiting (Iptables)**: Utiliza regras avançadas do iptables (`recent` e `hashlimit`) para identificar e bloquear automaticamente IPs que excedem limites de conexão (Anti-Prowler/Anti-Attacker).
3.  **Whitelist de Países (GeoIP)**: Permite explicitamente o tráfego de países confiáveis (configurado para PT, BR, US por padrão) antes de aplicar bloqueios.
4.  **Blocklists Automáticas**: Baixa e aplica listas de IPs maliciosos conhecidos de diversas fontes confiáveis.

## Como Usar

### Pré-requisitos

*   Acesso **root** (o script verifica isso automaticamente).
*   Pacotes recomendados: `curl`, `iptables`, `ipset` (opcional, mas recomendado para alta performance).

### Execução

1.  Dê permissão de execução ao script:
    ```bash
    chmod +x new_anti_ddos.sh
    ```

2.  Execute o script:
    ```bash
    ./new_anti_ddos.sh
    ```

### Agendamento (Cron)

Para manter as listas de bloqueio e configurações atualizadas, recomenda-se agendar a execução via crontab (exemplo para rodar a cada 24 horas):

1.  Edite o crontab: `crontab -e`
2.  Adicione a linha:
    ```
    0 3 * * * /caminho/para/new_anti_ddos.sh > /var/log/anti_ddos.log 2>&1
    ```

## Notas Importantes

*   **Limite de Regras**: O script limita o bloqueio individual de IPs de blocklists a 5000 entradas para evitar sobrecarga no iptables se o `ipset` não estiver sendo usado. Para proteção completa em larga escala, recomenda-se adaptar o script para usar `ipset`.
*   **Whitelist**: Verifique a variável `COUNTRIES_TO_ALLOW` no início do script para ajustar os países permitidos.

---
*Gerado por AI Assistant.*
