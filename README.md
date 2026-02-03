Esta suite de segurança implementa um firewall robusto baseado em iptables, desenvolvido por p0w3r0ff para proteger a infraestrutura da Cyber-Gamers. A solução foi exaustivamente testada e validada pela comunidade contra ataques DDoS. Para mais informações, visite https://cyber-gamers.org/

---

# Cyber Gamers Linux Security Suite

Este repositório evoluiu para uma suite completa de segurança, auditoria e hardening para sistemas Linux. Além do firewall original, ele agora inclui ferramentas para proteção de kernel, backups inteligentes, resposta a incidentes, detecção de intrusões e muito mais.

## Estrutura do Projeto

O projeto está organizado em suites modulares, cada uma focada em um aspecto crítico da segurança:

### 🛡️ Segurança de Rede e Firewall
**Diretórios:** `ddos_protection`, `linux_firewall_suite`, `advanced_network_security_suite`, `network_access_control`
*   **Anti-DDoS:** Scripts avançados com integração ao Kernel e Blocklists para mitigação de ataques volumétricos.
*   **Firewall Modular:** Suporte para `iptables`, `nftables`, `ufw`, `shorewall`, `firewalld` e `fail2ban`.
*   **Monitorização:** Detecção de tráfego de saída suspeito, túneis, scans internos e anomalias de DNS/TLS.

### 🐧 Kernel e Hardening do SO
**Diretórios:** `kernel_os_security_suite`, `system_security_suite`, `system_resistance_suite`
*   **Auditoria:** Verificação de integridade do kernel, módulos e binários do sistema.
*   **Hardening:** Ajustes de sysctl, detecção de rootkits, exploits locais e verificação de LSM (SELinux/AppArmor).
*   **Resistência:** Testes de resistência do sistema contra vetores de ataque comuns.

### 💾 Backups e Redundância
**Diretórios:** `smart_backup_suite`, `backup_security_suite`, `redundancy_and_survival_suite`, `governance_and_control_suite`
*   **Inteligência:** Backups incrementais, compressão adaptativa e retenção GFS (Grandfather-Father-Son).
*   **Segurança:** Criptografia, airgap, honeypots de backup e proteção contra ransomware.
*   **Resiliência:** Replicação geográfica e validação cruzada.

### 🚨 Detecção e Resposta a Incidentes
**Diretórios:** `incident_response_suite`, `intrusion_detection_suite`, `advanced_security_suite`, `logging_observability_suite`
*   **Resposta:** Ferramentas para congelamento de evidências, snapshots forenses e timeline de restauro.
*   **Detecção:** Identificação de beaconing, reverse shells, privilégios elevados e assinaturas de ataque.
*   **Observabilidade:** Centralização de logs, validação de timestamps e detecção de manipulação de logs (tampering).

### 📦 Segurança de Aplicações e Containers
**Diretórios:** `container_security_suite`, `application_security_suite`, `supply_chain_security_suite`, `web_security`
*   **Containers:** Auditoria de Docker/Podman, verificação de imagens e detecção de escapes.
*   **Web/App:** Proteção contra RCE, Webshells, SSRF e monitorização de uploads.
*   **Supply Chain:** Validação de updates, dependências e inventário de software.

### 🔒 Zero Trust e Automação
**Diretórios:** `zero_trust_suite`, `automation_and_maturity_suite`
*   **Zero Trust:** Auditoria de movimento lateral, isolamento de serviços e privilégios mínimos.
*   **Maturidade:** Dashboards de estado, scoring de segurança e auditorias automatizadas.

## Instalação e Uso

A maioria dos scripts foi desenvolvida para ser executada em ambiente Linux (Debian/Ubuntu/CentOS) e requer privilégios de **root**.

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/seu-repo/cyber-gamers-security.git
    cd cyber-gamers-security
    ```

2.  **Permissões de Execução:**
    ```bash
    chmod +x **/*.sh
    ```

3.  **Execução:**
    Navegue até o diretório da suite desejada e execute o script correspondente. Por exemplo, para ativar o novo Anti-DDoS:
    ```bash
    cd ddos_protection
    ./new_anti_ddos.sh
    ```

## Aviso Legal

Estes scripts são fornecidos "como estão", sem garantia de qualquer tipo. O uso destas ferramentas é de inteira responsabilidade do utilizador. Teste sempre em ambiente controlado antes de aplicar em produção.
