# Makefile per API Calls
# Usage: make <target>

# Configurazione
API_BASE = https://api.citylog.cloud
USERNAME = apollo@example.com
PASSWORD = 1234
SESSION_FILE = api_session.json

# Colori per output
GREEN = \033[0;32m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help login test get-rifiuti create-rifiuto update-rifiuto delete-rifiuto clean session-info curl-examples

help:
	@echo "$(GREEN)=== Makefile API Client ===$(NC)"
	@echo "Targets disponibili:"
	@echo "  $(GREEN)help$(NC)        	 - Mostra questo help"
	@echo "  $(GREEN)login$(NC)       	 - Login e ottieni token (HTTPie)"
	@echo "  $(GREEN)test$(NC)        	 - Test connessione API"
	@echo "  $(GREEN)get-rifiuti$(NC) 	 - Ottieni lista rifiuti"
	@echo "  $(GREEN)create-rifiuto$(NC) - Crea nuovo rifiuto"
	@echo "  $(GREEN)clean$(NC)       	 - Pulisci file temporanei"
	@echo "  $(GREEN)session-info$(NC)   - Info sessione"
	@echo "  $(GREEN)curl-examples$(NC)  - Esempi con curl"
	# Confronto tra con e senza auth
test-comparison:
	@echo "$(GREEN)=== Confronto endpoint ===$(NC)"
	@echo "1. Con autenticazione:"
	@make get-rifiuti || echo "Fallito (auth required)"
	@echo ""
	@echo "2. Senza autenticazione:"
	@make test-no-auth

# Login con HTTPie e salva session
login:
	@echo "$(GREEN)Effettuo login...$(NC)"
	http --session=$(SESSION_FILE) --form POST $(API_BASE)/auth/token \
		username=$(USERNAME) password=$(PASSWORD) \
		|| echo "$(RED)Login fallito$(NC)"

# Test connessione base
test:
	@echo "$(GREEN)Test connessione API...$(NC)"
	http --session=$(SESSION_FILE) GET $(API_BASE)/docs \
		|| echo "$(RED)Test fallito$(NC)"

# Test senza autenticazione
test-no-auth:
	@echo "$(GREEN)Test endpoint senza autenticazione...$(NC)"
	http GET $(API_BASE)/rifiuti/no-auth

# Ottieni lista rifiuti
get-rifiuti:
	@echo "$(GREEN)Recupero lista rifiuti...$(NC)"
	http --session=$(SESSION_FILE) GET $(API_BASE)/rifiuti/

# Crea nuovo rifiuto (esempio)
create-rifiuto:
	@echo "$(GREEN)Creazione nuovo rifiuto...$(NC)"
	http --session=$(SESSION_FILE) POST $(API_BASE)/rifiuti/ \
		tipo="Plastica" \
		quantita:=10 \
		descrizione="Bottiglie di plastica"

# Aggiorna rifiuto (esempio con ID)
update-rifiuto:
	@echo "$(GREEN)Aggiornamento rifiuto...$(NC)"
	http --session=$(SESSION_FILE) PUT $(API_BASE)/rifiuti/1 \
		tipo="Plastica Riciclata" \
		quantita:=15

# Elimina rifiuto
delete-rifiuto:
	@echo "$(RED)Eliminazione rifiuto ID 1...$(NC)"
	http --session=$(SESSION_FILE) DELETE $(API_BASE)/rifiuti/1

# Info sessione
session-info:
	@echo "$(GREEN)Info sessione:$(NC)"
	@if [ -f "$(SESSION_FILE)" ]; then \
		cat $(SESSION_FILE) | jq . 2>/dev/null || echo "Sessione non JSON"; \
	else \
		echo "Nessuna sessione attiva"; \
	fi

# Pulisci file temporanei
clean:
	@echo "$(GREEN)Pulizia file temporanei...$(NC)"
	@rm -f $(SESSION_FILE) token.txt response.json
	@echo "Pulizia completata"

# Esempi equivalenti con CURL (per confronto)
curl-examples:
	@echo "$(GREEN)=== Esempi CURL ===$(NC)"
	
	@echo "1. Login con curl:"
	@echo "curl -X POST \"$(API_BASE)/auth/token\" \\"
	@echo "  -H \"Content-Type: application/x-www-form-urlencoded\" \\"
	@echo "  -d \"username=$(USERNAME)&password=$(PASSWORD)\""
	
	@echo ""
	@echo "2. Get rifiuti con curl:"
	@echo "curl -X GET \"$(API_BASE)/rifiuti/\" \\"
	@echo "  -H \"Authorization: Bearer \$$TOKEN\""

# Target per sviluppo con watch
watch-rifiuti:
	@echo "$(GREEN)Watch rifiuti (aggiorna ogni 5s)...$(NC)"
	@while true; do \
		clear; \
		echo "=== Ultimo aggiornamento: $$(date) ==="; \
		make get-rifiuti || echo "$(RED)Errore$(NC)"; \
		sleep 5; \
	done

# Variabile environment
setup-env:
	@echo "#!/bin/bash" > .env.sh
	@echo "export API_BASE=$(API_BASE)" >> .env.sh
	@echo "export USERNAME=$(USERNAME)" >> .env.sh
	@echo "export PASSWORD=$(USERNAME)" >> .env.sh
	@chmod +x .env.sh
	@echo "$(GREEN)File .env.sh creato$(NC)"

# Backup sessione
backup-session:
	@if [ -f "$(SESSION_FILE)" ]; then \
		cp $(SESSION_FILE) $(SESSION_FILE).backup.$$(date +%Y%m%d_%H%M%S); \
		echo "$(GREEN)Backup sessione creato$(NC)"; \
	else \
		echo "$(RED)Nessuna sessione da backup$(NC)"; \
	fi

# Installazione dipendenze
check-deps:
	@echo "$(GREEN)Controllo dipendenze...$(NC)"
	@which http > /dev/null && echo "✓ HTTPie installato" || echo "✗ HTTPie non installato: brew install httpie"
	@which jq > /dev/null && echo "✓ jq installato" || echo "✗ jq non installato: brew install jq"
	@which curl > /dev/null && echo "✓ curl installato" || echo "✗ curl non installato"

# Target per scenario completo
scenario-completo: check-deps login test get-rifiuti session-info
	@echo "$(GREEN)=== Scenario completato ===$(NC)"
