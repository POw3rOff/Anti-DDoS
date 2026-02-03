Este conjunto de regras é destinado a rastrear e registrar atividades suspeitas no iptables,
identificando possíveis "prowlers" (entidades que podem estar realizando varreduras ou sondas suspeitas) e "attackers" (entidades que podem estar envolvidas em ataques).

O script usa as extensões recent e hashlimit do iptables para realizar o rastreamento. Aqui está uma breve explicação de cada parte:

TRACK_PROWLER:

prowler-rapid: Se um IP tentar estabelecer mais de 6 conexões em 10 segundos, ele será marcado como um prowler em alta velocidade.

prowler-fast: Se um IP tentar estabelecer mais de 1 conexão por minuto, ele será marcado como um prowler em alta velocidade.

prowler-medium: Se um IP tentar estabelecer mais de 1 conexão por hora, ele será marcado como um prowler de média velocidade.

prowler-slow: (Comentado) Se um IP tentar estabelecer mais de 1 conexão por dia, ele seria marcado como um prowler de baixa velocidade.

TRACK_ATTACKER:

Semelhante ao TRACK_PROWLER, mas para atividades associadas a possíveis ataques.
