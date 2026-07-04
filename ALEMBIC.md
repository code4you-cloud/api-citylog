# ALEMBIC - Guida rapida ai comandi

Alembic è lo strumento di migrazione per SQLAlchemy. Questa guida elenca i comandi essenziali, il loro scopo e quando utilizzarli.

## Setup iniziale

```bash
# Inizializza l'ambiente di migrazione nella cartella specificata (di solito 'alembic')
alembic init <directory>

# Modifica il file alembic.ini per impostare la stringa di connessione al database
# e il file env.py per puntare ai tuoi modelli SQLAlchemy.

2. Tabella riassuntiva dei comandi
Comando	Descrizione	                        Quando usarlo
alembic current	                            Mostra la revisione corrente del database	Per sapere a che punto sei
alembic history	                            Elenca tutte le migrazioni in ordine cronologico	Per vedere la cronologia e i rapporti tra revisioni
alembic revision -m "msg"	                Crea un nuovo file di migrazione vuoto	Quando vuoi scrivere manualmente le operazioni SQL
alembic revision --autogenerate -m "msg"	Genera automaticamente il codice di migrazione confrontando modelli e database	Per creare rapidamente migrazioni semplici
alembic upgrade <revisione>	                Applica le migrazioni fino alla revisione specificata	Per aggiornare il database a una versione specifica
alembic upgrade head	                    Applica tutte le migrazioni in sospeso fino all'ultima	Per portare il database all'ultimo stato
alembic downgrade <revisione>	            Annulla le migrazioni tornando a una revisione precedente	Per fare rollback di modifiche (mai in produzione senza backup)
alembic downgrade -1	                    Annulla l'ultima migrazione	Per tornare indietro di un passo (utile in fase di test)
alembic stamp <revisione>	                Imposta la versione del database senza eseguire migrazioni	Per allineare manualmente lo stato di Alembic al database
alembic stamp head	                        Marca il database come se fosse già all'ultima revisione	Usato per sincronizzare il timestamp dopo un reset
alembic stamp base	                        Resetta lo stato a "base", come se non ci fossero migrazioni	Primo passo per compattare la storia (squash)
alembic heads	                            Mostra tutte le "teste" disponibili (in caso di rami multipli)	Per gestire rami di sviluppo paralleli
alembic merge	                            Unisce due rami di migrazione	Quando due feature branch hanno generato migrazioni e vanno fuse
alembic check	                            Verifica se ci sono differenze non migrate tra modelli e database	Per controllare che tutto sia allineato prima di un rilascio

3. Descrizione dettagliata e scenari d'uso
3.1. alembic current
Mostra l'ID della revisione a cui il database è attualmente sincronizzato. Se viene visualizzato (head), significa che sei all'ultima migrazione disponibile.

Esempio:

bash
$ alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
0e13fca799ef (head)
3.2. alembic revision --autogenerate -m "messaggio"
Scenario tipico: hai appena modificato un modello SQLAlchemy (aggiunto una colonna, cambiato un tipo, ecc.). Eseguendo questo comando, Alembic confronta lo schema del database con i tuoi modelli e genera automaticamente il codice per portare il database allo stato desiderato.

Attenzione: controlla sempre il file generato! Può commettere errori, specialmente su operazioni complesse (rinomina di colonne, cambi di tipo che richiedono cast). Modificalo a mano se necessario.

3.3. alembic upgrade head
Il comando più usato per applicare le migrazioni. Porta il database all'ultima revisione. In produzione, dopo il deploy, è questo il comando da eseguire (insieme al backup).

3.4. alembic downgrade -1
Annulla l'ultima migrazione eseguita. Utile in fase di sviluppo per testare il rollback, ma mai in produzione senza aver verificato che la downgrade() sia corretta e che i dati non vengano persi.

3.5. alembic stamp head (o alembic stamp base)
Usato principalmente in due casi:

Allineamento dopo un reset della storia (vedi sezione "Compattare la storia").

Quando si eredita un progetto con database già creato ma senza file di migrazione. Si imposta stamp head per far credere ad Alembic che il database è già aggiornato.

3.6. Scrivere una migrazione manuale
A volte --autogenerate non è sufficiente o produce codice sbagliato. In tal caso:

bash
alembic revision -m "descrizione manuale"
Apri il file generato e scrivi le operazioni nelle funzioni upgrade() e downgrade():

python
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'email')
4. Compattare la storia (squash) – "azzerare la storicità"
Se hai una lunga serie di migrazioni e vuoi ricominciare da un unico file che rappresenta lo stato attuale, segui questi passi:

bash
alembic stamp base                   # imposta lo stato a "base"
rm alembic/versions/*.py             # cancella i vecchi file (conserva __init__.py)
alembic revision --autogenerate -m "initial state"  # genera il nuovo file unico
alembic stamp head                   # marca il database come già aggiornato
Questo è utile per mantenere pulito il repository, ma solo se sei sicuro che i vecchi script non servano più (tipicamente in fase di sviluppo).

5. Consigli pratici
Prima di ogni upgrade head in produzione, fai un backup del database.

Non usare downgrade in produzione – meglio fare un backup e ripristinare.

Controlla sempre il codice generato da --autogenerate – aggiungi commenti e verifica le operazioni, specialmente su alter_column e drop_constraint.

Mantieni i modelli SQLAlchemy sempre allineati con lo schema – altrimenti --autogenerate produrrà migrazioni indesiderate.

Se lavori in team, coordina le migrazioni per evitare conflitti (usa alembic merge se necessario).

6. Esempio di flusso di lavoro tipico
Modifichi il modello (es. aggiungi email a User).

Generi la migrazione:

bash
alembic revision --autogenerate -m "add email to user"
Controlli il file in versions/.

Applichi la migrazione:

bash
alembic upgrade head
Verifichi:

bash
alembic current
Se il campo è già stato aggiunto e vuoi solo aggiornare il timestamp (senza eseguire nulla), useresti stamp head – ma di solito non serve.

*Ultimo aggiornamento: giugno 2026 – basato su Alembic 1.7+*
