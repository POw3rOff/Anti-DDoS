http {
    # Configuração para limitar a taxa de solicitações
    limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;

    # Configurações gerais
    client_body_buffer_size 10k;
    client_header_buffer_size 1k;
    client_max_body_size 8m;
    large_client_header_buffers 2 1k;
    client_body_timeout 12s;
    client_header_timeout 12s;
    keepalive_timeout 15s;
    send_timeout 10s;

    # Configuração de rate limiting
    server {
        listen 80;
        server_name seuDominio.com;

        location / {
            limit_req zone=one burst=20;
            # ... outras configurações ...
        }
    }

    # Configuração de IP Whitelisting/Blacklisting
    server {
        listen 80;
        server_name outroDominio.com;

        location / {
            deny 192.168.1.1;
            allow 10.0.0.0/24;
            allow 192.168.2.0/24;
            deny all;
            # ... outras configurações ...
        }
    }

    # Configurações adicionais de segurança
    server {
        listen 80 default_server;
        server_name _;

        # Evitar informações desnecessárias
        server_tokens off;

        # Configurações de segurança de headers
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

        # Configuração para evitar hotlinking
        location ~ \.(jpg|jpeg|png|gif|swf)$ {
            valid_referers none blocked seuDominio.com;
            if ($invalid_referer) {
                return 403;
            }
        }

        # Configuração para proteger contra ataques de força bruta
        location /wp-login.php {
            limit_req zone=login burst=3;
            # ... outras configurações ...
        }

        # Configuração para proteger contra escaneamento de diretórios
        location ~ /\. {
            deny all;
        }
    }
}
